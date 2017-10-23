# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 21:36:02 2017

@author: marzipan
"""

import asyncio
import datetime
import os
import logging
import websockets

import server.

# Set up logging
USE_LOGFILE = False
if USE_LOGFILE:
    logfile = os.path.join(".", datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.log')
    logging.basicConfig(filename=logfile,level=logging.DEBUG, format='%(name)s: %(message)s',)
else:
    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s',)
    

# Start up command receiver
# This starts a websockets server - each new connection instantiates an instance of "handler"
start_server = websockets.serve(connHandler, '127.0.0.1', 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()