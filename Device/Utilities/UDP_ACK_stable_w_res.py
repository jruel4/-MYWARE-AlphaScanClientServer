# -*- coding: utf-8 -*-
"""
Created on Sun Feb 05 17:51:48 2017

@author: marzipan
"""

import socket
import time
from collections import deque
import matplotlib.pyplot as plt

class TimeoutException(Exception):
    pass

def run_trial(sleep_time_normal=0.010, 
              sleep_time_slow=0.015, 
              RCV_TMO=0.006, 
              ERR_THRESH = 2, 
              RESEND_THRESH = 6,
              TRIAL_DURATION=180.0,
              CONSTANT_SLIP=False,
              SHOW_PLOTS=False):
                  
    UDP_IP = "192.168.1.227"
    UDP_PORT = 50007
    MESSAGE = 'xxx'
    BUF_MAX = 1400*8
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUF_MAX)
    sock.bind(('',UDP_PORT))
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    
    #TODO Set device params from master
    #TODO Monitor device params from master
    #TODO Monitor SYNC Acknowledgements from slave
    #TODO are we overwriting ctr with nonsense sometimes?
    
    # Increase this to minimize bandwidth usage, decrease to minimize latency
    sock.settimeout(RCV_TMO)
    # This should balance with timeout to equal tx rate 

    errors = 0
    sock_timeout_errs = 0
    t_errsnd = 0
    err_sync_loop_list = list()
    interrupt_count = 0
    FORCE_SYNC = False
    sync_runs = 0
    
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
        except socket.timeout:
            pass
        except socket.error as e:
                # A non-blocking socket operation could not be completed immediately
                if e.errno == 10035: 
                    pass
                else:
                    raise e
        sock.settimeout(RCV_TMO)
        
    def get_newest_ctr(sock):
        valid = 0
        nctr = -1
        sndr_rc = -1
        while 1:
            try:
                data = sock.recv(1400)
                nctr = ord(data[0])
                sndr_rc = ord(data[2])
                valid = len(data)
            except socket.timeout:
                return nctr,valid,sndr_rc
                
                
    # Perform sync
    if SHOW_PLOTS: print("Init Sync") 
    flush_UDP(sock)              
    MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
    time.sleep(sleep_time_normal)
    nctr,valid,rc = get_newest_ctr(sock)
    if valid: ctr = nctr
    if nctr==-1: nctr = ((ctr+10)%256) # The 10 here is arbitrary, any positive value should work aside from 1
    while nctr != ((ctr+1)%256):
        ctr = nctr
        flush_UDP(sock) # Shouldnt have anything in buffer since previous flush... but could call 
        MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        time.sleep(sleep_time_slow) 
        nctr,valid,rc = get_newest_ctr(sock)
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
            nctr,size,rc = get_newest_ctr(sock)
            if (size): 
                ctr = nctr
            else:
                raise TimeoutException()
            #print(ctr)
            
            # Append new data
            if (ctr != prev_ctr) and not FORCE_SYNC:
                flush_UDP(sock)
                resend_count = 0
                errors = 0
                SYNC_FLAG = NOSYNC_TOKEN
                rx_buf.append((time.time(), size))
                rx_buf_total.append((time.time()-t0, size, rc))
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
                    nctr,valid,rc = get_newest_ctr(sock)
                    if valid: ctr = nctr
                    if SHOW_PLOTS: print("Sync")          
                    MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
                    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
                    time.sleep(sleep_time_slow)
                    nctr,valid,rc = get_newest_ctr(sock)
                    if valid: ctr = nctr
                    if nctr==-1: nctr = ((ctr+10)%256)
                    err_sync_loops = 0
                    sync_runs += 1
                    sync_begin = time.time()                    
                    
                    while nctr != ((ctr+1)%256):
                        ctr = nctr
                        flush_UDP(sock) # Shouldnt have anything in buffer since previous flush... but could call 
                        MESSAGE = chr(ctr)+'_'.encode('utf-8')+SYNC_TOKEN
                        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
                        time.sleep(sleep_time_slow) 
                        nctr,valid,rc = get_newest_ctr(sock)
                        if nctr==-1: nctr = ((ctr+10)%256)
                        err_sync_loops += 1
                        
                        # 
                        
                    ctr = nctr
                    resend_count = 0
                    err_sync_loop_list += [(time.time()-t0, time.time()-sync_begin, err_sync_loops, FORCE_SYNC,rc)]
                    if SHOW_PLOTS: print(err_sync_loop_list[-1])

                    continue
            errors = 0
            FORCE_SYNC = False
            
            if (CONSTANT_SLIP): 
                CONSTANT_SLIP += 1
                if CONSTANT_SLIP%1000==0:
                    raise KeyboardInterrupt()
                    
        except KeyboardInterrupt:
            # Force slip
            if interrupt_count < 10:
                interrupt_count += 1
                ctr = 0
                prev_ctr = 0
                resend_count = RESEND_THRESH + 1
                FORCE_SYNC = True
                print("Forcing packet loss")
                continue
            elif not CONSTANT_SLIP:
                break
            #TODO does not allow exit in CONSTANT_SLIP mode
                
        except TimeoutException:
            errors += 1
            sock_timeout_errs += 1
            
    sock.close()
    
    # Collect error vars
    err_list = [sock_timeout_errs, t_errsnd, err_sync_loop_list, max_delay, sync_runs]
    err_dict = dict()
    for e in err_list:
        for k,v in list(locals().iteritems()):
            if v is e:
                err_dict[k] = v
    
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
    
    if (SHOW_PLOTS):
        plot_delay(delay_list)
        plot_Bps(Bps_list)
    
    return Bps_list, delay_list, rx_buf_total, err_dict
    
# Script trials
Bps_list_list = list()
delay_list_list= list()
rx_buf_total_list = list()
err_dict_list = list()
total_trial_duration_hours = 0.1
time_per_trial_sec = 180
num_trials = total_trial_duration_hours * 60.0 * 60.0 / time_per_trial_sec

# Define search grid
g_sleep_time_normal= [0.001,0.011,0.021]
g_sleep_time_slow=[0.011,0.021,0.031]
g_RCV_TMO=[0.006,0.012,0.021]
g_ERR_THRESH=[2,8]
g_RESEND_THRESH=[4,6,12]

g_PARAMETERS = [(s1,s2,s3,s4,s5) for s1 in g_sleep_time_normal\
                                 for s2 in g_sleep_time_slow\
                                 for s3 in g_RCV_TMO\
                                 for s4 in g_ERR_THRESH\
                                 for s5 in g_RESEND_THRESH]

#==============================================================================
# num_trials = len(g_sleep_time_normal)*len(g_sleep_time_slow)*\
#              len(g_RCV_TMO)*len(g_ERR_THRESH)*len(g_RESEND_THRESH)
# 
# for i,(v_sleep_time_normal,v_sleep_time_slow,v_RCV_TMO,v_ERR_THRESH,v_RESEND_THRESH) in enumerate(g_PARAMETERS):
#     print("Trial:             ",i)
#     print("sleep_time_normal: ",v_sleep_time_normal)
#     print("sleep_time_slow:   ",v_sleep_time_slow)
#     print("RCV_TMO:           ",v_RCV_TMO)
#     print("ERR_THRESH:        ",v_ERR_THRESH)
#     print("RESEND_THRESH:     ",v_RESEND_THRESH)
#     try:
#         b,d,r,e = run_trial(TRIAL_DURATION=time_per_trial_sec, 
#                             CONSTANT_SLIP=False,
#                             sleep_time_normal=v_sleep_time_normal,
#                             sleep_time_slow=v_sleep_time_slow,
#                             RCV_TMO=v_RCV_TMO,
#                             ERR_THRESH=v_ERR_THRESH,
#                             RESEND_THRESH=v_RESEND_THRESH,
#                             SHOW_PLOTS=True)
#     except KeyboardInterrupt:
#         break
#     Bps_list_list += [b]
#     delay_list_list += [d]
#     rx_buf_total_list += [r]
#     err_dict_list += [e]
#     time.sleep(0.5) 
#==============================================================================

try:
    for i in range(int(num_trials)):
        print("Trial: ",i)
        try:
            b,d,r,e = run_trial(TRIAL_DURATION=time_per_trial_sec, 
                                CONSTANT_SLIP=False,
                                sleep_time_normal=0.001,
                                sleep_time_slow=0.031,
                                RCV_TMO=10.0,
                                ERR_THRESH=100,
                                RESEND_THRESH=1,
                                SHOW_PLOTS=True)
        except KeyboardInterrupt:
            break
        Bps_list_list += [b]
        delay_list_list += [d]
        rx_buf_total_list += [r]
        err_dict_list += [e]
        time.sleep(0.5) 
except KeyboardInterrupt:
    pass










