from AlphaScanController import AlphaScanDevice
import numpy as np

class DeviceCluster:
    """
    The DeviceCluster class serves to coordinate the control of multiple 
    AlphaScan Devices. The GUI should never directly call AlphaScanDevice
    methods, it should go through the Device cluster instead.
    """
    
    def __init__(self, port_list = [50007]):
        self.num_devices = len(port_list)
        self.dev = [AlphaScanDevice(i) for i in port_list]
    
    def open_debug_port(self):
        for d in self.dev:
            d.open_debug_port()
        return "unimplemented r-code"
    
    def close_debug_port(self):
        for d in self.dev:
            d.open_debug_port()
        return "unimplemented r-code"
    
    def read_debug_port(self):
        for d in self.dev:
            d.close_debug_port()
        return "unimplemented r-code"
        
    def init_TCP(self):
        for d in self.dev:
            d.init_TCP()
        return "unimplemented r-code"
            
    def close_TCP(self):
        for d in self.dev:
            d.close_TCP()
        return "unimplemented r-code"
        
    def close_UDP(self):
        for d in self.dev:
            d.close_UDP()
        return "unimplemented r-code"
    
    def close_event(self):
        for d in self.dev:
            d.close_event()
        return "unimplemented r-code"
                
    def generic_tcp_command_BYTE(self, cmd, extra = ''):
        response = ''
        for d in self.dev:
            response += d.generic_tcp_command_BYTE("ACC_get_status")
        return response
        
    def generic_tcp_command_OPCODE(self, opcode, _extra = ''):
        for d in self.dev:
            d.generic_tcp_command_OPCODE(opcode, extra=_extra)
        return "unimplemented r-code"
        
    def generic_tcp_command_STRING(self, txt):
        for d in self.dev:
            d.generic_tcp_command_STRING(txt)
        return "unimplemented r-code"
        
    def read_tcp(self, _num_bytes=64):
        for d in self.dev:
            d.read_tcp(num_bytes=_num_bytes)	
        return "unimplemented r-code"

    def pull_adc_registers(self, devNum=0):
        if(devNum in range(len(self.dev))):
            retMsg = "PULL: Pulled from device number " + str(devNum)
            return self.dev[devNum].pull_adc_registers(), retMsg
        else:
            return False, "PULL: Invalid device number " + str(devNum)
#        for d in self.dev:
#            d.pull_adc_registers()
#        return "unimplemented r-code"
 
    def push_adc_registers(self, RegMap, devNum=[]):
        if(devNum == []):
            for d in self.dev:
                d.push_adc_registers(RegMap)
            return "PUSH: Pushed to all " + str(len(self.dev)) + "devices"
        else:
            if(devNum in range(len(self.dev))):
                self.dev[devNum].push_adc_registers(RegMap)
                return "PUSH: Pushed to device " + str(devNum)
            else:
                return "PUSH: Invalid device number"
	
    def sync_adc_registers(self):
        for d in self.dev:
            d.sync_adc_registers()
        return "unimplemented r-code"

    def initiate_UDP_stream(self):
        for d in self.dev:
            d.initiate_UDP_stream()
        return "unimplemented r-code"
        
    def initiate_TCP_stream(self):
        for d in self.dev:
            d.initiate_TCP_stream()
        return "unimplemented r-code"
        
    def initiate_TCP_streamX(self):
        for d in self.dev:
            d.initiate_TCP_streamX()
        return "unimplemented r-code"
        
    def initiate_TCP_stream_direct(self):
        for d in self.dev:
            d.initiate_TCP_stream_direct()
        return "unimplemented r-code"
        
    def terminate_UDP_stream(self):
        for d in self.dev:
            d.terminate_UDP_stream()
        return ['NULL' for i in range(5)]
        
    def terminate_TCP_stream(self):
        for d in self.dev:
            d.terminate_TCP_stream()
        return "unimplemented r-code"
    
    def flush_TCP(self):
        for d in self.dev:
            d.flush_TCP()
        return "unimplemented r-code"
    
    def flush_UDP(self):
        for d in self.dev:
            d.flush_UDP()
        return "unimplemented r-code"
    
    def update_adc_registers(self,reg_to_update):
        for d in self.dev:
            d.update_adc_registers(reg_to_update)
        return "unimplemented r-code"

    def update_command_map(self):
        for d in self.dev:
            d.update_command_map()
        return "unimplemented r-code"
        
    def get_drop_rate(self):
        for d in self.dev:
            d.get_drop_rate()
        return "unimplemented r-code"
    
    def broadcast_disco_beacon(self):
        for d in self.dev:
            d.broadcast_disco_beacon()
        return "unimplemented r-code"
        
    def listen_for_device_beacon(self):   
        for d in self.dev:
            d.listen_for_device_beacon()
        return "unimplemented r-code"
        
    def connect_to_device(self):
        r = [False for i in range(self.num_devices)]
        for i in range(self.num_devices):
            r[i] = self.dev[i].connect_to_device()
        print(r)
        return True
        
    def set_udp_delay(self, delay):
        for d in self.dev:
            d.set_udp_delay(delay)
        return "unimplemented r-code"
    
    def parse_sys_commands(self):
        for d in self.dev:
            d.parse_sys_commands()
        return "unimplemented r-code"
    
    def ADC_send_hex_cmd(self,cmd):
        for d in self.dev:
            d.ADC_send_hex_cmd(cmd)
        return "unimplemented r-code"
        
    def count_time_interval(self):
        for d in self.dev:
            d.count_time_interval()
        return "unimplemented r-code"
            
    def close_udp_solo(self):
        for d in self.dev:
            d.close_udp_solo()
        return "unimplemented r-code"
    
    def get_stream_stats(self):
        keys = ['avg_rtt', 'std_rtt', 'min_rtt', 'max_rtt', 'miss', 'skip']
        res = {k:[] for k in keys}
        for d in self.dev:
            res['avg_rtt'] += [np.mean(d.rtt)]
            res['std_rtt'] += [np.std(d.rtt)]
            res['min_rtt'] += [np.min(d.rtt)]
            res['max_rtt'] += [np.max(d.rtt)]
            res['miss'] += [np.mean(d.miss)]
            res['skip'] += [np.mean(d.skip)]
        return res
          
    def time_sync(self):
        r = []
        for d in self.dev:
            r += [d.time_sync()]
        return r