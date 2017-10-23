# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 12:12:43 2016

@author: marzipan
"""

import socket
import time
from collections import deque
import matplotlib.pyplot as plt

UDP_IP = "192.168.1.227"
UDP_PORT = 50007
num = 10
MESSAGE = 'xxx'
num_iter = num * 100


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,8192)
sock.bind(('',UDP_PORT))
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

#socket.setdefaulttimeout(0)
#sock.setblocking(False)

# Increase this to minimize bandwidth usage, decrease to minimize latency
sock.settimeout(0.005)
# This should balance with timeout to equal tx rate 
RSND_THRESH = 2

data = ''
inbuf = list()
errors = 0

# track the longest delay between fresh packets
max_delay = 0
delay_list = list()
tb = time.time()

# Track the throughput per second
rx_buf = deque([(0,0) for i in range(100)],100)
prev_ctr = -1
Bps_list = list()
t0 = time.time()

while True:
    try:
        if (errors > RSND_THRESH):
            # This implies that remote hasn't sent another packet, so resend ACK
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
            errors = 0
        # Receive packet
        data = sock.recv(1400)
        ctr = ord(data[0])
        #print(ctr)
        
        # Append new data
        if ctr != prev_ctr:
            rx_buf.append((time.time(), len(data)))
            prev_ctr = ctr
            # Check if new max delay reached
            tn = time.time()
            td = (tn - tb)
            if td > max_delay:
                max_delay = td
            tb = tn
            delay_list += [(tn-t0, td)]
            
            if ctr == 0:
            # print rx rate
                t = 0
                for d in rx_buf:
                    t += d[1]
                Bps = t/(rx_buf[-1][0] - rx_buf[0][0])
                Bps_list += [(time.time()-t0,Bps)]
                print("Bps: ", Bps)
        
        # Send ACK for received data
        MESSAGE = chr(ctr)+'tt'.encode('utf-8')
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        errors = 0
        
        
            
    except:
        errors += 1
        #if errors % 10000 == 0: print(errors)
        #if errors > (num_iter*200): # make this relative to time 
            #break
        
sock.close()
print("finished: "+str(len(inbuf)/float(num_iter)))



def plot_delay():# input delay list
    global delay_list
    t = [u[0] for u in delay_list]
    v = [u[1] for u in delay_list]
    plt.plot(t,v)
    plt.show()

def plot_Bps():
    global Bps_list
    t = [u[0] for u in Bps_list]
    v = [u[1] for u in Bps_list]
    plt.plot(t,v)
    plt.show()




