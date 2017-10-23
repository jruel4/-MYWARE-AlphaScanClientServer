
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 05 22:06:37 2016

@author: marzipan
"""

def twos_comp(val, bits=24):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val

'''   
data = pickle.load( open("workspace\\AlphaScan\\Controller\\Data\\sqwave.p", "rb"))

ch1tc = list()
for n in data:
    ch1tc += [str(n[3:6])]

for n in chan1tc: # where chan1tc is a list of length 3 strings of tc data
    val = 0
    for i,s in list(reversed(list(enumerate(n)))):
        val ^= ord(s) << (i*8)
    chan1tcord += [twos_comp(val)]
'''    
    

