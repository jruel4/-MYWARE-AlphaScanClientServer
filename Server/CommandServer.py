# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 02:22:29 2017

@author: marzipan
"""

import asyncio
import logging
import websockets
import simplejson as json

from Server.CommandServerResponses import CommandServerResponses, KILL_SERVER_EXCEPTION
from Server.CommandServerAlphaScanInterface import AscanCommandSender

class CommandServer:
    def __init__(self):
        self.ws = None
        self.err_handling = None
        
        self.path = None

        # This send the actual commands to the AlphaScan and manages multiple devices
        self.ascan_command_sender = None

        self.COMMANDS = {} #created later in connection_handler (ascan_command_sender must have an actual value)

    async def _FUNCTION_NOT_IMPLEMENTED(self, ws, *args):
        log_msg = "Function not implemented, got args: " + " | ".join([str(a) for a in args])
        await self.err_handling.OK(msg=log_msg)

    def _formatAddress(self,add):
        return str(add[0]) + ":" + str(add[1])
    
    def _createCommandMap(self):
        self.COMMANDS = {
            "DEV_CON" : self.ascan_command_sender.connect,
            "DEV_DISCON" : self.ascan_command_sender.disconnect,
            "BEG_STREAM" : self.ascan_command_sender.beginStream,
            "STOP_STREAM" : self.ascan_command_sender.stopStream,
            "SYNC_TIME" : self.ascan_command_sender.syncTime,
            "ENTER_OTA_MODE" : self._FUNCTION_NOT_IMPLEMENTED,
            "ENTER_AP_MODE" : self._FUNCTION_NOT_IMPLEMENTED,
            "ENTER_WEB_UPDATE_MODE" : self._FUNCTION_NOT_IMPLEMENTED,
            "DEV_RESET" : self.ascan_command_sender.reset,
            
            "LOAD_NETWORK_PARAMETERS" : self._FUNCTION_NOT_IMPLEMENTED,
        }    

    async def connectionHandler(self, ws, path):
        '''
        This is functionally our init for the class
        '''
        self.path = path
        logging.info("Receievd connection from: " + self._formatAddress(ws.remote_address) + "\n\tPath: " + str(path))
        
        # Set up error handling etc...
        self.ws = ws
        self.err_handling = CommandServerResponses(ws) # NOTE: The correct ws is pass in to CommErrors in connectionHandler
        self.ascan_command_sender = AscanCommandSender(self.err_handling)
        
        # Create command map
        self._createCommandMap()
        
        return await self.commandLinstener(ws)

    async def commandLinstener(self, ws):
        stay_alive = True
        try:
            while stay_alive:
                message = await ws.recv()
                stay_alive = await self.messageParser(ws, message)
            logging.info("Exiting...")
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(ws.remote_address) + " closed.")

    async def messageParser(self, ws, msg):
        '''
        Parses input commands from GUI
        '''
        logging.info("RX: " + msg)
        # TODO add error handler if JSON load fails
        try:
            json_parsed = json.loads(msg)
            if not isinstance(json_parsed, dict):
                raise TypeError
        except (TypeError, json.JSONDecodeError):
            return await self.err_handling.ERR_BAD_JSON("Bad JSON received, got: " + msg)

        # Make sure our JSON has an opcode object and it's valid
        if "OPCODE" not in json_parsed.keys() or not isinstance(json_parsed["OPCODE"], str):
            return await self.err_handling.ERR_BAD_JSON("Bad JSON received, got: " + msg)
        
        # We have our opcode now...
        opcode = json_parsed["OPCODE"]
        
        # Make sure it's valid for the commands we have
        if opcode == "KILL_SERVER":
            await self.err_handling.OK(msg="Received kill server opcode, dying...")
            raise KILL_SERVER_EXCEPTION()
            return False
        elif opcode not in self.COMMANDS.keys():
            return await self.err_handling.ERR_BAD_OPCODE('Received unknown opcode "' + opcode + '", full message: ' + msg)        

        # All tests passed, run the command
        logging.info("Received good opcode: " + opcode)
        command = self.COMMANDS[opcode]
        await command(msg) #reparses JSON (TODO: just pass JSON object, no need to reparse/recheck if it was validly loaded)
        return True # Keep running