# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:25:26 2017

@author: marzipan
"""

import asyncio
import logging

from Server.Errors import CommunicationErrors
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
                json_error_handler = self.err_handling
            assert isinstance(json_error_handler, CommunicationErrors), "JSON error handler MUST be instance of CommunicationErrors, got:\n\t" + str(type(json_error_handler)) + "\nexpected:\n\t" + str(CommunicationErrors)

            try:
                json_parsed = json.loads(json_msg)
            except (TypeError, json.JSONDecodeError):
                return await json_error_handler.ERR_BAD_JSON("Bad JSON received, got: " + json_msg)
            
            # Log the keys and types we got from parsing JSON
            log_msg = " , ".join([str(k) + ":" + str(type(json_parsed[k])) for k in json_parsed.keys()])
            logging.info("JSON got keys:types | " + log_msg)

            # Keys should be ACTUAL parameter names, values are pulled from "json_parsed"
            parameters_to_wrapped_function = dict()
            
            # Check that all expected parameters are in the JSON and verify they are of the correct types
            for p_name in expected_parameters.keys():

                # Parameter not found, raise error
                if p_name not in json_parsed.keys():
                    return await json_error_handler.ERR_BAD_NUM_PARAMS(func.__name__ + ' | expected parameter: "'+p_name + '", did not receive')

                # If expecting a list, verify list and type of elements
                if isinstance(expected_parameters[p_name], list):
                    expected_type = expected_parameters[p_name][0]

                    if not isinstance(json_parsed[p_name], list):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(func.__name__ + ' | "' + p_name + '" expected type: ' + str(list) + " got: " + str(type(json_parsed[p_name])))

                    # Check that all received list elements are of the expected type
                    elif not all(isinstance(x, expected_type) for x in json_parsed[p_name]):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(func.__name__ + ' | "' + p_name + '" expected list of type: ' + str(expected_type) + " got: " + ",".join([str(type(p)) for p in  json_parsed[p_name]]))
                        
                    # If all checks passed then add it to our dictionary of parameters to pass to the function
                    else:
                        parameters_to_wrapped_function.update({p_name: json_parsed[p_name]})
                
                # If not a list, then...
                else:
                    expected_type = expected_parameters[p_name]
                    if not isinstance(json_parsed[p_name], expected_type):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(func.__name__ + ' | "' + p_name + '" expected type: ' + str(expected_type) + " got: " + str(type(json_parsed[p_name])))
                    else:
                        parameters_to_wrapped_function.update({p_name: json_parsed[p_name]})

            logging.info("params to pass: ", parameters_to_wrapped_function)
            return await func(self, **parameters_to_wrapped_function)
        return wrapper
    return decorator

class AscanCommandSender():
    def __init__(self, err_handling):
        self.err_handling = err_handling
        self.device_cluster = None
        self.connected = False
        self.is_streaming = False
        self.num_devices = -1
        self.device_ports = []
        
    @validate_json({ "ports":[int], })
    async def connect(self, ports=[]):
        if self.connected:
            return await self.err_handling.ERR_ALREADY_CONNECTED()
        logging.info("Connecting to " + str(len(ports)) + " AlphaScans on ports: " + ",".join([str(p) for p in ports]))

        dev_tmp = DeviceCluster(port_list = ports)
        if dev_tmp.connect_to_device():
            self.device_cluster = dev_tmp
            self.num_devices = len(ports)
            self.device_ports = ports
            self.connected = True
            return await self.err_handling.OK("Succesfully connected.")
        else:
            # TODO: Create specific error code for this OR give a more detailed error (from dev cluster)
            # TODO: automatically check if AP signal is available.
            return await self.err_handling.ERR_WHEN_CONNECTING()
# =============================================================================
#             ("Make sure AlphaScan is powered on and wait about 10 " +\
#             "seconds for it to be allocated an IP Adress by your router. " +\
#             "If AlphaScan fails to connect, to will switch to Software " +\
#             "Access Point Mode")
# =============================================================================

    @validate_json({})
    async def disconnect(self):
        if self.is_streaming: return await self.err_handling.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()

        logging.info("Disconnecting from AlphaScan(s)...")

        # TODO: Check for succesful disconnect?
        self.device_cluster.close_TCP()
        self.connected = False

        return await self.err_handling.OK("Succesfully disconnected")

    @validate_json({})
    async def reset(self):
        if self.is_streaming: return await self.err_handling.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()
        
        logging.info("Resetting device...")
        
        # TODO: Check if this succeeds
        r = self.device_cluster.generic_tcp_command_BYTE("GEN_reset_device")
        self.disconnect_from_device()
        logging.debug("Got response from AlphaScan: " + str(r))

        return await self.err_handling.OK(msg="Succesfully reset")

    @validate_json({})
    async def beginStream(self):
        if self.is_streaming: return await self.err_handling.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()

        logging.info("Begin streaming...")
        begin_stream_string = self.device_cluster.initiate_TCP_stream()

        # TODO validate
        self.is_streaming = True
        logging.debug("Got response from AlphaScan: " + str(begin_stream_string))

        return await self.err_handling.OK(msg="Succesfully began streaming")

    @validate_json({})
    async def stopStream(self):
        if not self.is_streaming: return await self.err_handling.ERR_NOT_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()


        stat, time, avail, rx, drop = self.device_cluster.terminate_UDP_stream()
        self.is_streaming = False # TODO validate
        
        # These come from Martin - figure out what they mean and if they should be sent/displayed
        logging.info("UDP Stats:" + "\n"\
                     "stat(us?)         | " + str(stat) + "\n" +\
                     "time(of what?)    | " + str(time) + "\n" +\
                     "availability(?)   | " + str(avail) + "\n" +\
                     "Packets received  | " + str(rx) + "\n" +\
                     "Packets dropped   | " + str(drop))
        return await self.err_handling.OK("Succesfully stopped streaming.")


    @validate_json({})
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

    @validate_json({})
    async def enterOTA(self):
        if self.is_streaming: return await self.err_handling.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()
        
        r = self.device_cluster.generic_tcp_command_BYTE('GEN_start_ota') 
        self.disconnect_from_device()

        #TODO add response into firmware
        if 'OTA' in r:
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)


    @validate_json({})
    async def enterAP(self):
        if self.is_streaming: return await self.err_handling.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()
        
        r = self.device_cluster.generic_tcp_command_BYTE('GEN_start_ap') 
        msgBox = QMessageBox()
        if 'ap_mode' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()

    @validate_json({})
    async def enterWebUpdate(self):
        if self.is_streaming: return await self.err_handling.ERR_STILL_STREAMING()
        if not self.connected: return await self.err_handling.ERR_NOT_CONNECTED()
        
        r = self.device_cluster.generic_tcp_command_BYTE('GEN_web_update') 
        msgBox = QMessageBox()
        if 'web_update' in r:#TODO add response into firmware
            msgBox.setText("SUCCESS")
        else:
            msgBox.setText(r)
        msgBox.exec_()
        self.disconnect_from_device()
        
if __name__ == "__main__":
    
    def _run(coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    from AlphaScanClientServer.Stubs.stub_websockets import stub_websockets
    ws = stub_websockets()
    e = CommunicationErrors(ws)
    ascan = AscanCommandSender(e)
    _run(ascan.connect("{\"ports\":[50007]}"))
