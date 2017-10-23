# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:57:54 2017

@author: marzipan
"""

import logging

class stub_websockets:
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
        logging.info("TST SEND: ", msg)