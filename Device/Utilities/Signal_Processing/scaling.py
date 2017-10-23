# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 11:51:41 2017

@author: marzipan
"""

def scale_p1_m1(y):
    '''
    scale x so that its max is +1 and min is -1
    
    Test
    >>> x = np.random.randn((64))
    >>> r = scale_p1_m1(x)
    >>> x.max()
    1.0
    >>> x.min()
    -1.0
    '''
    x = y.copy()
    x -= x.min() # set min to zero
    x /= x.max() / 2 # set max to 2
    x -= 1.0
    return x
    