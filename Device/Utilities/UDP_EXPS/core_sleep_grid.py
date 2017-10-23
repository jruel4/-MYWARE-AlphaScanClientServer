# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 00:54:53 2017

@author: marzipan
"""

import matplotlib.pyplot as plt
import pickle
import numpy as np
import socket
import time

UDP_IP = "192.168.1.227"
UDP_PORT = 50007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,8192)
sock.bind(('',UDP_PORT))

def msg(c):
    return chr(c)+'_'.encode('utf-8')+chr(0x00)     
def get_newest_ctr(sock):
    valid = 0
    nctr = -1
    sndr_rc = -1
    data = ''
    while 1:
        try:
            data = sock.recv(1400)
            nctr = ord(data[0])
            sndr_rc = ord(data[2])
            valid = len(data)
        except socket.timeout:
            break
        except socket.error as e:
        # A non-blocking socket operation could not be completed immediately
            if e.errno == 10035: 
                break
            else:
                raise e
    return nctr,valid,sndr_rc,data
def get_queue_size(data):
    msb = ord(data[1])
    lsb = ord(data[2])
    return ((msb << 8) | lsb)
    
def get_heap_size(data):
    msb = ord(data[3])
    csb = ord(data[4])    
    lsb = ord(data[5])
    return ((msb << 16) | (csb << 8) | lsb)
    
num_trials = 1
l_l_delays = [list() for i in range(num_trials)]
l_skip = [list() for i in range(num_trials)]
l_miss = [list() for i in range(num_trials)]
l_totrx = [list() for i in range(num_trials)]
l_kBps = [list() for i in range(num_trials)]
l_tp = [list() for i in range(num_trials)]
l_max_d = [list() for i in range(num_trials)]
l_min_d = [list() for i in range(num_trials)]
l_av_d = [list() for i in range(num_trials)]
l_sd_d = [list() for i in range(num_trials)]
l_queue = [list() for i in range(num_trials)]
l_heap = [list() for i in range(num_trials)]

#sleeps = np.linspace(0.026,0.034,num=9)
sleeps = [0.033]

for i in range(num_trials):
    for sleep in sleeps:
    
        # Stat vars
        do_print = False
        pd = 10.0 # print delta
        pl = time.time() # print last
        dl = list() # delay list
        rp = time.time() # rx previous
        rc = 0 # rx current
        t_data = list()
        t_q = list()
        t_heap = list()
        
        # Core vars
        sock.settimeout(0)
        totrx = 0
        skip = -1
        miss = 0
        te = 15
        t0 = time.time()
        ctr = 0x00
        while (time.time()-t0)<te:
            sock.sendto(msg(ctr), (UDP_IP, UDP_PORT))    
            time.sleep(sleep) 
            nctr,valid,rc,d = get_newest_ctr(sock)   
            if not valid: miss+=1;
            elif nctr != (ctr+1)%256: ctr=nctr;skip+=1
            else: ctr=nctr;totrx+=valid;rc=time.time();dl+=[rc-rp];rp=rc;t_data+=[d];t_q+=[get_queue_size(d)];\
                  t_heap+=[get_heap_size(d)]
            
            # Stats code
            if ((time.time()-pl)>pd) and do_print:
                pl = time.time()
                print("sleep: ",sleep)
                print("skip:  ",skip)
                print("miss:  ",miss)
                print("totrx: ",totrx)
                print("kBps:  ",totrx/1000.0/te)
                print("%tp:   ",(totrx/1400.0)/(te/sleep)*100)
                print("-------------------------")
        
        dl = dl[1:] # discard first value
        if True:        
            print("sleep:     ",sleep)
            print("skip:      ",skip)
            print("miss:      ",miss)
            print("totrx:     ",totrx)
            print("kBps:      ",totrx/1000.0/te)
            print("%tp:       ",(totrx/1400.0)/(te/sleep)*100)
            print("max delay: ",max(dl))
            print("min delay: ",min(dl))
            print("av. delay: ",np.mean(dl))
            print("sd. delay: ",np.std(dl))
            plt.plot(t_heap)
            plt.show()
            plt.plot(t_q)
            plt.show()
            print("-------------------------")
        l_l_delays[i] += [dl]
        l_skip[i] += [skip]
        l_miss[i] += [miss]
        l_totrx[i] += [totrx]
        l_kBps[i] += [totrx/1000.0/te]
        l_tp[i] += [(totrx/1400.0)/(te/sleep)*100]
        l_max_d[i] += [max(dl)]
        l_min_d[i] += [min(dl)]
        l_av_d[i] += [np.mean(dl)]
        l_sd_d[i] += [np.std(dl)]
        l_queue[i] += [t_q]
        l_heap[i] += [t_heap]
        # @1KSPS, 1400 generated every 56 milliseconds (assuming sending 24 data bytes + 1 counter byte)
        # Average delay at 33 ms sleep configuration is ~48 ms, leaving an 8 ms leeway.
        # So, running @ 1KSPS we could potentially fall behind and have difficult breaking even w/out 
        # delay modulation (i.e. shift from ~15 ms delay with high kBps to more stable ~33ms delay as needed)
        # @250SPS, 1400 bytes generated every 224 ms, leaving 176 ms leeway I.E. plenty of time for catchup.
        # We can fit 57 samples (@24 Bytes each) + another 24 status Bytes tota into a 1400 Byte packet.

err_dump = [l_l_delays,l_skip,l_miss,l_totrx,l_kBps,l_tp,l_max_d,l_min_d,l_av_d,l_sd_d]
pickle.dump(err_dump, open("err_dump_"+time.strftime("%d_%m_%Y__%H_%M_%S")+"_.p",'wb'))
    
#==============================================================================
# print("kBps")
# plt.plot(sleeps,l_kBps)
# plt.show()
# print("Max Delay")
# plt.plot(sleeps,l_max_d)
# plt.show()
# print("Min Delay")
# plt.plot(sleeps,l_min_d)
# plt.show()
# print("Average Delay")
# plt.plot(sleeps,l_av_d)
# plt.show()
# print("Standard Deviation Delay")
# plt.plot(sleeps,l_sd_d)
# plt.show()
# print("% Throughput")
# plt.plot(sleeps,l_tp)
# plt.show()
#==============================================================================

# Only completely exempt delays are 0.02888 and 0.031666


















