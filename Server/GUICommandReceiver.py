# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 02:22:29 2017

@author: marzipan
"""

import asyncio
import logging
import websockets


class GUICommandReceiver:
    def __init__(self):
        
        pass

    def _formatAddress(self,add):
        return str(add[0]) + ":" + str(add[1])

    async def connectionHandler(self, websocket, path):
        logging.info("Receievd connection from: " + self._formatAddress(websocket.remote_address))
    
        #create future object which will be executed
        command_linstener_task = asyncio.ensure_future(self.commandLinstener(websocket))
    
        # wait for futures / coroutines to complete
        done, pending = await asyncio.wait( [command_linstener_task] )

    async def commandLinstener(self, websocket):
        try:
            while True:
                message = await websocket.recv()
                await self.messageParser(websocket, message)
        except websockets.exceptions.ConnectionClosed as E:
            logging.info("Connection from " + self._formatAddress(websocket.remote_address) + " closed.")

    async def messageParser(self, ws, msg):
        '''
        Parses input commands from GUI
        '''
        logging.info("RX: " + msg)
        msg_split = msg.split("|")
        opcode = msg_split[0]
        
        # Make sure opcode is valid
        try:
            command = COMMANDS[opcode]
        except KeyError:
            logging.warning("Received unknown opcode, message: " + msg)
            await ws.send("ERR_BAD_PARAMS")
            return
    
        # Call command
        if len(msg_split) > 1:
            command(msg_split[1:])
        else:
            command()