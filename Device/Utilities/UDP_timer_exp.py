# -*- coding: utf-8 -*-
"""
Created on Mon Feb 06 16:41:58 2017

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
                  
UDP_IP = "192.168.1.227"
UDP_PORT = 50007
MESSAGE = 'xxx'
BUF_MAX = 1400*8
TRIAL_DURATION = 10

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUF_MAX)
sock.bind(('',UDP_PORT))
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
sock.settimeout(0)

timeouts = 0
blocks = 0
d_times = list()
t_old = time.time()


t_begin = time.time()
try:
    while (time.time() - t_begin) < TRIAL_DURATION:
    
        try:
            data = sock.recv(1400)
            t_new = time.time()
            t_delta = t_new - t_old
            d_times += [t_delta]
            t_old = t_new
        except socket.timeout:
            timeouts += 1
        except socket.error as e:
            if e.errno == 10035:
                blocks += 1
            else:
                raise e
except KeyboardInterrupt:
    pass
    
import numpy as np
print("sample size: ",len(d_times))
print("max        : ",max(d_times))
print("min        : ",min(d_times))
print("mean       : ",np.mean(d_times))
print("std        : ",np.std(d_times))












