# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 23:25:26 2017

@author: marzipan
"""

import asyncio
import logging
from functools import wraps
import simplejson as json

from Server.CommandServerResponses import CommandServerResponses
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
            assert isinstance(json_error_handler, CommandServerResponses), "JSON error handler MUST be instance of CommandServerResponses, got:\n\t" + str(type(json_error_handler)) + "\nexpected:\n\t" + str(CommandServerResponses)

            try:
                json_parsed = json.loads(json_msg)
            except (TypeError, json.JSONDecodeError):
                return await json_error_handler.ERR_BAD_JSON("Bad JSON received, got: " + json_msg)
            
            # Log the keys and types we got from parsing JSON
            log_msg = " , ".join([str(k) + ":" + str(type(json_parsed[k])) for k in json_parsed.keys()])
            logging.info("JSON received keys of types: " + log_msg)

            # Keys should be ACTUAL parameter names, values are pulled from "json_parsed"
            parameters_to_wrapped_function = dict()
            
            # Check that all expected parameters are in the JSON and verify they are of the correct types
            for p_name in expected_parameters.keys():

                # Parameter not found, raise error
                if p_name not in json_parsed.keys():
                    return await json_error_handler.ERR_BAD_NUM_PARAMS(func.__name__ + ", expected parameter: \"" + p_name + "\", did not receive")

                # If expecting a list, verify list and type of elements
                if isinstance(expected_parameters[p_name], list):
                    expected_type = expected_parameters[p_name][0]

                    if not isinstance(json_parsed[p_name], list):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(func.__name__ + ', parameter "' + p_name + '" expected type: ' + str(list) + " got: " + str(type(json_parsed[p_name])))

                    # Check that all received list elements are of the expected type
                    elif not all(isinstance(x, expected_type) for x in json_parsed[p_name]):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(func.__name__ + ', parameter "' + p_name + '" expected list of type: ' + str(expected_type) + " got: " + ",".join([str(type(p)) for p in  json_parsed[p_name]]))
                        
                    # If all checks passed then add it to our dictionary of parameters to pass to the function
                    else:
                        parameters_to_wrapped_function.update({p_name: json_parsed[p_name]})
                
                # If not a list, then...
                else:
                    expected_type = expected_parameters[p_name]
                    if not isinstance(json_parsed[p_name], expected_type):
                        return await json_error_handler.ERR_BAD_PARAM_TYPES(func.__name__ + ', parameter "' + p_name + '" expected type: ' + str(expected_type) + " got: " + str(type(json_parsed[p_name])))
                    else:
                        parameters_to_wrapped_function.update({p_name: json_parsed[p_name]})

            logging.info("Passing parameters: " + str(parameters_to_wrapped_function) + " to function: " + func.__name__)
# =============================================================================
#             if not parameters_to_wrapped_function:
#                 return await func(self)
#             else:
# =============================================================================
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
        
        self.this_event_loop = asyncio.get_event_loop()
    
    def _runAsyncThreadsafe(self,coroutine, event_loop = None):
        if event_loop:
            return event_loop.run_until_complete(coroutine)
        else:
            return asyncio.run_coroutine_threadsafe(coroutine, self.this_event_loop)
#            return self.this_event_loop.run_until_complete(coroutine)
    
    @validate_json({ "ports":[int], })
    async def connect(self, ports=[]):
        if self.connected:
            return await self.err_handling.ERR_ALREADY_CONNECTED()
        logging.info("Connecting to " + str(len(ports)) + " AlphaScans on ports: [" + ", ".join([str(p) for p in ports]) + "]...")

        dev_tmp = DeviceCluster(port_list = ports)
        devs_sucessfully_connected = dev_tmp.connect_to_device()
        if all(d for d in devs_sucessfully_connected):
            self.device_cluster = dev_tmp
            self.num_devices = len(ports)
            self.device_ports = ports
            self.connected = True
            return await self.err_handling.OK("Succesfully connected.")
        else:
            # TODO: Create specific error code for this OR give a more detailed error (from dev cluster)
            # TODO: automatically check if AP signal is available.
            return await self.err_handling.ERR_WHEN_CONNECTING("Not all devices succesfully connected to, for succesful connections got: " + str(devs_sucessfully_connected))
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
        self.disconnect()
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

        logging.info("Stopping streaming...")

        stat, time, avail, rx, drop = self.device_cluster.terminate_UDP_stream()
        self.is_streaming = False # TODO validate
        
        # These come from Martin - figure out what they mean and if they should be sent/displayed
        logging.info("\n\n"+\
                     "UDP Stats:" + "\n"\
                     "\tstat(?)         | " + str(stat) + "\n" +\
                     "\ttime(of what?)    | " + str(time) + "\n" +\
                     "\tavailability(?)   | " + str(avail) + "\n" +\
                     "\tPackets received  | " + str(rx) + "\n" +\
                     "\tPackets dropped   | " + str(drop) + "\n")

        return await self.err_handling.OK("Succesfully stopped streaming.")


    @validate_json({})
    async def syncTime(self):
        
        # Set up callback
        all_threads_succesfully_started = True
        all_succeeded = True
        error_msg = ""
        def finishedProcessingTimeSync(success, msg):
            # Set up callback
            nonlocal all_threads_succesfully_started
            nonlocal all_succeeded
            nonlocal error_msg
            
            # We have to import this because 
            nonlocal self
            # If any devices fail then we should send an error back to the GUI
            if not success:
                all_succeeded = False
                error_msg = msg

            # Check if all devices are finished
            finished = True
            for i,d in enumerate(self.device_cluster.dev):
                finished &= d.ts.finished.is_set()

            
            #If all devices have finished then process (if success), send response to server
            if finished:
                if not all_threads_succesfully_started:
                    return self._runAsyncThreadsafe(self.err_handler.ERR_OTHER("Was not able to succesfully start all threads"))
                elif all_succeeded:
                    logging.info("Sync succesfully finished")
                    # drift(uS/S), len_offsets, drift_reasonable
                    sync_results = [d.ts.get_drift_stats() for i,d in enumerate(self.device_cluster.dev)]
                    response_data = {}
                    for devno in range(len(sync_results)):
                        response_data.update(
                            { devno: {
                                "DRIFT":sync_results[devno][0],
                                "OFFSETS":sync_results[devno][1],
                                "IS_REASONABLE":bool(sync_results[devno][2]),
                                }
                            }
                        )
                    return self._runAsyncThreadsafe(self.err_handling.OK("Succesfully synced", response_data))
                else:
                    return self._runAsyncThreadsafe(self.err_handler.ERR_BAD_SYNC(error_msg))
            else:
                #let the last callback handle server response
                return
        
        # Run sync
        logging.info("Beginning sync, please wait...")
        threads_succesfully_started = self.device_cluster.time_sync(finishedProcessingTimeSync)
        all_threads_succesfully_started = all(threads_succesfully_started)
        # In case none of the threads succesfully started, then we need to manually respond
        #  to server b/c the callback will never execute
        if not any(threads_succesfully_started):
            self.err_handling.ERR_OTHER("No threads succesfully started!")
            



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

    logging.basicConfig(level=logging.DEBUG)

    ws = stub_websockets()
    e = CommunicationErrors(ws)
    ascan = AscanCommandSender(e)
    _run(ascan.connect(json.dumps({"ports":[50007]})))
    _run(ascan.syncTime(json.dumps({})))
    _run(ascan.disconnect(json.dumps({})))