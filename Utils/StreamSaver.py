# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 16:09:12 2017

@author: marzipan
"""

'''

LSL Spec

This module is used for "recording" lsl streams. That means that user will pick
a stream, and module will have to buffer it it memory unti writing to a db.

Aside from that, just need to make sure my use of the MongoDB module is good.

Ok, so multiple streams will need to be tracked at once. The simplest way to do
this is to have a streams object that encapsulates state-specific activities
e.g. buffering, converting, etc.

'''
from pylsl import StreamInlet, resolve_stream
from threading import Thread, Event
import numpy as np
from MongoDB import MongoController
import pickle
import time
import os

import copy
import logging
import time
import websocket as WSClient
import simplejson as json
import socket

class StreamManager:
    
    def __init__(self, stream_router_ip, stream_router_port):
        self.stream_router_ip = stream_router_ip
        self.stream_router_port = stream_router_port

        self.stay_alive = True
        
        # The key for each saving instance should be and IP address
        self.saving_instances = {}
        self.instance_template = {
                "FILENAME":"",
                "OVERWRITE":False,
                "VALID_UIDS":[],
                "VALID_MARKER_STREAMS":[],
                "METADATA":{},
                "DATA":{},
                "LISP_DATA":None, #whatever Martin wants in here
                }
        # Each data instance and metadata instance should have the ascan UID as reference;
        #  use key "ALL" for metadata pertaining to entire set
        #  use key "QUIZ" for data/metadata pertaining to quiz
        #  use key "EVENTS" for data/metadata pertaining to other events
        self.instance_data = {
                "TS":[],
                "DATA":[],
                }
        self.instance_metadata = {
                "CHANNELS":[],
                "MASTER":False,
                # Can add more later
                }
        
        # Contains list of IP's that we're actively saving data from
        self.actively_saving = []

        self.rxed = []
        self.rxed_cnt0 = 0
        self.rxed_cnt1 = 0
        self.rxed_cnt2 = 0
        self.rxed_cnt3 = 0

        self.router = None
        self.db = MongoController()
    
    def run(self):
        while self.stay_alive:
            # Try connecting to stream router
            if not self.router:
                try:
                    self.router = WSClient.create_connection(
                        "ws://" + self.stream_router_ip + ":" + str(self.stream_router_port),
#                            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY),),
                        timeout=0.1)
                    logging.info("Connection to router created")
                    init_msg = {"STREAM_SAVER":{}}
                    self.router.send(json.dumps(init_msg))                    
                except socket.timeout as e:
                    logging.error("Stream Saver client couldn't connect, timed out, retrying...")
                    time.sleep(1)
                    self.router = None
                except Exception as e:
                    logging.error("Got unknown exception trying to connect: " + str(e))
            else:
                # Receive data from 
                while self.stay_alive and self.router:
                    try:
                        msg = self.router.recv()
                        msg_dict = json.loads(msg)
                        self.rxed += [[msg,msg_dict]]
                        if "IP" in msg_dict:
                            ip = msg_dict["IP"]
                            if "CMD_STREAM_SAVER" in msg_dict:
                                if "OPCODE" in msg_dict["CMD_STREAM_SAVER"] and msg_dict["CMD_STREAM_SAVER"]["OPCODE"] == "NEW_SAVE":
                                    if ip not in self.saving_instances:
                                        self.saving_instances.update({ ip: copy.copy(self.instance_template) })
                                        if "METADATA" in msg_dict:
                                            self.saving_instances[ip].update(msg_dict["METADATA"])
                                        logging.info("Init saving for IP: " + ip)
                                    else:
                                        logging.error("Already have saving instance for IP: " + ip)
                                elif "OPCODE" in msg_dict["CMD_STREAM_SAVER"] and msg_dict["CMD_STREAM_SAVER"]["OPCODE"] == "START_SAVE":
                                    if ip in self.saving_instances and ip not in self.actively_saving:
                                        self.actively_saving += [ip]
                                        logging.info("Begin saving for IP: " + ip)
                                    elif ip in self.saving_instances and ip in self.actively_saving:
                                        logging.warning("Already actively saving instance for IP: " + ip) 
                                    else:
                                        logging.warning("Have not created save instance for IP: " + ip + ", must do this before beginning save")
                                elif "OPCODE" in msg_dict["CMD_STREAM_SAVER"] and msg_dict["CMD_STREAM_SAVER"]["OPCODE"] == "PAUSE_SAVE":
                                    if ip in self.saving_instances:
                                        self.actively_saving.remove(ip)
                                        logging.info("Pause saving IP: " + ip)
                                    else:
                                        logging.warning("Can't pause stream for IP: " + ip + ", was not actively saving")
                                elif "OPCODE" in msg_dict["CMD_STREAM_SAVER"] and msg_dict["CMD_STREAM_SAVER"]["OPCODE"] == "STOP_SAVE":
                                    self.save_to_mongo(ip)
                                    logging.info("Saving stream from IP: " + ip)
                            
                            elif "TYPE" in msg_dict and "UID" in msg_dict:
                                    self.rxed_cnt0 += 1
                                    UID = msg_dict["UID"]
                                    if ip in self.saving_instances:
                                        self.rxed_cnt1 += 1
                                        if UID not in self.saving_instances[ip]["DATA"]:
                                            self.rxed_cnt2 += 1
                                            self.saving_instances[ip]["DATA"].update( {UID: copy.deepcopy(self.instance_data) })
                                        # Only save if we're actively saving from this IP
                                        elif ip in self.actively_saving:
                                            self.rxed_cnt3 += 1
                                            self.saving_instances[ip]["DATA"][UID]["TS"].append(msg_dict["TS"])
                                            self.saving_instances[ip]["DATA"][UID]["DATA"].append(msg_dict["DATA"])
                            else:
                                logging.error("Stream Server got unknown message: " + msg)
                    except (socket.timeout, WSClient.WebSocketTimeoutException) as e:
                        pass
                    except Exception as e:
                        logging.critical("Unkown exception occurred when receiving data to SS:\n\t" + str(e))
        
    def save_to_mongo(self, ip):
        '''
        Function:
            Stops saving data; cleans up and finishes writing to MongoDB
        Args:
            None
        Returns:
            success: int,
                1 if successful,
                0 if no stream currently running,
                -1 if error stopping stream
        '''

        if ip in self.actively_saving:
            self.actively_saving.remove(ip)
        # Collect all streams data
        self.to_save = copy.deepcopy(self.saving_instances)
        metadata = self.saving_instances.pop(ip) #we pop data from this, making it only the metadata
        data = metadata.pop("DATA")
                
        # Create filename
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dir_path, '..', 'Data', "streams", str(time.time()) + '.simmie')
        
        # Pickle data to that grid fs will chunk it
        logging.info("Dumping data to file for IP: " + ip)
        pickle.dump(data, open(filename, 'wb'))
        
        # Open and pass file handle
        logging.info("Reading data from file")
        f_handle = open(filename, 'rb').read()
        
        # Write to databse
        self.db.write_streams(f_handle, metadata)
        logging.info("Upload complete for IP: " + ip)



    # load_current_data
    def load_current_data(self):
        '''
        Function:
            Load data from the currently running session. Local buffers should be used for
            smaller amounts of data, this should only be used when loading large amounts of data
            and time is not a concern. For example, this may be used by a plotting function to
            plot beta power over the past 20 minutes.
            
            Beginning and end positions must be specific. A stream UID may be specified to retrieve a specific
            stream, otherwise returns all streams (including markers)
        
        Args:
            beg: None, int, float,
                If None, start at the beginning of the session
                If int (negative), start at "beg" samples back from current samples
                If int (positive), start at "beg" samples from the beginning
                If float (negative), start at "beg" seconds back from current time
                If float (positive), start at "beg" seconds from the beginning
                If 0 or 0.0, error (None should be used to indicate the beginning, not zero)
            end: None, int, float,
                If None, finish at the end of the session
                Otherwise the same as begin, except choosing where to end
            (O) stream_uid: unicode str, UID of the stream to retrieve
        
        Returns:
            data: dict,
                Keys are the UIDs of the data streams. Data is a numpy array in the
                format [nchan, nsamples], where the are the earliest samples.
                (Ex. [0,0] is the first samples recorded from channel 0, [0,1] is the second, etc...)
            data_ts: dict,
                Keys are the UIDs of the data streams.
            markers:
                Keys are the UIDs of the marker streams.
            markers_ts:
                Keys are the UIDs of the marker streams.
        
        '''
        data = dict()
        data_ts = dict()
        markers = dict()
        markers_ts = dict()
        for uid,stream in self.selected_streams.items():
            if stream.type == 'REGULAR':
                data[uid] = stream.get_data()
                data_ts[uid] = stream.get_ts()
            else:
                markers[uid] = stream.get_data()
                markers_ts[uid] = stream.get_ts()
                
        return {'data':data,'data_ts':data_ts,'markers':markers,'markers_ts':markers_ts}
    
if __name__ == "__main__":
    # Set up logging
    LOG_FORMAT_NORMAL_DETAIL = '%(asctime)s|%(levelname)s|%(message)s'
    LOG_FORMAT_HIGH_DETAIL = '%(asctime)s|%(levelname).1s|%(filename).20s@%(lineno).4d|%(funcName).20s\n\t%(message)s'
    LOGGING_FORMAT = LOG_FORMAT_HIGH_DETAIL
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT,)
    s = StreamManager("127.0.0.1","5678")
    s.run()