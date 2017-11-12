"""
SERVER
"""

import time
import socket
# NOTE: importing timing_utils from Experimental.Timing, TODO FIX IMPORT
import AlphaScan.Experimental.Timing.timing_utils as timing_utils
import struct
import random
from threading import Thread, Event
import numpy as np
from matplotlib import pyplot as plt
from sklearn import linear_model
import pylsl

import logging

class TimeSync:
    
    def __init__(self):
        self.t_init = pylsl.local_clock()
        self.finished = Event()
        self.finished.clear()
        
        self.drift = None
        self.length_offsets = None
        self.drift_reasonable = None
        
        
    def get_drift_stats(self):
        return [ self.drift, self.length_offsets, self.drift_reasonable]
    def sync(self, IP, DEVNUM, CALLBACK_FN):
        self.UDP_IP_REMOTE = IP
        self.DEVNUM = DEVNUM
        self.syncThread = Thread(target=lambda: self.sync_thread(CALLBACK_FN))
        self.syncThread.start()
        return self.syncThread.isAlive()
        
    def sync_threadx(self):
        self.t0 = pylsl.local_clock()
        print("running thread")
        while (pylsl.local_clock()-self.t0) < 5.0:
            pass
        self.finished.set()
        
    def process_offsets(self):
        # Check offset len
        x,y = zip(*self.offsets)
        xc,yc = timing_utils.clean_data(x,y)
        xc = np.asarray(xc).reshape(-1,1)
        yc = np.asarray(yc).reshape(-1,1)
        regr = linear_model.LinearRegression()
        regr.fit(xc,yc)
        drift = regr.coef_[0][0]
        drift_reasonable = drift < 5E-5
        plt.plot(x,y)
        plt.plot(xc,yc)
        self.regr = regr
        
        # These valus can be retrieved with get_drift_stats()
        self.drift = drift
        self.length_offsets = len(self.offsets)
        self.drift_reasonable = drift_reasonable

        return drift,len(self.offsets), drift_reasonable
        
    def calculate_offset(self, device_timestamp):
        '''
        dev_time = host_time*drift + initial offset ==>
        host_time = (dev_time-initial_offset)/drift
        '''
        return ((device_timestamp - self.regr.intercept_) / (1 + self.regr.coef_[0][0])) / (1.0e6)
        
    def sync_thread(self, callback_fn):
        UDP_IP_LOCAL = ''
        
        UDP_PORT_LOCAL = 2049 + self.DEVNUM
        UDP_PORT_REMOTE = 2050
        
        UDP_IP_REMOTE = self.UDP_IP_REMOTE
        
        PKT_FORMAT = 'Q'*5
        
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,8192)
        sock.bind((UDP_IP_LOCAL,UDP_PORT_LOCAL))
        sock.settimeout(0.400) # 10 millisecond timeout ... might be low?

        # Init clock
        self.t0 = pylsl.local_clock()
        
        timeouts = 0    
        self.offsets = []
        
        self.iter_count = 0
        while (pylsl.local_clock()-self.t0) < 60.0:
            self.iter_count += 1
            #time.sleep(0.001)
        
            # Generate packet id
            pid = random.randint(0,2**64-1)
            
            # Generate t1, pkt1, and immediatly send
            t1 = timing_utils.s2us(pylsl.local_clock())
            pkt1 = struct.pack(PKT_FORMAT, pid, t1, 0, 0, 0)
            sock.sendto(pkt1, (UDP_IP_REMOTE,UDP_PORT_REMOTE))
            
            # Block wait for rx with reasonable timeout (timeout ~ max expected RTT)
            try:
                rx_data = sock.recv(256)
                #TODO handle Errno 10054
                
                # Upon receipt immediatly generate t4
                t4 = pylsl.local_clock()
                
                # Check if packet is correct
                rx_pid,t1,t2,t3,_ = struct.unpack(PKT_FORMAT, rx_data)
                
                if rx_pid == pid:
                    t4 = timing_utils.s2us(t4)
                    offset = timing_utils.get_offset_us(t1,t2,t3,t4)
                    self.offsets += [(t4,offset)]
                    #print(offset)
                else:
                    logging.info("TimeSync | Received INVALID id")
                    #flush udp
                    try:
                        sock.recv(65535)
                    except socket.timeout:
                        pass
                    
            except socket.timeout as e:
                timeouts += 1
            except socket.error as e:
                if e.errno == 10054:
                    # JCR: I assume this means that the sync code is finished
                    logging.info("TimeSync | Received socket error no 10054, exiting...")
                    break
                else:
                    sock.close()
                    self.finished.set()
                    callback_fn(False, "Got socket error number: " + str(e.errno) + ", quitting...")
                    raise e


        sock.close()

        # This should be called here - no reason for it not to be
        self.process_offsets()

        self.finished.set()
        callback_fn(True, "Success")
        return
                
                
                
                
        















