# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 04:39:22 2017

@author: marzipan
"""

import asyncio
import logging
import time
from websocket import create_connection

ws = create_connection("ws://127.0.0.1:5678", timeout=1)



try:
    while True:
        print("Sending 'Hello, World'...")
        ws.send("Hello, World")
        print("Sent")
        print("Receiving...")
        result =  ws.recv()
        print("Received '%s'" % result)
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    ws.close()    