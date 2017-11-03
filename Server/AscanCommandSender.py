# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:25:26 2017

@author: marzipan
"""

import asyncio
import logging

from Device.DeviceCluster import DeviceCluster

class GeneralCommands():
    pass


'''
Call decorator as follows:

    For a function which expects one parameter ("a") whose value is a single int:
        @validate_json({"a":int})
    For a function which expects one parameter ("b") whose value is a list of ints:
        @validate_json({"b":[int]})
    For a function which expects two parameters ("c","d") whose values are 1) a list of strings and 2) a single string:
        @validate_json({"c":[str], "d":str})
'''
import collections #for checking if iterable in a nice way
from functools import wraps
import simplejson as json

def validate_json(expected_parameters):
    assert isinstance(expected_parameters, dict), "Expected parameters must be a dictionary"

    def decorator(func):

        @wraps(func)
        def wrapper(json_msg):
            parsed = json.loads(json_msg)
            print(parsed)

            parameters_to_pass = dict()
            for param_name in expected_parameters.keys():
                if param_name not in parsed.keys():
                    print("Error, parameter name not in JSON")
                else:
                    if isinstance(expected_parameters[param_name], list):
                        expected_type = expected_parameters[param_name][0]
                        assert isinstance(expected_type, type), "Expected object type (list)"
                        if not isinstance(parsed[param_name], list):
                            print("Didn't receive list in JSON")
                        else:
                            if False in [isinstance(x, expected_type) for x in parsed[param_name]]:
                                print("Not all elements of JSON list were of the expected type")
                            else:
                                parameters_to_pass.update({param_name, parsed[param_name]})
                    else:
                        expected_type = expected_parameters[param_name]
                        assert isinstance(expected_type, type), "Expected object type (single)"
                        if not isinstance(parsed[param_name], expected_type):
                            print("JSON object not of correct type")
                        else:
                            parameters_to_pass.update({param_name: parsed[param_name]})
            print("params to pass: ", parameters_to_pass)
            return func(**parameters_to_pass)
        return wrapper
    return decorator

@validate_json({'a':int})
def f(**kwargs):
    print("FROM f, kwargs: ", kwargs)

class AscanCommandSender():
    def __init__(self, err_handler):
        self.err_handler = err_handler
        self.device_cluster = None
        self.connected = False
        self.is_streaming = False
        self.num_devices = -1
        self.device_ports = []
        
        args_list = {
                self.connect : [(list, int)],
                
                }

    @input_types([ (list, int),  ])
    async def connect(self, ports, _checkArgs = False):
        if _checkArgs: return 
        
        if self.connected:
            return self.err_handler.ERR_ALREADY_CONNECTED()
        logging.info("Connecting to " + str(len(ports)) + " on ports: " + ",".join([str(p) for p in ports]))

        dev_tmp = DeviceCluster(port_list = ports)
        if dev_tmp.connect_to_device():
            self.device_cluster = dev_tmp
            self.num_devices = len(ports)
            self.device_ports = ports
            self.connected = True
            await self.err_handler.OK(msg="Succesfully connected.")
        else:
            # TODO: Create specific error code for this OR give a more detailed error (from dev cluster)
            # TODO: automatically check if AP signal is available.
            await self.err_handler.ERR_OTHER(msg="Could not succesfully conntect to device(s)")
# =============================================================================
#             ("Make sure AlphaScan is powered on and wait about 10 " +\
#             "seconds for it to be allocated an IP Adress by your router. " +\
#             "If AlphaScan fails to connect, to will switch to Software " +\
#             "Access Point Mode")
# =============================================================================


    async def disconnect(self):
        if not self.Connected: return
        self.Text_ConnectStatus.setText("Disconnecting from AlphaScan...")
        self._Device.close_TCP()
        self.Connected = False
        self.Text_ConnectStatus.setText("Disconnected")
    async def reset(self):
        r = self._Device.generic_tcp_command_BYTE("GEN_reset_device")
        msgBox = QMessageBox()
        msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
    async def beginStream(self):
        if self.Streaming or not self.Connected:
            self.Text_GeneralMessage.setText("ILLEGAL")
            return
        begin_stream_string = self._Device.initiate_TCP_stream()
        self.Streaming = True # TODO validate
        self.Text_AdcStreamStatus.setText(begin_stream_string)
    async def stopStream(self):
        if not self.Streaming or not self.Connected:
            self.Text_GeneralMessage.setText("ILLEGAL: Streaming must be true, Connected must be true")
            return
        stat, time, avail, rx, drop = self._Device.terminate_UDP_stream()
        self.Streaming = False # TODO validate
        self.Text_AdcStreamStatus.setText(stat)
        self.Text_AvailabilityVAL.setText(avail)
        self.Text_PacketRateVAL.setText(time)
        self.Text_TotalDroppedVAL.setText(drop)
        self.Text_TotalReceivedVAL.setText(rx)
    async def syncTime(self):
        self._Debug.append("beginning sync")
        QMessageBox.information(self, "Synchronizing Time", "Please wait for time sync to complete...")
        
        self.time_begin = time.time()
        self.xt = QTimer()
        self.xt.timeout.connect(self.update_progress)
        self.xt.start(600)
        
        r = self._Device.time_sync()
        self._Debug.append(str(r))
            
        async def update_progress(self):
            self.fake_time += 1
            self.Progress_SyncProgress.setValue(self.fake_time)  
            
            # Check if all devices are finished
            finished = True
            for i,d in enumerate(self._Device.dev):
                s = d.ts.finished.is_set()
                #self._Debug.append(str(i)+" "+str(s))
                finished &= s
                
                
            if (finished):
                self.Progress_SyncProgress.setValue(100) 
                self.xt.stop()
                QMessageBox.information(self, "Sync Complete", "Done!")   
                r = []
                for i,d in enumerate(self._Device.dev):
                    # Process
                    r += [d.ts.process_offsets()]
                key = "[drift(uS/S), len_offsets, drift_reasonable]\n"
                QMessageBox.information(self, "Sync Results", key+str(r))

    async def enterOTA(self):
        r = self._Device.generic_tcp_command_BYTE('GEN_start_ota') 
        msgBox = QMessageBox()
        if 'OTA' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
    async def enterAP(self):
        r = self._Device.generic_tcp_command_BYTE('GEN_start_ap') 
        msgBox = QMessageBox()
        if 'ap_mode' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
    async def enterWebUpdate(self):
        r = self._Device.generic_tcp_command_BYTE('GEN_web_update') 
        msgBox = QMessageBox()
        if 'web_update' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
        
        
        
class GeneralTab(QWidget):
    
    # Define Init Method
    def __init__(self,Device, Debug):
        super(GeneralTab, self).__init__(None)
        
        #######################################################################
        # Basic Init ##########################################################
        #######################################################################
        
        self._Device = Device      
        self._Debug = Debug
        
        # Define status vars
        self.Connected = False
        self.Streaming = False
        
        # Set layout
        self.layout = QGridLayout()
        self.setLayout(self.layout) # Does it matter when I do this?
        
        # Set layout formatting
        self.layout.setAlignment(Qt.AlignTop)
        #TODO self.layout.setColumnStretch(3,1)
        # TODO prevent horizontal stretch
        
        #######################################################################
        # Status Row ##########################################################
        #######################################################################
        
 
        
        self.Button_Disconnect.clicked.connect(self.disconnect_from_device)   
        
        #######################################################################
        # Accelerometer Row ###################################################
        #######################################################################
        
        # Connect Accel Status button signals to slots
        self.Button_RefreshAccelStatus.clicked.connect(self.update_accel_status)
        
        #######################################################################
        # Power Management Row ################################################
        #######################################################################

        # Connect Power Manage button signals to slots
        self.Button_RefreshPowerStatus.clicked.connect(self.update_power_status)
        
        #######################################################################
        # ADC Row #############################################################
        #######################################################################
        

        # Connect ADC signal to slots
        self.Button_RefreshAdcStatus.clicked.connect(self.update_adc_status)
        
        self.Button_AdcBeginStream.clicked.connect(self.begin_streaming_tcp)
        self.Button_AdcStopStream.clicked.connect(self.stop_streaming)
        
        # Add time sync button
        self.Button_SyncTime.clicked.connect(self.synchronize_time)
        
        #######################################################################
        # OTA Mode ############################################################
        #######################################################################
        self.Button_OtaMode.clicked.connect(self.enter_ota_mode)
        
        #######################################################################
        # AP Mode #############################################################
        #######################################################################
        self.Button_ApMode.clicked.connect(self.enter_ap_mode)
        
        #######################################################################
        # Update Command Map ##################################################
        #######################################################################

        self.Button_UpdateCmdMap.clicked.connect(self.update_command_map)
        
        #######################################################################
        # Update UDP Delay Value ##############################################
        #######################################################################
        self.Button_SetUdpDelayVal.clicked.connect(self.update_udp_delay)
        
        #######################################################################
        # Reset Device ########################################################
        #######################################################################
        self.Button_ResetDevice.clicked.connect(self.reset_device)
        
        #######################################################################
        # Auto Connect Enable #################################################
        #######################################################################
        self.Button_WebUpdateMode.clicked.connect(self.enter_web_update_mode)
        
    @Slot()
    def update_accel_status(self):
        if self.Streaming or not self.Connected:
            self.Text_AccelStatus.setText("ILLEGAL")
            return
        accel_status_string = self._Device.generic_tcp_command_BYTE("ACC_get_status")
        self.Text_AccelStatus.setText(accel_status_string)
        
    
    @Slot()
    def stop_streaming(self):

        
    @Slot()
    def stop_streaming_tcp(self):
        if not self.Streaming or not self.Connected:
            self.Text_GeneralMessage.setText("ILLEGAL: Streaming must be true, Connected must be true")
            return
        self._Device.terminate_TCP_stream()
        self.Streaming = False # TODO validate
        self.Text_AdcStreamStatus.setText("Stopped streaming")
        
    @Slot()
    def stop_streaming_tcp_X(self):
        r = self._Device.getPdataSize()
        self.Text_AdcStreamStatus.setText("Size pData: "+str(r))
  
        
    @Slot()
    def clear_gen_msg(self):
        self.Text_GeneralMessage.setText("")
        
    @Slot()

        
    @Slot()

        
    @Slot()

    
    @Slot()
    def update_command_map(self):
        r = self._Device.update_command_map()
        msgBox = QMessageBox()
        if 'map_command' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        
    @Slot()
    def update_udp_delay(self):
        r = self._Device.set_udp_delay(int(self.Line_UdpDelayVal.text()))
        msgBox = QMessageBox()
        msgBox.setText(r)
        msgBox.exec_()
        
    @Slot()

        
    @Slot()
    def disable_auto_connect(self):
        self._Debug.append("Disabling auto connect to save tcp buffer response")
        self.Check_AutoConnectEnable.setCheckState(Qt.CheckState.Unchecked)
    
    @Slot()
    def auto_connect(self):
        if self.Check_AutoConnectEnable.isChecked() and not self.Streaming:
            if not self.Connected:
                # connect routine 
                if self._Device.listen_for_device_beacon():
                    self._Debug.append("Device found, attempting to connect...")
                    self.connect_to_device()
                else:
                    # TODO check for Access Point Availability
                    pass
            else:
                # hearbeat routine, send ALIVE? query, and if no answer then disconnect_from_device
                # TODO This has risk of colliding with user actions, consider using an IDLE flag
                if self.heartbeatIntervalCounter > 40: 
                    # reset counter and send alive query
                    self.heartbeatIntervalCounter = 0
                    r = self._Device.generic_tcp_command_BYTE("GEN_alive_query")
                    if "ALIVE_ACK" not in r:
                        self.heartbeatFailCounter += 1
                    else:
                        self.heartbeatFailCounter = 0
                        
                    if self.heartbeatFailCounter > 1:
                        self.disconnect_from_device()
                        self.heartbeatFailCounter = 0
                else:
                    self.heartbeatIntervalCounter += 1
                    
        elif self.Check_AutoConnectEnable.isChecked() and self.Streaming:
            #TODO check for stream validity
            pass
        
    @Slot()
    def read_debug_log(self):
        if self.Check_DebugLogEnable.isChecked() and self.Connected and not self.Streaming:
            r = self._Device.read_debug_port()
            if r:
                self._Debug.append(r)
    
    @Slot()
    def toggle_debug_state(self):
        if self.Check_DebugLogEnable.isChecked():
            if self._Device.open_debug_port():
                self._Debug.append("Debug Enabled")
            else:
                self._Debug.append("Debug Enable Failed")
        else:
            if self._Device.close_debug_port():
                self._Debug.append("Debug Disabled")
            else:
                self._Debug.append("Debug Disable Failed")
        
            
    @Slot()
