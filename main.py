# -*- coding: utf-8 -*-

"""
Created on Fri Oct 20 21:36:02 2017

@author: marzipan


'''
You can use the following code to add custom attributes to the logger
'''
# =============================================================================
# old_factory = logging.getLogRecordFactory()
# def record_factory(*args, **kwargs):
#     record = old_factory(*args, **kwargs)
#     record.custom_attribute = 0xdecafbad 
#     return record 
# logging.setLogRecordFactory(record_factory) 
# =============================================================================

TODO
    Set up loading/saving network parameters
    Set up sending network parameters to device
    
    Set up loading/saving acquisition settings
    Set up sending acquisition to device

    Set up saving data to MongoDB

    Set up streaming to server
        Probably use D3.js for saving data
        Should have "START_STREAM":*stream_keyword*

"""

import asyncio
import datetime
import os
import logging
import websockets

from Server.CommandServer import CommandServer
from Server.CommandServerResponses import KILL_SERVER_EXCEPTION



# Set up logging
LOG_FORMAT_NORMAL_DETAIL = '%(asctime)s|%(levelname)s|%(message)s'
LOG_FORMAT_HIGH_DETAIL = '%(asctime)s|%(levelname).1s|%(filename).10s@%(lineno).4d|%(funcName).10s\n\t%(message)s'

# PARAMETERS
USE_LOGFILE = False
LOGGING_FORMAT = LOG_FORMAT_HIGH_DETAIL

if USE_LOGFILE:
    logfile = os.path.join(".", datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.log')
    logging.basicConfig(filename=logfile,level=logging.DEBUG, format=LOGGING_FORMAT,)
else:
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT,)

commandServer = CommandServer()

# Start up command receiver
# This starts a websockets server - each new connection instantiates an instance of "handler"
start_server = websockets.serve(commandServer.connectionHandler, '192.168.2.9', 50505)

event_loop = asyncio.get_event_loop()
try:
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()
except KeyboardInterrupt as e:
    logging.warning("Caught keyboard interrupt. Cancelling tasks...")
except KILL_SERVER_EXCEPTION:
    logging.info("Killing server...")
finally:
    start_server.server.close()