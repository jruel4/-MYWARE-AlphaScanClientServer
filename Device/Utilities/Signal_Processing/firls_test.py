# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 00:02:06 2017

@author: marzipan
"""

from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
fig, axs = plt.subplots(2)
nyq = 125.  # Hz
desired = (0, 0, 1, 1, 0, 0)
store_fir = [list() for i in range(2)]
for bi, bands in enumerate(((0, 1, 2, 30, 31, 125), (0, 1, 2, 30, 35, 125))):
    fir_firls = signal.firls(257, bands, desired, nyq=nyq)
    fir_remez = signal.remez(257, bands, desired[::2], Hz=2 * nyq)
    fir_firwin2 = signal.firwin2(257, bands, desired, nyq=nyq)

    store_fir[bi] = fir_firls    
    
    hs = list()
    ax = axs[bi]
    for fir in (fir_firls, fir_remez, fir_firwin2):
        freq, response = signal.freqz(fir)
        hs.append(ax.semilogy(nyq*freq/(np.pi), np.abs(response))[0])
    for band, gains in zip(zip(bands[::2], bands[1::2]), zip(desired[::2], desired[1::2])):
        ax.semilogy(band, np.maximum(gains, 1e-7), 'k--', linewidth=2)
    if bi == 0:
        ax.legend(hs, ('firls', 'remez', 'firwin2'), loc='lower center', frameon=False)
    else:
        ax.set_xlabel('Frequency (Hz)')
    ax.grid(True)
    ax.set(title='Band-pass %d-%d Hz' % bands[2:4], ylabel='Magnitude')

fig.tight_layout()
plt.show()







