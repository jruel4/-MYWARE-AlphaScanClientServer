# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 00:22:38 2017

@author: marzipan
"""
import numpy as np

def rms(d): return np.sqrt(np.mean((d-np.mean(d))**2))
    
def get_imp(d):
    b2v = 4.5/(2**23 -1)
    V = (max(d) - min(d))*b2v
    I = 24E-6
    return V/I
    
def get_voltage(b, gain=1.0):
    b2v = 4.5/(2**23 - 1)
    b2v /= gain
    return b*b2v
    
def get_noise(dev, _gain=24):
    data = np.asarray(dev.dev[0].t_data)
    rms_noise = [get_voltage(rms(data[:,i]),gain=_gain) for i in range(8)]
    return rms_noise
    
def get_noise_np(data, _gain=24):  
    rms_noise = [get_voltage(rms(data[:,i]),gain=_gain) for i in range(8)]
    return rms_noise
    
    

    
#==============================================================================
# ivt = list()
# win_len = 250
# for i in range(len(data)-win_len):
#     frame = data[i:i+win_len]
#     ivt += [get_imp(frame)]
#==============================================================================










