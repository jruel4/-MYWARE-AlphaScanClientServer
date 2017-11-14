# -*- coding: utf-8 -*-
"""
Created on Sun Nov 12 20:06:56 2017

@author: marzipan
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Nov 12 15:50:03 2017

@author: marzipan
"""

import asyncio
import websockets
import logging



import zmq
from random import randrange

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

while True:
    zipcode = randrange(1, 100000)
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)

    socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))



# =============================================================================
# 
# 
# 
# 
# class WebsocketsEchoServer:
#     def __init__(self):
#         self.ws = None
#         self.prints = 0
# 
#     def _formatAddress(self,add):
#         return str(add[0]) + ":" + str(add[1])
# 
#     async def connectionHandler(self, ws, path):
#         '''
#         This is functionally our init for the class
#         '''
#         logging.info("Receievd connection from: " + self._formatAddress(ws.remote_address))
#         
#         # Set up error handling etc...
#         self.ws = ws    
#         #create future object which will be executed
#         command_linstener_task = asyncio.ensure_future(self.commandLinstener(ws))
#     
#         # wait for futures / coroutines to complete
#         done, pending = await asyncio.wait( [command_linstener_task] )
#     
#     async def listener(self, ws):
#         stay_alive = True
#         try:
#             while stay_alive and self.prints < 20:
#                 message = await ws.recv()
#                 print("Got message: \n" + message)
#                 self.prints += 1
#                 await asyncio.sleep(1)
#             logging.info("Exiting...")
#         except websockets.exceptions.ConnectionClosed as E:
#             logging.info("Connection from " + self._formatAddress(ws.remote_address) +" closed.")
# 
# # Set up logging
# LOG_FORMAT_NORMAL_DETAIL = '%(asctime)s|%(levelname)s|%(message)s'
# LOG_FORMAT_HIGH_DETAIL = '%(asctime)s|%(levelname)8s|%(filename)20s.%(lineno)4d|%(funcName)20s|%(message)s'
# LOGGING_FORMAT = LOG_FORMAT_HIGH_DETAIL
# logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT,)
# 
# 
# # Start up command receiver
# simpleSyrup = WebsocketsEchoServer()
# # This starts a websockets server - each new connection instantiates an instance of "handler"
# start_server = websockets.serve(simpleSyrup.connectionHandler, "localhost", 5678)
# 
# event_loop = asyncio.get_event_loop()
# try:
#     event_loop.run_until_complete(start_server)
#     event_loop.run_forever()
# except KeyboardInterrupt as e:
#     logging.warning("Caught keyboard interrupt. Cancelling tasks...")
# finally:
#     event_loop.close()
# =============================================================================
