# -*- coding: utf-8 -*-
"""
Created on Mon Feb 06 03:00:41 2017

@author: marzipan
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Feb 05 17:51:48 2017

@author: marzipan
"""

import socket
import time
from collections import deque
import matplotlib.pyplot as plt

def run_trial(sleep_time_normal=0.010, 
              sleep_time_slow=0.015, 
              RCV_TMO=0.006, 
              ERR_THRESH = 2, 
              RESEND_THRESH = 6):
                  
    UDP_IP = "192.168.1.227"
    UDP_PORT = 50007
    MESSAGE = 'xxx'
    BUF_MAX = 1400*8
    TRIAL_DURATION = 180
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUF_MAX)
    sock.bind(('',UDP_PORT))
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    
    #socket.setdefaulttimeout(0)
    #sock.setblocking(False)
    
    # Increase this to minimize bandwidth usage, decrease to minimize latency
    sock.settimeout(RCV_TMO)
    # This should balance with timeout to equal tx rate 

    errors = 0
    t_errors = 0
    t_errsnd = 0
    err_sync_loop_list = list()
    # TODO name more specific total error types and return in dictionary
    # TODO force slip event
    
    # track the longest delay between fresh packets
    max_delay = 0
    delay_list = list()
    tb = time.time()
    
    # Track the throughput per second
    rx_buf = deque([(0,0) for i in range(256)],256)
    rx_buf_total = deque()
    prev_ctr = -2
    Bps_list = list()
    t0 = time.time()
    
    # Track synchronization
    resend_count = 0
    
    SYNC_TOKEN = chr(0x1)
    NOSYNC_TOKEN = chr(0x0)
    SYNC_FLAG = NOSYNC_TOKEN
    ctr = 0
    nctr = -1
    
    def flush_UDP(sock):
        try:
            sock.settimeout(0)
            sock.recv(BUF_MAX)
        except:
            pass
        sock.settimeout(RCV_TMO)
        
    def get_newest_ctr(sock):
        valid = 0
        nctr = -1
        while 1:
            try:
                data = sock.recv(1400)
                nctr = ord(data[0])
                valid = len(data)
            except:
                return nctr,valid
                
                
    # Perform sync
    print("Init Sync") 
    flush_UDP(sock)              
    MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    time.sleep(sleep_time_normal)
    nctr,valid = get_newest_ctr(sock)
    if valid: ctr = nctr
    if nctr==-1: nctr = ((ctr+10)%256) # The 10 here is arbitrary, any positive value should work aside from 1
    while nctr != ((ctr+1)%256):
        ctr = nctr
        flush_UDP(sock) # Shouldnt have anything in buffer since previous flush... but could call 
        MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        time.sleep(sleep_time_slow) 
        nctr,valid = get_newest_ctr(sock)
        if nctr==-1: nctr = ((ctr+10)%256)
        
    ctr = nctr
    
    while (time.time() - t0) < TRIAL_DURATION:
        try:
            if (errors > ERR_THRESH):
                # This implies that remote hasn't sent another packet, so resend ACK
                MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_FLAG
                sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
                time.sleep(sleep_time_slow)
                errors = 0
                resend_count += 1
                t_errsnd += 1
                
            # Send ACK for received data
            MESSAGE = chr(ctr)+'_'.encode('utf-8')+NOSYNC_TOKEN
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
            time.sleep(sleep_time_normal)
            
            # Receive packet
            nctr,size = get_newest_ctr(sock)
            if (size): 
                ctr = nctr
            else:
                raise Exception()
            #print(ctr)
            
            # Append new data
            if ctr != prev_ctr:
                flush_UDP(sock)
                resend_count = 0
                errors = 0
                SYNC_FLAG = NOSYNC_TOKEN
                rx_buf.append((time.time(), size))
                rx_buf_total.append((time.time(), size))
                prev_ctr = ctr
                # Check if new max delay reached
                tn = time.time()
                td = (tn - tb)
                if td > max_delay:
                    max_delay = td
                tb = tn
                delay_list += [(tn-t0, td)]
                
                # print rx rate
                if ctr == 0:
                    t = 0
                    for d in rx_buf:
                        t += d[1]
                    Bps = t/(rx_buf[-1][0] - rx_buf[0][0])
                    Bps_list += [(tn-t0,Bps)]
                    print("Bps: ", tn-t0, Bps, max_delay)
            else:
                # If new ctr does == previous then we track it to monitor synchronization
                resend_count += 1
                # If resend exceed threshold then trigger sync event
                if resend_count > RESEND_THRESH:
                    # Perform sync
                    nctr,valid = get_newest_ctr(sock)
                    if valid: ctr = nctr
                    print("Sync")                
                    MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
                    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
                    time.sleep(sleep_time_slow)
                    nctr,valid = get_newest_ctr(sock)
                    if valid: ctr = nctr
                    if nctr==-1: nctr = ((ctr+10)%256):
                    err_sync_loops = 0
                    
                    while nctr != ((ctr+1)%256):
                        ctr = nctr
                        flush_UDP(sock) # Shouldnt have anything in buffer since previous flush... but could call 
                        MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
                        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
                        time.sleep(sleep_time_slow) #TODO make this longer?
                        nctr,valid = get_newest_ctr(sock)
                        if nctr==-1: nctr = ((ctr+10)%256):
                        err_sync_loops += 1
                        
                    ctr = nctr
                    resend_count = 0
                    err_sync_loop_list += [(time.time(),err_sync_loops)]
                    #TODO flush_UDP(sock)
                    #errors = 0
                    continue
            errors = 0
        except KeyboardInterrupt:
            break
        except:
            errors += 1
            t_errors += 1
            
    sock.close()
    
    # Collect error vars
    err_list = [t_errors, t_errsnd]
    
    def plot_delay(delay_list):# input delay list
        t = [u[0] for u in delay_list]
        v = [u[1] for u in delay_list]
        plt.plot(t,v)
        plt.show()
    
    def plot_Bps(Bps_list):
        t = [u[0] for u in Bps_list]
        v = [u[1] for u in Bps_list]
        plt.plot(t,v)
        plt.show()
    
    plot_delay(delay_list)
    plot_Bps(Bps_list)
    
    return Bps_list, delay_list, rx_buf_total
    
# Script trials
Bps_list_list = list()
delay_list_list= list()
rx_buf_total_list = list()
for i in range(4):
    b,d,r = run_trial()
    Bps_list_list += [b]
    delay_list_list += [d]
    rx_buf_total_list += [r]
    print("Trial: ",i)
    time.sleep(5) # TODO May want to sent reset command to AlphaScan here and wait max startup time




