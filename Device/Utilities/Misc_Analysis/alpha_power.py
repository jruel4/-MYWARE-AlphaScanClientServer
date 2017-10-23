# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 21:47:26 2017

@author: marzipan
"""

from xdf import load_xdf
from matplotlib import pyplot as plt

d = load_xdf(u'C:\\Recordings\\CurrentStudy\\subj1\\block_.xdf')
data = d[0][0]['time_series']


