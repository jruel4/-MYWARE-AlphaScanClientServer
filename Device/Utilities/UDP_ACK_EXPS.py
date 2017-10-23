# -*- coding: utf-8 -*-
"""
Created on Mon Feb 06 21:58:41 2017

@author: marzipan
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 12:12:43 2016

@author: marzipan
"""

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
        return nctr,valid,sndr_rc

# Stat vars
do_print = False
pd = 10.0 # print delta
pl = time.time() # print last
dl = list() # delay list
rp = time.time() # rx previous
rc = 0 # rx current

# Core vars
sock.settimeout(0)
sleep = 0.030
totrx = 0
skip = -1
miss = 0
te = 60*10
t0 = time.time()
ctr = 0x00
while (time.time()-t0)<te:
    sock.sendto(msg(ctr), (UDP_IP, UDP_PORT))    
    time.sleep(sleep) 
    nctr,valid,rc = get_newest_ctr(sock)   
    if not valid: miss+=1;
    elif nctr != (ctr+1)%256: ctr=nctr;skip+=1
    else: ctr=nctr;totrx+=valid;rc=time.time();dl+=[rc-rp];rp=rc
    
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
print("sleep:     ",sleep)
print("skip:      ",skip)
print("miss:      ",miss)
print("totrx:     ",totrx)
print("kBps:      ",totrx/1000.0/te)
print("%tp:       ",(totrx/1400.0)/(te/sleep)*100)
print("max delay: ",max(dl))
print("av. delay: ",np.mean(dl))
print("sd. delay: ",np.std(dl))
print("-------------------------")
#1400 generated every 46 milliseconds
#




















