# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 18:27:09 2017

@author: marzipan
"""
from BitPacking import rms
from xdf import load_xdf
import numpy as np
from scipy.optimize import minimize

# V = I*Rt; Rt = R + 1/(2pifC);
# f-->inf, R-->0, V-->Down

folder = u'C:\\Recordings\\CurrentStudy\\subj5'
d = load_xdf('block_.xdf')
d = d[0][0]['time_series']
ch7 = d[:,6] # adjust desired channel number here
srate = 250 # only for first three sections
window_dur = 0.5
window_len = int(srate*window_dur)

# get rms over time
d_rms = []
for i in range(len(ch7)-window_len):
    d_rms += [rms(ch7[i:i+window_len])]
    
b2v = 5.0/2**24
d_rms = np.asarray(d_rms)
d_rms = d_rms*b2v

# d_rms[7000] == 1.6405860893346951
# d_rms[10000] == 0.66687585168470309
# d_rms[13000] == 0.34110832354068427

v_d = dict() # frequency to voltage mapping
v_d[7.8] = 1.6405860893346951
v_d[31.2] = 0.66687585168470309
v_d[62.5] = 0.34110832354068427

I = 24E-6 # current constant at 24 microamps
# V = I * (R + 1/(2pifC))
def V(R,C,f): 
    I = 24E-6   
    return I * (R + 1/(2*np.pi*f*C))
    
def error(x):
    R=x[0]
    C=x[1]
    e = 0
    for f in v_d.keys():
        e += ((v_d[f] - V(R,C,f))/((v_d[f] + V(R,C,f))/2.0))**2
    return e
    

x_bounds = [(100,None),(1E-7,None)]
guess = (51E3,47E-9)
res = minimize(error, guess, bounds=x_bounds,method='Nelder-Mead', options={'disp': False, 'iprint': 1,
                                                        'eps': 1.4901161193847656e-01, 
                                                        'maxiter': 1000, 'ftol': 1e-06})



R = res['x'][0]
C = res['x'][1]

keys = np.asarray(list(sorted(v_d.keys())))
v_pred = dict()
for f in keys:
    v_pred[f] = V(R,C,f)
y1 = np.asarray([v_d[k] for k in keys])
y2 = np.asarray([v_pred[k] for k in keys])
nd = np.vstack((y1,y2)).transpose()










