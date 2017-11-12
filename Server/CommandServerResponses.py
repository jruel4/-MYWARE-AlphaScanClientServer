# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 06:49:41 2017

@author: marzipan
"""

import asyncio
import logging
import numpy as np
import inspect
from types import MethodType

import simplejson as json

class KILL_SERVER_EXCEPTION(Exception):
    pass

from functools import wraps
# =============================================================================
# 0
# def error_message(func):
#     @wraps(func) # tool to retain orig function metadata
#     async def wrapper(self, optional_msg=""):
#         calling_function = str(inspect.stack()[1][3]) # function calling this function
#         error_name = func.__name__ # name of error
#         print("FUNC NAME: " + calling_function + " error: " + self.ERRORS[error_name][1])
# #            logging.info("FUNC: "  + str(inspect.stack()[1][3]) + " | Success")
# #            if msg: logging.info("MSG: " + str(msg))
# #            await self.ws.send(name)
# #            return self.ERRORS[name][0]
# #            return func(self, **parameters_to_wrapped_function)
#         return 0
#     return wrapper
# =============================================================================

class CommandServerResponses:
    
    def __init__(self, ws):
        self.ws = ws

        self.LOG_LEVELS = {
            "CRITICAL" : 50,
            "ERROR" : 40,
            "WARNING" :30,
            "INFO" : 20,
            "DEBUG" : 10,
        }

        self.ERRORS = {
            "OK"                    : [  0, "INFO",  "Operation succeeded" ],
            "ERR_BAD_OPCODE"        : [ -1, "ERROR", "Opcode unrecognized" ],
            "ERR_BAD_NUM_PARAMS"    : [ -2, "ERROR", "Incorrect parameters provided" ],
            "ERR_BAD_PARAM_TYPES"   : [ -3, "ERROR", "Incorrect parameter types" ],
            "ERR_WHEN_CONNECTING"   : [ -4, "ERROR", "Not able to establish connection(s) with device(s)" ],
            "ERR_STILL_STREAMING"   : [ -5, "ERROR", "Device is streaming, operation incompatible" ],
            "ERR_NOT_STREAMING"     : [ -6, "ERROR", "Device is not streaming, operation incompatible" ],
            "ERR_BAD_SYNC"          : [ -7, "ERROR", "Sync failed due to erroneous / outlandish values" ],
            "ERR_BAD_COMM"          : [ -8, "ERROR", "Attempted to execute command but did not receive expected output" ],
            "ERR_ALREADY_CONNECTED" : [ -9, "ERROR", "Device is already connected, cannot connect again" ],
            "ERR_NOT_CONNECTED"     : [-10, "ERROR", "Device us not connected, operation incompatible" ],
            "ERR_BAD_JSON"          : [-11, "ERROR", "Received invalid JSON, coudln't parse or didn't have \"OPCODE\" key"],
            "ERR_OTHER"             : [-99, "ERROR", "Other error" ],
            "TEST_0"                : [-999,"INFO",  "TEST" ],
        }
        
        for e in self.ERRORS.keys():
            setattr(self, e, MethodType(self._error_message_function_generator(e), self))
    
    def _error_message_function_generator(self,error_name):
        async def error_function(self, msg="", data=None, error_name=error_name, error_code=None, log_lvl=None, error_description=""):
            if error_code == None: error_code = self.ERRORS[error_name][0]
            if log_lvl == None: log_lvl = self.LOG_LEVELS[self.ERRORS[error_name][1]]
            if not error_description: error_description = self.ERRORS[error_name][2]
            calling_function = str(inspect.stack()[1][3]) # function calling this functions
            logging.log(log_lvl,\
                        str(error_name) + "|" +\
                        "Calling function="  + calling_function + "|" +\
                        'Message=' + str(msg) + "|" +\
                        'Data=' + str(json.dumps(data)))
            json_msg = {"RESP":error_name, "CODE":error_code, "MSG":msg,"DATA":data}
            await self.ws.send(json.dumps(json_msg))
            return error_code
        return error_function
    
if __name__ == "__main__":
    
    def _run(coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    from AlphaScanClientServer.Stubs.stub_websockets import stub_websockets
    print("MAIN")
    ws = stub_websockets()
    e = CommunicationErrors(ws)
    _run(e.TEST_0("REZZ"))