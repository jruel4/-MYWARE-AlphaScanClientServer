# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 03:09:18 2017

@author: marzipan
"""
import sys
sys.path.append('..')

from Modules.TimeSync import TimeSync
from DeviceCluster import DeviceCluster
import time
import logging

class DeviceGeneral():
    def __init__(self, ws, err):
        self.err = err
        self.ws = ws
        
        self.COMMANDS = {
            "INTERNAL_TEST" : print,
            "DEV_CON" : self.deviceConnect,
            "DEV_DISCON" : self.deviceDisconnect,
            "DEV_RESET" : self.deviceReset,
            "BEG_STREAM" : self.beginStream,
            "STOP_STREAM" : self.stopStream,
            "SYNC_TIME" : self.syncTime,
            "ENTER_OTA_MODE" : self.enterOTA,
            "ENTER_AP_MODE" : self.enterAP,
            "ENTER_WEB_UPDATE_MODE" : self.enterWebUpdate,
        }
        
        self.connected = False
        self.streaming = False
        self.portnos = None
        
        TODO
        # add method to "DeviceCluster" which allows changing the number of devices on the fly
        self._device_master = DeviceCluster()

    def deviceConnect(self, args):
        '''
        Params:
            - Portnos | [INT] | Device port numbers
        Response:
            - OK
            - ERR_WHEN_CONNECTING
            - "DEVS_CONNECTED" | [INT] | Device numbers which were succesfully connected to 
        '''
        # Check if already connected and validity of parameters
        if len(args) != 1: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 1, len(args))
        try:
            self.portnos = [int(s) for s in args.split(",")]
        except ValueError:
            return self.err.ERR_BAD_PARAM_TYPES(self.ws)
        if self.connected: return self.err.ERR_ALREADY_CONNECTED(self.ws)        

        # Try to connect
        if self._device_master.connect_to_device():
            self.connected = True
            return self.err.OK("Succesfully connected")
        else:
            return self.err.ERR_WHEN_CONNECTING()
            
                
    def deviceDisconnect(self, args):
        '''
        Params:
            - None
        Response:
            - OK
            - ERR_STIll_STREAMING
            - ERR_BAD_COMM
        '''

        # Check params, if already disconnected or currently streaming
        if len(args) != 0: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 0, len(args))
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        # Disconnect
        self._device_master.close_TCP()
        self.connected = False
        return self.err.OK("Succesfully disconnected")
        
    def deviceReset(self, args):
        '''
        Params:
            - Devno, INT, which device to sent into OTA
        Response:
            - OK
            - ERR_STILL_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM

        '''
        # Check params, if already disconnected or currently streaming
        if len(args) != 1: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 1, len(args))
        try:
            devno = int(args[0])
        except ValueError:
            return self.err.ERR_BAD_PARAM_TYPES(self.ws)
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        # Reset
        r = self._device_master.generic_tcp_command_BYTE("GEN_reset_device")
        self.disconnect_from_device()
        self.err.OK("Device reset: " + str(r))

    def beginStream(self, args):
        '''
        Params:
            - None
        Response:
            - OK
            - ERR_STILL_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM

        '''
        # Check params, if already disconnected or currently streaming
        if len(args) != 0: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 0, len(args))
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        begin_stream_string = self._device_master.initiate_TCP_stream()
        self.streaming = True # TODO validate
        self.err.OK("Streaming..." + begin_stream_string)

    def stopStream(self, args):
        '''
        Params:
            - None
        Response:
            - OK
            - ERR_NOT_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM
        '''
        # Check params, if already disconnected or currently streaming
        if len(args) != 0: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 0, len(args))
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        stat, time, avail, rx, drop = self._device_master.terminate_UDP_stream()
        self.streaming = False # TODO validate
        logstr = "Streaming stopped" +\
                    "Status: " + stat +\
                    "Availability: " + avail +\
                    "Packet Rate: " + time +\
                    "Total Dropped: " + drop +\
                    "Total RX: " + rx
        self.err.OK(logstr)

    def syncTime(self, args):        
        '''
        Params:
            - None
        Response:
            - OK
                - "DEV_TIMES" | 2D ARR, INT | Devs x Times array of uncleaned times
                - "DEV_TIMES_FIT" | 2D ARR, INT | Devs x Times array of fitted times
            - ERR_BAD_SYNC
                - "DEV_TIMES" | 2D ARR, INT | Devs x Times array of uncleaned times
                - "DEV_TIMES_FIT" | 2D ARR, INT | Devs x Times array of fitted times
            - ERR_STILL_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM
        '''
        
        # Check params, if already disconnected or currently streaming
        if len(args) != 0: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 0, len(args))
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        
        self._Debug.append("beginning sync")
        QMessageBox.information(self, "Synchronizing Time", "Please wait for time sync to complete...")
        
        self.time_begin = time.time()
        self.xt = QTimer()
        self.xt.timeout.connect(self.update_progress)
        self.xt.start(600)
        
        r = self._device_master.time_sync()
        self._Debug.append(str(r))
        

    def _update_progress(self):
        self.fake_time += 1
        self.Progress_SyncProgress.setValue(self.fake_time)  
        
        # Check if all devices are finished
        finished = True
        for i,d in enumerate(self._device_master.dev):
            s = d.ts.finished.is_set()
            #self._Debug.append(str(i)+" "+str(s))
            finished &= s
            
            
        if (finished):
            self.Progress_SyncProgress.setValue(100) 
            self.xt.stop()
            QMessageBox.information(self, "Sync Complete", "Done!")   
            r = []
            for i,d in enumerate(self._device_master.dev):
                # Process
                r += [d.ts.process_offsets()]
            key = "[drift(uS/S), len_offsets, drift_reasonable]\n"
            QMessageBox.information(self, "Sync Results", key+str(r))

    def enterOTA(self, args):
        '''
        Params:
            - Devno, INT, which device to sent into OTA
        Response:
            - OK
            - ERR_STILL_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM

        '''

        # Check params, if already disconnected or currently streaming
        if len(args) != 1: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 1, len(args))
        try:
            devno = int(args[0])
        except ValueError:
            return self.err.ERR_BAD_PARAM_TYPES(self.ws)
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        # Enter OTA
        r = self._device_master.generic_tcp_command_BYTE('GEN_start_ota')         
        if 'OTA' in r:#TODO add response into firmware
            self.disconnect_from_device()
            return self.err.OK("Entering OTA mode")
        else:
            return self.err.ERR_BAD_COMM("Error entering OTA, message: " + str(r))

    def enterAP(self, args):
        '''
        Params:
            - Devno, INT, which device to sent into OTA
        Response:
            - OK
            - ERR_STILL_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM
    '''

        # Check params, if already disconnected or currently streaming
        if len(args) != 1: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 1, len(args))
        try:
            devno = int(args[0])
        except ValueError:
            return self.err.ERR_BAD_PARAM_TYPES(self.ws)
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        r = self._device_master.generic_tcp_command_BYTE('GEN_start_ap')
        if 'ap_mode' in r:#TODO add response into firmware
            self.disconnect_from_device()
            return self.err.OK("Entering AP mode")
        else:
            return self.err.ERR_BAD_COMM("Error entering AP mode, message: " + str(r))
        
    def enterWebUpdate(self, args):
        '''
        Params:
            - Devno, INT, which device to sent into OTA
        Response:
            - OK
            - ERR_STILL_STREAMING
            - ERR_NOT_CONNECTED
            - ERR_BAD_COMM
        '''

        # Check params, if already disconnected or currently streaming
        if len(args) != 1: return self.err.ERR_BAD_NUM_PARAMS(self.ws, 1, len(args))
        try:
            devno = int(args[0])
        except ValueError:
            return self.err.ERR_BAD_PARAM_TYPES(self.ws)
        if not self.connected: return self.err.ERR_NOT_CONNECTED()
        if self.streaming: return self.err.ERR_STIll_STREAMING()

        r = self._device_master.generic_tcp_command_BYTE('GEN_web_update')
        if 'web_update' in r:#TODO add response into firmware
            self.disconnect_from_device()
            return self.err.OK("Entering web update mode")
        else:
            return self.err.ERR_BAD_COMM("Error entering web update, message: " + str(r))