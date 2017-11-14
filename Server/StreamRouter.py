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







import time
import asyncio
import websockets
import logging
import numpy as np
import simplejson as json

import copy

# For recv timeouts, so we can check to make sure we're still running
from async_timeout import timeout as async_timeout

# For pretty printing to logs
import pprint

class WebsocketsEchoServer:
    def __init__(self):
        self.stay_alive = True
        
        # We're only going to have one LISP client and one saver client
        self.lisp_client = None
        self.ss_client = None
        
        '''
        {
        "GUI_HOST_IP:GUI_HOST_PORT":
            {
            "GUI": GUI_WS,
            "COMMAND":COMMAND_WS,
            "ASCAN:
                {
                # See below for list of AlphaScan properties
                UID_0: {*ASCAN0 PROPERTIES*}+{"WS":ASCAN0_WS},
                UID_1: {*ASCAN1 PROPERTIES*}+{"WS":ASCAN1_WS},
                ...
                }
            }
        }
        '''
        self.empty_connection_template = { "GUI":None, "COMMAND":None, "ASCAN":{}}
        self.connections = {}
        
        # For all pretty printing needs
        self.pprint = pprint.PrettyPrinter(indent=2,width=1)
        
        # This stores all used UIDs
        self.uids = []
        
        self.ascan_properties = ["ASCAN_IP", "ASCAN_PORT", "ASCAN_CH", "ASCAN_MASTER"]
        self.command_properties = []
        self.gui_properties = []
        self.lisp_properties = []
        self.saver_properties = []

    def _formatAddress(self,add):
        return str(add[0]) + ":" + str(add[1])

    def _generateUID(self):
        uid = np.random.randint(0,1e6)
        while uid in self.uids:
            uid = np.random.randint(0,1e6)
        return uid
    
    def _loadJSON(self, m):
        try:
            json_parsed = json.loads(m)
            if not isinstance(json_parsed, dict): logging.warning("JSON was pasred, is NOT a dict, got: " + m)
            return json_parsed
        except (TypeError, json.JSONDecodeError):
            logging.error("Unable to parse JSON, got: " + m)
            return None
    
    async def _rxMessage(self,ws,timeout):
        try:
            async with async_timeout(timeout):
                msg = await ws.recv()
        except asyncio.TimeoutError:
            return None
        return msg

    async def _rxJSON(self, ws, timeout):
        msg = await self._rxMessage(ws, timeout)
        return ((None,None) if msg == None else (msg, self._loadJSON(msg)))

    async def baseConnectionHandler(self, ws, path):
        '''
        This is functionally our init for the class
        '''
        current_connection_ip = ws.remote_address[0]
        current_connection_port = ws.remote_address[1]

        # For now, all we're going to do is save this as the IP
        # definitely prohibitive, but we can set up ID tagging the GUI/AlphaScan's later
#        current_connection_address = self._formatAddress(ws.remote_address)
        current_connection_address = current_connection_ip
        logging.info("Received connection from: " + self._formatAddress(ws.remote_address))

        # Get intro message
        try:
            msg, msg_dict = await self._rxJSON(ws, timeout=5)
            logging.info("Received intro message: " + str(msg))
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed before rx'ing intro string")
            return

        # If we didn't receve anything then quit
        if msg_dict == None:
            logging.warning("Didn't receive valid intro message, closing connection")
            ws.close()
            return
        
        # If this is a new client create a new connection record
        if current_connection_address not in self.connections.keys():
            self.connections.update({ current_connection_address: copy.copy(self.empty_connection_template) })

        current_connection  = self.connections[current_connection_address]
        
#        ---------------------------------
#        ----- ASCAN
#        ---------------------------------
        if "ASCAN" in msg_dict.keys():
            # Make sure we have all properties for AlphaScan
            for p in self.ascan_properties:
                if p not in msg_dict["ASCAN"].keys():
                    logging.error("Did not receive all AlphaScan properties, missing: " + p + ", got: " + msg_dict["ASCAN"].keys())
                    ws.close()
                    return
            
            # Make sure we haven't already got this AlphaScan
            for ip,port,_,__ in current_connection["ASCAN"].values():
                if ip == msg_dict["ASCAN"]["ASCAN_IP"] or port == current_connection["ASCAN"]["ASCAN_PORT"]:
                    logging.error("Got duplicate AlphaScan connection")
                    ws.close()
                    return
            
            # All tests passed, let's generate a UID for this bitch and get it registered (also msg it back with it's UID)
            uid = self._generateUID()
            current_connection["ASCAN"].update({uid : {**msg_dict["ASCAN"], **{"WS":ws}} }) # add websocket property to dict
            await ws.send(json.dumps({"UID":uid}))
            
            #create future object which will be executed and wait for them to complete
            handler = asyncio.ensure_future(self.ascanConnectionHandler(ws, current_connection_address, uid))
            done, pending = await asyncio.wait( [handler] )


# =============================================================================
# #        ---------------------------------
# #        ----- COMMAND SERVER
# #        ---------------------------------       
#         elif "COMMAND" in msg_dict.keys():
#             # Make sure we have all properties for GUI
#             for p in self.command_properties:
#                 if p not in msg_dict["COMMAND"].keys():
#                     logging.error("Did not receive all COMMAND properties, missing: " + p + ", got: " + msg_dict["GUI"].keys())
#                     ws.close()
#                     return
# 
#             # Make sure we haven't already got this GUI
#             if current_connection["COMMAND"]:
#                 logging.error("Got duplicate COMMAND connection")
#                 ws.close()
#                 return
#             
#             current_connection["COMMAND"] = ws
#             
#             #create future object which will be executed and wait for them to complete
#             handler = asyncio.ensure_future(self.commandConnectionHandler(ws, current_connection_address))
#             done, pending = await asyncio.wait( [handler] )
#         
# =============================================================================

#        ---------------------------------
#        ----- GUI
#        ---------------------------------       
        elif "GUI" in msg_dict.keys():
            # Make sure we have all properties for GUI
            for p in self.gui_properties:
                if p not in msg_dict["GUI"].keys():
                    logging.error("Did not receive all GUI, missing: " + p + ", got: " + msg_dict["GUI"].keys())
                    ws.close()
                    return

            # Make sure we haven't already got this GUI
            if current_connection["GUI"]:
                logging.error("Got duplicate GUI connection")
                ws.close()
                return
            
            current_connection["GUI"] = ws
            
            #create future object which will be executed and wait for them to complete
            handler = asyncio.ensure_future(self.guiConnectionHandler(ws, current_connection_address))
            done, pending = await asyncio.wait( [handler] )
        
#        ---------------------------------
#        ----- LISP
#        ---------------------------------
        elif "LISP" in msg_dict.keys():
            # Make sure we have all properties for LISP server
            for p in self.lisp_properties:
                if p not in msg_dict["LISP"].keys():
                    logging.error("Did not receive all LISP properties, missing: " + p + ", got: " + msg_dict["GUI"].keys())
                    ws.close()
                    return
            
            if self.lisp_client:
                logging.error("Already have connection to LISP cliet, got duplicate")
                ws.close()
                return
            
            self.lisp_client = ws
            
            #create future object which will be executed and wait for them to complete
            handler = asyncio.ensure_future(self.lispConnectionHandler(ws))
            done, pending = await asyncio.wait( [handler] )

#        ---------------------------------
#        ----- STREAM SAVER
#        ---------------------------------
        elif "STREAM_SAVER" in msg_dict.keys():
            # Make sure we have all properties for LISP server
            for p in self.ss_properties:
                if p not in msg_dict["STREAM_SAVER"].keys():
                    logging.error("Did not receive all STREAM_SAVER properties, missing: " + p + ", got: " + msg_dict["GUI"].keys())
                    ws.close()
                    return
            
            if self.ss_client:
                logging.error("Already have connection to STREAM_SAVER client, got duplicate connection")
                ws.close()
                return
            
            self.ss_client = ws
            
            #create future object which will be executed and wait for them to complete
            handler = asyncio.ensure_future(self.ssConnectionHandler(ws))
            done, pending = await asyncio.wait( [handler] )

#        ---------------------------------
#        ----- Other / Unknown
#        ---------------------------------        
        else:
            logging.error("Received unknown connection webserver, got message: " + msg)
            ws.close()
            return
            
    async def guiConnectionHandler(self, ws, current_connection_address):
        try:
            while self.stay_alive:
                msg, msg_dict = await self._rxJSON(ws, 1)
                if msg_dict == None:
                    pass
                elif "CMD_ASCAN" in msg_dict.keys():
                    if self.connections[current_connection_address]["COMMAND"]:
                        await self.connections[current_connection_address]["COMMAND"].send(msg)
                    else:
                        logging.warning("Command client at: " + current_connection_address + " not connected")
                        await ws.send(json.dumps({"ERR_NOT_CONNECTED@COMMAND":current_connection_address}))
                elif "CMD_LISP" in msg_dict.keys() and self.lisp_client:
                    if self.lisp_client:
                        await self.lisp_client.send(msg)
                    else:
                        logging.warning("LISP client not connected")
                        await ws.send(json.dumps({"ERR_NOT_CONNECTED@LISP":None}))
                elif "CMD_STREAM_SAVER" in msg_dict.keys() and self.ss_client:
                    if self.ss_client:
                        await self.ss_client.send(msg)
                    else:
                        logging.warning("Stream saver client not connected")
                        await ws.send(json.dumps({"ERR_NOT_CONNECTED@STREAM_SAVER":None}))
                elif "CMD_ROUTER" in msg_dict.keys():
                    await self.serverMessageParser(ws, msg_dict)
                elif "DATA_QUIZ" in msg_dict.keys():
                    if self.lisp_client: await self.lisp_client.send(msg)
                    if self.ss_client: await self.ss_client.send(msg)
                else:
                    logging.warning("Got unknown command from GUI, message: " + msg)
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed.")
        finally:
            if ws:
                ws.close()
            self.connections[current_connection_address]["GUI"] = None

    async def lispConnectionHandler(self,ws):
        try:
            while self.stay_alive:
                msg, msg_dict = await self._rxJSON(ws, 1)
                if msg_dict == None:
                    # Couldn't parse JSON or didn't RX any
                    continue
                elif "RESP_GUI" in msg_dict.keys() and "DESTINATION" in msg_dict.keys():
                    dest = msg_dict["DESTINATION"]
                    if dest in self.connections.keys() and self.connections[dest]["GUI"]:
                        await self.connections[dest]["GUI"].send(msg)
                    else:
                        logging.error("GUI at destination: " + dest + " not connected")
                        await ws.send(json.dumps({"ERR_NOT_CONNECTED@GUI":dest}))
                else:
                    logging.warning("Got unknown command from LISP client, message: " + msg)
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed.")
        finally:
            if ws:
                ws.close()
            self.lisp_client = None
        
    async def commandConnectionHandler(self,ws, current_connection_address):
        try:
            while self.stay_alive:
                msg, msg_dict = await self._rxJSON(ws, 1)
                if msg_dict == None:
                    # Couldn't parse JSON or didn't RX any
                    continue
                elif "RESP_GUI" in msg_dict.keys():
                    if self.connections[current_connection_address]["GUI"]:
                        await self.connections[current_connection_address]["GUI"].send(msg)
                else:
                    logging.warning("Got unknown command from GUI, message: " + msg)
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed.")
        finally:
            if ws:
                ws.close()
            self.connections[current_connection_address]["COMMAND"] = None

    async def ascanConnectionHandler(self,ws, current_connection_address, uid):
        try:
            while self.stay_alive:
                msg, msg_dict = await self._rxJSON(ws, 1)
                if msg_dict == None:
                    # Couldn't parse JSON or didn't RX any
                    pass
                elif "UID" in msg_dict.keys() and "DATA" in msg_dict.keys() and "TS" in msg_dict.keys():
                    if self.ss_client:
                        await self.ss_client.send(msg) 
                    if self.lisp_client:
                        await self.lisp_client.send(msg) 
                else:
                    logging.warning("Got unknown message from AlphaScan, message: " + msg)
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed.")
        finally:
            if ws:
                ws.close()
            # Remove UID from dict
            self.connections[current_connection_address]["ASCAN"].pop(uid)
    
    async def ssConnectionHandler(self, ws):
        try:
            while self.stay_alive:
                msg = self._rxMessage(ws, 1)
                if msg == None:
                    # Didn't RX message
                    continue
                else:
                    logging.error("Error from STREAM_SAVER: " + str(msg))
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed.")
        finally:
            if ws:
                ws.close()
            self.ss_client = None
        pass
    
    async def serverMessageParser(self, ws, msg_dict):
        logging.info("Got server command: " + str(msg_dict))
        if "OPCODE" in msg_dict.keys():
            if msg_dict["OPCODE"] == "LIST_CONN":
                logging.info("Router connections:\n" + self.pprint.pformat(self.connections))
        
        return

# Set up logging
LOG_FORMAT_NORMAL_DETAIL = '%(asctime)s|%(levelname)s|%(message)s'
LOG_FORMAT_HIGH_DETAIL = '%(asctime)s|%(levelname).1s|%(filename).20s@%(lineno).4d|%(funcName).20s\n\t%(message)s'
LOGGING_FORMAT = LOG_FORMAT_HIGH_DETAIL
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT,)


if asyncio.get_event_loop().is_closed():
    asyncio.set_event_loop(asyncio.new_event_loop())
event_loop = asyncio.get_event_loop()

# Start up command receiver
simpleSyrup = WebsocketsEchoServer()
# This starts a websockets server - each new connection instantiates an instance of "handler"
start_server = websockets.serve(simpleSyrup.baseConnectionHandler, "localhost", 5678, loop=event_loop)

def kk():
    start_server.server.close()

try:
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()
except KeyboardInterrupt as e:
    logging.warning("Caught keyboard interrupt. Cancelling tasks...")
    simpleSyrup.stay_alive = False

    # Find all running tasks:
#    pending = asyncio.Task.all_tasks()

    # Run loop until tasks done:
#    event_loop.run_until_complete(asyncio.gather(*pending))

#    start_server.server.close()

    logging.warning("Done")
finally:
    start_server.server.close()
#    event_loop.close()
#    server.close()
