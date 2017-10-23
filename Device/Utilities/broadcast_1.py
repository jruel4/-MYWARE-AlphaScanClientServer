# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 17:28:01 2016

@author: marzipan
"""

from socket import *
s=socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.sendto('alpha_scan_beacon',('255.255.255.255',2390))