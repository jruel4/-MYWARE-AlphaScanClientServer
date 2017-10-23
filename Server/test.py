# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 05:43:43 2017

@author: marzipan
"""

import logging

class WebsocketStub:
    def __init__(self):
        pass
    async def rcv(self, msg = ""):
        if not (isinstance(msg, str) or isinstance(msg, bytes)):
            raise AssertionError("Error, message must either be string or bytes")
        return msg
    async def send(self, msg):
        if not (isinstance(msg, str) or isinstance(msg, bytes)):
            logging.error("Error, message must either be string or bytes")
            raise TypeError
        print("TST SEND: ", msg)
        
# =============================================================================
# w = WebsocketStub()
# import functools
# asyncio.get_event_loop().run_until_complete(functools.partial(messageParser,w,"DD"))
# command_linstener_task = asyncio.ensure_future(messageParser(w, "DD"))
# done, pending = asyncio.wait( [command_linstener_task] )
# =============================================================================
