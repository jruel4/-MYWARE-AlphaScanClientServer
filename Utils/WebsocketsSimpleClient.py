# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 04:39:22 2017

@author: marzipan
"""

import asyncio
import logging
import time
from websocket import create_connection
import simplejson as json
import threading

gui_intro_string = {"GUI":{}}
lisp_intro_string = {"LISP":{}}
dump_connections = {"CMD_ROUTER":None, "OPCODE":"LIST_CONN"}
def gui_print_connections(ws):
    if ws:
        ws.send(json.dumps(gui_intro_string))
        count = 0
        try:
            while count < 2:
                ws.send(json.dumps(dump_connections))
                time.sleep(3)
                count += 1
        except KeyboardInterrupt:
            pass
        finally:
            ws.close()   

rxed = []
def lisp_save_data(ws):
    global rxed
    if ws:
        ws.send(json.dumps(lisp_intro_string))
        count = 0
        try:
            while count < 200:
                rxed += [json.loads(ws.recv())]
                count += 1
            ws.send(json.dumps({"RESP_GUI":"TEST12","DESTINATION":"127.0.0.1"}))
        except KeyboardInterrupt:
            pass
        finally:
            ws.close()   

def kk():
    ws = create_connection("ws://192.168.2.9:50505/Test", timeout=1)
#    ws = create_connection("ws://127.0.0.1:5678/Test", timeout=1)
    time.sleep(0.1)
    ws.close()


ws = create_connection("ws://127.0.0.1:5678/", timeout=1)
#ws = create_connection("ws://192.168.2.9:5678/", timeout=1)
thread_targets = [
#        lambda: lisp_save_data(ws),
        lambda: gui_print_connections(ws),
        ]

threads = []
for t in thread_targets:
    x = threading.Thread(target=t)
    threads.append(x)
    x.start()

for t in threads:
    t.join()