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

from Server.GUICommandReceiver import GUICommandReceiver
from Server.Errors import KILL_SERVER_EXCEPTION

# Set up logging
USE_LOGFILE = False
LOG_FORMAT = '%(name)s: %(message)s'
if USE_LOGFILE:
    logfile = os.path.join(".", datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.log')
    logging.basicConfig(filename=logfile,level=logging.DEBUG, format=LOG_FORMAT,)
else:
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT,)
    

x = GUICommandReceiver()

# Start up command receiver
# This starts a websockets server - each new connection instantiates an instance of "handler"

start_server = websockets.serve(x.connectionHandler, '127.0.0.1', 5678)

event_loop = asyncio.get_event_loop()

try:
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()
except KeyboardInterrupt as e:
    logging.warning("Caught keyboard interrupt. Cancelling tasks...")
except KILL_SERVER_EXCEPTION:
    logging.info("Killing server.")
finally:
    event_loop.close()