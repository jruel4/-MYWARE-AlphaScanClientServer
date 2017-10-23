# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 00:43:18 2017

@author: marzipan
"""

from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
from threading import Thread
from collections import deque
from random import random

fs = 250
N = fs*30
amp = 2 * np.sqrt(2)
time = np.arange(N) / float(fs)

plt.ion()

fig = plt.figure()
ax = fig.add_subplot(111)

x = amp * np.sin(2*np.pi*12*time)
x = deque(x, maxlen=N)

f, t, Sxx = signal.spectrogram(x, fs)
qm = plt.pcolormesh(t, f, Sxx)
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time [sec]')
plt.show()

plt.ion()

def animation_loop():
    try:
        inc = 0
        cnt = 0
        toggle = True
        while True:

            inc += 1
            if inc%180 == 0:
                toggle = not toggle
                cnt = 0
                
            if toggle:
                freq = 10
            else:
                freq = 50
            
            x_new = [amp*np.sin(2*np.pi*freq*(i+cnt)/fs)+(random()/10) for i in range(17)]
            cnt += 17
            
            x.extend(x_new)
            f, t, Sxx = signal.spectrogram(x, fs, noverlap=0)
            
            qm.set_array(Sxx.ravel())
            fig.canvas.draw()
            
            sleep(1.0/60.0)
    
    except KeyboardInterrupt:
        pass

thread = Thread(target = animation_loop)
thread.start()










