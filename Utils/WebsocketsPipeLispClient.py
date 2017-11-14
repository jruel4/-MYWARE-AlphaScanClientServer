# -*- coding: utf-8 -*-
"""
Created on Sun Nov 12 20:32:32 2017

@author: marzipan
"""

import sys
import zmq

#  Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

print("Collecting updates from weather server…")
socket.connect("tcp://localhost:5556")

# Process 5 updates
total_temp = 0
for update_nbr in range(5):
    string = socket.recv_string()