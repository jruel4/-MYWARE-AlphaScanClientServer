# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:25:26 2017

@author: marzipan
"""

import asyncio
import logging

from AlphaScanClientServer.Server.Errors import CommunicationErrors
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

def validate_json(expected_parameters, json_error_handler_dec_param = None):
    
    # expected_parameters should be a dictionary, keys are ACTUAL parameter names (& str's) and values are the EXPECTED TYPES (or list, with first element as expected type for whole list)
    assert isinstance(expected_parameters, dict), "VALIDATE_JSON: Error, expected_parameters must be a dictionary"
    for v in expected_parameters.values():
        if isinstance(v, list):
            assert len(v) == 1, "VALIDATE_JSON: Can only pass in list to decorator parameters if list contains a single element which represents type for the whole list"
            assert isinstance(v[0], type), "VALIDATE_JSON: Error in expected_parameters, an value was a list but the first element did not contain a valid type"
        else:
            assert isinstance(v, type), "VALIDATE_JSON: Error in expected_parameters, an value was not a valid type"
    
    for k in expected_parameters.keys():
        assert isinstance(k, str), "VALIDATE_JSON: Keys MUST be strings (which correspond to input parameters of decorated function)"

    def decorator(func):
        @wraps(func) # tool to retain orig function metadata
        async def wrapper(self, json_msg, json_error_handler = json_error_handler_dec_param):
            
            if json_error_handler == None:
                json_error_handler = self.err_handler
            assert isinstance(json_error_handler, CommunicationErrors), "JSON error handler MUST be instance of CommunicationErrors"


            # TODO add error handler if JSON load fails
            try:
                json_parsed = json.loads(json_msg)
            except json.JSONDecodeError:
                return await json_error_handler.ERR_OTHER(msg="Bad JSON received, got: " + json_msg)
            
            # Log the keys and types we got from parsing JSON
            log_msg = " , ".join([str(k) + ":" + str(type(json_parsed[k])) for k in json_parsed.keys()])
            logging.info("JSON got keys:types | " + log_msg)

            # Keys should be ACTUAL parameter names, values are pulled from "json_parsed"
            parameters_to_wrapped_function = dict()
            
            # Check that all expected parameters are in the JSON and verify they are of the correct types
            for p_name in expected_parameters.keys():

                # Parameter not found, raise error
                if p_name not in json_parsed.keys():
                    return await json_error_handler.ERR_BAD_NUM_PARAMS(expected="P_NAME="+p_name, received="DID NOT RX")

                # If expecting a list, verify list and type of elements
                if isinstance(expected_parameters[p_name], list):
                    expected_type = expected_parameters[p_name][0]

                    if not isinstance(json_parsed[p_name], list):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(msg=p_name + " expected " + str(list) + " got: " + str(type(json_parsed[p_name])))
                    # Check that all received list elements are of the expected type
                    elif not all(isinstance(x, expected_type) for x in json_parsed[p_name]):
                        log_msg = "VALIDATE_JSON | " + p_name + " expected list of " + str(expected_type) + " got: " + ",".join([str(type(p)) for p in  json_parsed[p_name]])
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(msg=log_msg)
                        
                        # If all checks passed then add it to our dictionary of parameters to pass to the function
                    else:
                        parameters_to_wrapped_function.update({p_name, json_parsed[p_name]})
                
                # If not a list, then...
                else:
                    expected_type = expected_parameters[p_name]
                    if not isinstance(json_parsed[p_name], expected_type):
                        log_msg = "VALIDATE_JSON | " + p_name + " expected type " + str(expected_type) + " got: " + str(type(json_parsed[p_name]))
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(msg=log_msg)
                    else:
                        parameters_to_wrapped_function.update({p_name: json_parsed[p_name]})

            print("params to pass: ", parameters_to_wrapped_function)
            return func(self, **parameters_to_wrapped_function)
        return wrapper
    return decorator

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

    @validate_json({ "ports":[int], })
    async def connect(self, ports=[]):
        if self.connected:
            return await self.err_handler.ERR_ALREADY_CONNECTED()
        logging.info("Connecting to " + str(len(ports)) + " on ports: " + ",".join([str(p) for p in ports]))

        dev_tmp = DeviceCluster(port_list = ports)
        if dev_tmp.connect_to_device():
            self.device_cluster = dev_tmp
            self.num_devices = len(ports)
            self.device_ports = ports
            self.connected = True
            return await self.err_handler.OK(msg="Succesfully connected.")
        else:
            # TODO: Create specific error code for this OR give a more detailed error (from dev cluster)
            # TODO: automatically check if AP signal is available.
            return await self.err_handler.ERR_WHEN_CONNECTING()
# =============================================================================
#             ("Make sure AlphaScan is powered on and wait about 10 " +\
#             "seconds for it to be allocated an IP Adress by your router. " +\
#             "If AlphaScan fails to connect, to will switch to Software " +\
#             "Access Point Mode")
# =============================================================================

    @validate_json({})
    async def disconnect(self):
        if self.is_streaming: return await self.err_handler.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handler.ERR_NOT_CONNECTED()

        logging.info("Disconnecting from AlphaScan(s)...")

        # TODO: Check for succesful disconnect?
        self.device_cluster.close_TCP()
        self.connected = False

        self.err_handling.OK(msg="Succesfully disconnected")

    async def reset(self):
        if self.is_streaming: return await self.err_handler.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handler.ERR_NOT_CONNECTED()
        
        logging.info("Resetting device...")
        
        # TODO: Check if this succeeds
        r = self.device_cluster.generic_tcp_command_BYTE("GEN_reset_device")
        self.disconnect_from_device()
        logging.debug("Got response from AlphaScan: " + str(r))

        self.err_handling.OK(msg="Succesfully reset")

    async def beginStream(self):
        if self.is_streaming: return await self.err_handler.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handler.ERR_NOT_CONNECTED()

        logging.info("Begin streaming...")
        begin_stream_string = self.device_cluster.initiate_TCP_stream()

        # TODO validate
        self.is_streaming = True
        logging.debug("Got response from AlphaScan: " + str(begin_stream_string))
        self.err_handling.OK(msg="Succesfully began streaming")

    async def stopStream(self):
        if not self.is_streaming: return await self.err_handler.ERR_NOT_STREAMING()
        if not self.connected: return await self.err_handler.ERR_NOT_CONNECTED()


        stat, time, avail, rx, drop = self.device_cluster.terminate_UDP_stream()
        self.is_streaming = False # TODO validate
        
        # These come from Martin - figure out what they mean and if they should be sent/displayed
        logging.info("UDP Stats:" + "\n"\
                     "stat(us?)         | " + str(stat) + "\n" +\
                     "time(of what?)    | " + str(time) + "\n" +\
                     "availability(?)   | " + str(avail) + "\n" +\
                     "Packets received  | " + str(rx) + "\n" +\
                     "Packets dropped   | " + str(drop))
        self.err_handling.OK("Succesfully stopped streaming.")


    async def syncTime(self):
        self._Debug.append("beginning sync")
        QMessageBox.information(self, "Synchronizing Time", "Please wait for time sync to complete...")
        
        self.time_begin = time.time()
        self.xt = QTimer()
        self.xt.timeout.connect(self.update_progress)
        self.xt.start(600)
        
        r = self.device_cluster.time_sync()
        self._Debug.append(str(r))
            
        async def update_progress(self):
            self.fake_time += 1
            self.Progress_SyncProgress.setValue(self.fake_time)  
            
            # Check if all devices are finished
            finished = True
            for i,d in enumerate(self.device_cluster.dev):
                s = d.ts.finished.is_set()
                #self._Debug.append(str(i)+" "+str(s))
                finished &= s
                
                
            if (finished):
                self.Progress_SyncProgress.setValue(100) 
                self.xt.stop()
                QMessageBox.information(self, "Sync Complete", "Done!")   
                r = []
                for i,d in enumerate(self.device_cluster.dev):
                    # Process
                    r += [d.ts.process_offsets()]
                key = "[drift(uS/S), len_offsets, drift_reasonable]\n"
                QMessageBox.information(self, "Sync Results", key+str(r))

    async def enterOTA(self):
        r = self.device_cluster.generic_tcp_command_BYTE('GEN_start_ota') 
        msgBox = QMessageBox()
        if 'OTA' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
    async def enterAP(self):
        r = self.device_cluster.generic_tcp_command_BYTE('GEN_start_ap') 
        msgBox = QMessageBox()
        if 'ap_mode' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
    async def enterWebUpdate(self):
        r = self.device_cluster.generic_tcp_command_BYTE('GEN_web_update') 
        msgBox = QMessageBox()
        if 'web_update' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
        
        
# =============================================================================
#         
# class GeneralTab(QWidget):
#     
#     # Define Init Method
#     def __init__(self,Device, Debug):
#         super(GeneralTab, self).__init__(None)
#         
#         #######################################################################
#         # Basic Init ##########################################################
#         #######################################################################
#         
#         self._Device = Device      
#         self._Debug = Debug
#         
#         # Define status vars
#         self.Connected = False
#         self.Streaming = False
#         
#         # Set layout
#         self.layout = QGridLayout()
#         self.setLayout(self.layout) # Does it matter when I do this?
#         
#         # Set layout formatting
#         self.layout.setAlignment(Qt.AlignTop)
#         #TODO self.layout.setColumnStretch(3,1)
#         # TODO prevent horizontal stretch
#         
#         #######################################################################
#         # Status Row ##########################################################
#         #######################################################################
#         
#  
#         
#         self.Button_Disconnect.clicked.connect(self.disconnect_from_device)   
#         
#         #######################################################################
#         # Accelerometer Row ###################################################
#         #######################################################################
#         
#         # Connect Accel Status button signals to slots
#         self.Button_RefreshAccelStatus.clicked.connect(self.update_accel_status)
#         
#         #######################################################################
#         # Power Management Row ################################################
#         #######################################################################
# 
#         # Connect Power Manage button signals to slots
#         self.Button_RefreshPowerStatus.clicked.connect(self.update_power_status)
#         
#         #######################################################################
#         # ADC Row #############################################################
#         #######################################################################
#         
# 
#         # Connect ADC signal to slots
#         self.Button_RefreshAdcStatus.clicked.connect(self.update_adc_status)
#         
#         self.Button_AdcBeginStream.clicked.connect(self.begin_streaming_tcp)
#         self.Button_AdcStopStream.clicked.connect(self.stop_streaming)
#         
#         # Add time sync button
#         self.Button_SyncTime.clicked.connect(self.synchronize_time)
#         
#         #######################################################################
#         # OTA Mode ############################################################
#         #######################################################################
#         self.Button_OtaMode.clicked.connect(self.enter_ota_mode)
#         
#         #######################################################################
#         # AP Mode #############################################################
#         #######################################################################
#         self.Button_ApMode.clicked.connect(self.enter_ap_mode)
#         
#         #######################################################################
#         # Update Command Map ##################################################
#         #######################################################################
# 
#         self.Button_UpdateCmdMap.clicked.connect(self.update_command_map)
#         
#         #######################################################################
#         # Update UDP Delay Value ##############################################
#         #######################################################################
#         self.Button_SetUdpDelayVal.clicked.connect(self.update_udp_delay)
#         
#         #######################################################################
#         # Reset Device ########################################################
#         #######################################################################
#         self.Button_ResetDevice.clicked.connect(self.reset_device)
#         
#         #######################################################################
#         # Auto Connect Enable #################################################
#         #######################################################################
#         self.Button_WebUpdateMode.clicked.connect(self.enter_web_update_mode)
#         
#     @Slot()
#     def update_accel_status(self):
#         if self.Streaming or not self.Connected:
#             self.Text_AccelStatus.setText("ILLEGAL")
#             return
#         accel_status_string = self._Device.generic_tcp_command_BYTE("ACC_get_status")
#         self.Text_AccelStatus.setText(accel_status_string)
#         
#     
#     @Slot()
#     def stop_streaming(self):
# 
#         
#     @Slot()
#     def stop_streaming_tcp(self):
#         if not self.Streaming or not self.Connected:
#             self.Text_GeneralMessage.setText("ILLEGAL: Streaming must be true, Connected must be true")
#             return
#         self._Device.terminate_TCP_stream()
#         self.Streaming = False # TODO validate
#         self.Text_AdcStreamStatus.setText("Stopped streaming")
#         
#     @Slot()
#     def stop_streaming_tcp_X(self):
#         r = self._Device.getPdataSize()
#         self.Text_AdcStreamStatus.setText("Size pData: "+str(r))
#   
#         
#     @Slot()
#     def clear_gen_msg(self):
#         self.Text_GeneralMessage.setText("")
#         
#     @Slot()
# 
#         
#     @Slot()
# 
#         
#     @Slot()
# 
#     
#     @Slot()
#     def update_command_map(self):
#         r = self._Device.update_command_map()
#         msgBox = QMessageBox()
#         if 'map_command' in r:#TODO add response into firmware
#             msgBox.setText("SUCCESS")
#         else:
#             msgBox.setText(r)
#         msgBox.exec_()
#         
#     @Slot()
#     def update_udp_delay(self):
#         r = self._Device.set_udp_delay(int(self.Line_UdpDelayVal.text()))
#         msgBox = QMessageBox()
#         msgBox.setText(r)
#         msgBox.exec_()
#         
#     @Slot()
# 
#         
#     @Slot()
#     def disable_auto_connect(self):
#         self._Debug.append("Disabling auto connect to save tcp buffer response")
#         self.Check_AutoConnectEnable.setCheckState(Qt.CheckState.Unchecked)
#     
#     @Slot()
#     def auto_connect(self):
#         if self.Check_AutoConnectEnable.isChecked() and not self.Streaming:
#             if not self.Connected:
#                 # connect routine 
#                 if self._Device.listen_for_device_beacon():
#                     self._Debug.append("Device found, attempting to connect...")
#                     self.connect_to_device()
#                 else:
#                     # TODO check for Access Point Availability
#                     pass
#             else:
#                 # hearbeat routine, send ALIVE? query, and if no answer then disconnect_from_device
#                 # TODO This has risk of colliding with user actions, consider using an IDLE flag
#                 if self.heartbeatIntervalCounter > 40: 
#                     # reset counter and send alive query
#                     self.heartbeatIntervalCounter = 0
#                     r = self._Device.generic_tcp_command_BYTE("GEN_alive_query")
#                     if "ALIVE_ACK" not in r:
#                         self.heartbeatFailCounter += 1
#                     else:
#                         self.heartbeatFailCounter = 0
#                         
#                     if self.heartbeatFailCounter > 1:
#                         self.disconnect_from_device()
#                         self.heartbeatFailCounter = 0
#                 else:
#                     self.heartbeatIntervalCounter += 1
#                     
#         elif self.Check_AutoConnectEnable.isChecked() and self.Streaming:
#             #TODO check for stream validity
#             pass
#         
#     @Slot()
#     def read_debug_log(self):
#         if self.Check_DebugLogEnable.isChecked() and self.Connected and not self.Streaming:
#             r = self._Device.read_debug_port()
#             if r:
#                 self._Debug.append(r)
#     
#     @Slot()
#     def toggle_debug_state(self):
#         if self.Check_DebugLogEnable.isChecked():
#             if self._Device.open_debug_port():
#                 self._Debug.append("Debug Enabled")
#             else:
#                 self._Debug.append("Debug Enable Failed")
#         else:
#             if self._Device.close_debug_port():
#                 self._Debug.append("Debug Disabled")
#             else:
#                 self._Debug.append("Debug Disable Failed")
#         
#             
#     @Slot()
# 
# =============================================================================
