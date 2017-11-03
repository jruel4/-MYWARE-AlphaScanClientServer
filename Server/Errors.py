# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 06:49:41 2017

@author: marzipan
"""

import logging
import numpy as np
import inspect


class KILL_SERVER_EXCEPTION(Exception):
    pass

class CommunicationErrors:
    
    def __init__(self, ws):
        self.ws = ws

        self.ERRORS = {
            "OK"                    : (  0, "Operation succeeded"),
            "ERR_BAD_OPCODE"        : ( -1, "Opcode unrecognized"),
            "ERR_BAD_NUM_PARAMS"    : ( -2, "Incorrect parameters provided"),
            "ERR_BAD_PARAM_TYPES"   : ( -3, "Incorrect parameter types"),
            "ERR_WHEN_CONNECTING"   : ( -4, "Not able to establish connection(s) with device(s)"),
            "ERR_STILL_STREAMING"   : ( -5, "Device is streaming, operation incompatible"),
            "ERR_NOT_STREAMING"     : ( -6, "Device is not streaming, operation incompatible"),
            "ERR_BAD_SYNC"          : ( -7, "Sync failed due to erroneous / outlandish values"),
            "ERR_BAD_COMM"          : ( -8, "Attempted to execute command but did not receive expected output"),
            "ERR_ALREADY_CONNECTED" : ( -9, "Device is already connected, cannot connect again"),
            "ERR_NOT_CONNECTED"     : (-10, "Device us not connected, operation incompatible"),
            "ERR_OTHER"             : (-99, "Other error"),
        }
            

    async def OK(self, msg=""):
        ''' Operation succeeded '''
        name = inspect.currentframe().f_code.co_name
        logging.info("FUNC: "  + str(inspect.stack()[1][3]) + " | Success")
        if msg: logging.info("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_BAD_OPCODE(self, opcode="(NOT PROVIDED)", msg=""):
        ''' Opcode unrecognized '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("Bad opcode received, got: " + str(opcode))
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]
    
    async def ERR_BAD_NUM_PARAMS(self, expected = "(NOT PROVIDED)", received = "(NOT PROVIDED)", msg=""):
        ''' Incorrect number of parameters provided '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Didn't receive correct number of arguments, correct number: " + str(expected) + ", received: " + str(received))
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]
    
    async def ERR_BAD_PARAM_TYPES(self, msg=""):
        ''' Incorrect type(s) of parameters provided '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Incorrect parameter types received")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_WHEN_CONNECTING(self, msg=""):
        ''' Not able to establish connection(s) with device(s) '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Couldn't connect to devices")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_STILL_STREAMING(self, msg=""):
        ''' Device is streaming, operation incompatible '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Device is streaming")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_NOT_STREAMING(self, msg=""):
        ''' Device is not streaming, operation incompatible '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Device is not streaming")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_BAD_SYNC(self, msg=""):
        ''' Sync failed due to erroneous / outlandish values '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Time sync failed due to erroneous / outlandish values ")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_BAD_COMM(self, msg=""):
        ''' Attempted to execute command but did not receive expected output '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Attempted to execute command but did not receive expected output")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_ALREADY_CONNECTED(self, msg=""):
        ''' Device is connected, operation incompatible '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Devices already connected")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_NOT_CONNECTED(self, msg=""):
        ''' Device is not connected, operation incompatible '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Devices not connected")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]

    async def ERR_OTHER(self, msg=""):
        ''' Other error '''
        name = inspect.currentframe().f_code.co_name
        logging.warning("FUNC: "  + str(inspect.stack()[1][3]) + " | Other error")
        if msg: logging.warning("MSG: " + str(msg))
        await self.ws.send(name)
        return self.ERRORS[name][0]