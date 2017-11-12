# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 01:41:23 2017

@author: marzipan
"""
'''

The general idea of this class is to collect producers and consumers and forward
data from the former to the latter.

Examples of producers:
    AlphaScan Manager
    Classifier Output
    Quiz
Examples of consumers:
    Classifier Input
    Data Vizualization (Python or other)
    GUI Data Vizualization
    Stream Saver

For nomarl operation, data flow is as follows:
    AlphaScan
        -> Classifier Input
        -> Stream Saver

    Quiz
        -> Classifier Input
        -> Stream Saver

    Classifier Output
        -> GUI Data Vizualization
        -> Stream saver

'''
import asyncio
import logging
import socket
import simplejson as json

class streamRouterAscanServer(asyncio.Protocol):
    def __init__(self):
        self.producers = None
        self.consumers = None

        # Used to send data back to producer
        self.transport = None
        self.iters = 0
        
        self.ascan_portno = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.transport = transport
        logging.warning("Accepted connection from: " + ":".join([str(p) for p in peername]))

    def data_received(self, data):
        if self.iters < 10:
            self.iters +=1
            try:
                msg=json.loads(data.decode())
                self.ascan_portno = msg["ALPHASCAN"]["portno"]
                print(self.ascan_portno)
                self.transport.write("ACK".encode())
            except UnicodeDecodeError:
                print(data.decode())
            except KeyError:
                pass

    def connection_lost(self, exc):
        logging.warning("Connection lost")


logging.basicConfig(level=logging.DEBUG)



# =============================================================================
# import signal
# 
# loop = asyncio.get_event_loop()
# 
# 
# class Connector:
# 
#     def __init__(self):
#         self.closing = False
#         self.closed = asyncio.Future()
#         task = loop.create_task(self.connection_with_client())
#         task.add_done_callback(self.closed.set_result)
# 
# 
#     async def connection_with_client(self):
#         while not self.closing:
#             print('Read/write to open connection')
#             await asyncio.sleep(1)
# 
#         print('I will now close connection')
#         await asyncio.sleep(1)
# 
# 
# conn = Connector()
# 
# 
# def stop(loop):
#     conn.closing = True
#     print("from here I will wait until connection_with_client has finished")
#     conn.closed.add_done_callback(lambda _: loop.stop())
# 
# loop.add_signal_handler(signal.SIGINT, stop, loop)
# 
# 
# =============================================================================

loop = asyncio.get_event_loop()
coro = loop.create_server(streamRouterAscanServer,
                              'localhost', 8888)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()






# =============================================================================
# 
# class streamRouterServer(asyncio.Protocol):
#     def __init__(self, producers, consumers):
#         # Used to send to consumers
#         assert isinstance(producers, dict) and isinstance(consumers, dict)
# 
#         self.producers = producers
#         self.consumers = consumers
# 
#         self.this_producer_instance = ""        
#         self.consumer_connections = []
# 
#         # Used to send data back to producer
#         self.transport = None
#         
#         self.is_valid_connection = False
# 
#     def connection_made(self, transport):
#         peername = transport.get_extra_info('peername')
#         self.transport = transport
#         logging.warning("Accepted connection from: " + ":".join([str(p) for p in peername]))
# 
#     def data_received(self, data):
#         print(data.decode())
#         if not self.is_valid_connection:
#             for k,v in self.producers.items():
#                 if data.decode() == k:
#                     self.this_producer_instance = k
#                     break
#             
#             if not self.this_producer_instance:
#                 logging.warning("Accepted connection from unknown producer: " + data.decode())
#                 self.is_valid_connection = False
#             else:
#                 logging.info("Valid connection from producer: \"" + self.this_producer_instance)
#                 self.is_valid_connection = True
#                 # Create connections to consumers
#                 try:
#                     for c in self.consumers.values():
#                         if c[1] == self.this_producer_instance:
#                             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                             s.connect(c[0])
#                             self.consumer_connections.append(s)
#                     if not self.consumer_connections:
#                         logging.warning("No connected for producer: " + self.this_producer_instance)
#                 except:
#                     pass
#         else:
#             for t in self.consumer_connections:
#                 t.send(data.decode())
# 
#     def connection_lost(self, exc):
#         logging.warning("Connection to " + self.this_producer_instance + " was lost")
# 
# 
# =============================================================================
