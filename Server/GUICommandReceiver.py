# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 02:22:29 2017

@author: marzipan
"""

import asyncio
import logging
import websockets

from Server.Errors import CommunicationErrors, KILL_SERVER_EXCEPTION
from Server.AscanCommandSender import AscanCommandSender

class GUICommandReceiver:
    def __init__(self):
        self.ws = None
        self.err_handling = None
        self.ascan_command_sender = None
        self.COMMANDS = {}

    async def _FUNCTION_NOT_IMPLEMENTED(self, ws, *args):
        log_msg = "Function not implemented, got args: " + " | ".join([str(a) for a in args])
        await self.err_handling.OK(msg=log_msg)

    def _formatAddress(self,add):
        return str(add[0]) + ":" + str(add[1])
    
    def _createCommandMap(self):
        self.COMMANDS = {
            "DEV_CON" : self.ascan_command_sender.connect,
            "DEV_DISCON" : self._FUNCTION_NOT_IMPLEMENTED,
            "BEG_STREAM" : self._FUNCTION_NOT_IMPLEMENTED,
            "STOP_STREAM" : self._FUNCTION_NOT_IMPLEMENTED,
            "SYNC_TIME" : self._FUNCTION_NOT_IMPLEMENTED,
            "ENTER_OTA_MODE" : self._FUNCTION_NOT_IMPLEMENTED,
            "ENTER_AP_MODE" : self._FUNCTION_NOT_IMPLEMENTED,
            "ENTER_WEB_UPDATE_MODE" : self._FUNCTION_NOT_IMPLEMENTED,
            "DEV_RESET" : self._FUNCTION_NOT_IMPLEMENTED,
        }    

    async def connectionHandler(self, ws, path):
        '''
        This is functionally our init for the class
        '''
        logging.info("Receievd connection from: " + self._formatAddress(ws.remote_address))
        
        # Set up error handling etc...
        self.ws = ws
        self.err_handling = CommunicationErrors(self.ws) # NOTE: The correct ws is pass in to CommErrors in connectionHandler
        self.ascan_command_sender = AscanCommandSender(self.err_handling)
        
        # Create command map
        self._createCommandMap()
        
        #create future object which will be executed
        command_linstener_task = asyncio.ensure_future(self.commandLinstener(ws))
    
        # wait for futures / coroutines to complete
        done, pending = await asyncio.wait( [command_linstener_task] )

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
        msg_split = msg.split("|")
        opcode = msg_split[0]
        
        if opcode == "KILL_SERVER":
            await self.err_handling.OK(msg="Received kill server opcode, dying...")
            raise KILL_SERVER_EXCEPTION()
            return False

        # Make sure opcode is valid
        try:
            command = self.COMMANDS[opcode]
            logging.info("Received good opcode: " + opcode)
        
            # Call command
            if len(msg_split) > 1:
                await command(ws, msg_split[1:])
            else:
                await command(ws)

        except KeyError:
            await self.err_handling.ERR_BAD_OPCODE(opcode=opcode, msg="Received unknown opcode, message: " + msg)
        
        return True # Keep running unless we
    
    def checkArgs(self, function, *args):
        args_list = function(_