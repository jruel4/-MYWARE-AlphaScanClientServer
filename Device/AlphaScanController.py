# Server code for streaming tcp connection
import socket
from collections import deque
import time
from threading import Thread, Event
from pylsl import StreamInfo, StreamOutlet, local_clock
import random
from Device.Includes.CommandDefinitions import *
from Device.Utilities.stats import get_imp
from Device.Includes.BitPacking import twos_comp
import select
from matplotlib import pyplot as plt
import queue
import numpy as np
from Device.Modules.TimeSync import TimeSync

# JCR - preferred method of outputting to console
import logging

# JCR - used to send data through websockets
import websocket as WSClient

# JCR - for sending JSON objects through WS
import simplejson as json

class AlphaScanDevice:
    
    def __init__(self, portno, stream_router_ip=None, stream_router_port=None):
        
        ###############################################################################
        # Stream Router Settings
        ###############################################################################
        self.stream_router_ip = stream_router_ip
        self.stream_router_port = stream_router_port
        self.errs = None

        ###############################################################################
        # TCP Settings
        ###############################################################################
        self.TCP_IP = '' 
        self.COMM_PORT = portno
               #CONFIGURABLE
        self.user_input = ''
        self.data = ''
        
        ###############################################################################
        # UDP Settings
        ###############################################################################
        self.UDP_IP = "192.168.1.17"      #This gets over written dynamically
        #self.UDP_IP_UNI = "192.168.1.109"
        self.UDP_IP_UNI = "192.168.1.105" # TODO GET RID OF THIS!
        self.UDP_PORT = 2390              #CONFIGURABLE
        
        self.num = 10
        self.MESSAGE = chr(self.num)
        self.num_iter = self.num * 100
        self.skips = 0
        self.reads = 0
        self.DEV_streamActive = Event()
        self.DEV_streamActive.clear()
        self.DEV_log = list()
        self.inbuf = list()  
        self.unknown_stream_errors = 0
        self.begin = 0
        self.end = 0
        self.IS_CONNECTED = False
        self.time_alpha = 0
        self.time_beta = 0
        self.time_intervals = list()
        self.time_interval_count = 0
        self.fifo_queue = queue.Queue()
        self.fifo_queue_imp = queue.Queue()
        self.reg_map = [[False for i in range(8)] for j in range(24)]
        
        self.sqwave = list()
        
        
        self.info = StreamInfo('AS_'+time.strftime("%Y-%m-%d_%H-%M-%S"+str(portno)), 'EEG', 8, 250, 'float32', 'AS_'+time.strftime("%Y-%m-%d_%H-%M-%S"+str(portno)))
        self.outlet = StreamOutlet(self.info)
        self.mysample = [random.random(), random.random(), random.random(),
            random.random(), random.random(), random.random(),
            random.random(), random.random()]
            
        # Impedance outlet
        self.imp_info = StreamInfo('IMP_'+time.strftime("%Y-%m-%d_%H-%M-%S"+str(portno)), 'IMP', 8, 250, 'float32', 'IMP_'+time.strftime("%Y-%m-%d_%H-%M-%S"+str(portno)))
        self.imp_outlet = StreamOutlet(self.imp_info)
            
        self.SysParams = {'vcc':None,
                          'free_heap':None,
                          'mcu_chip_id':None,
                          'sdk_ver':None,
                          'boot_ver':None,
                          'boot_mode':None,
                          'cpu_freq_mhz':None,
                          'flash_chip_id':None,
                          'flash_chip_real_size':None,
                          'flash_chip_size':None,
                          'flash_chip_speed':None,
                          'flash_chip_mode':None,
                          'free_sketch_space':None}
        # Debug port variables
        self.debug_port_open = False
        self.debug_port_no = 2391
        #self.open_debug_port()
        
        # create sync object
        self.ts = TimeSync()
    
    def tobyte(self, x): return bytes([x])
        
    def close_event(self):
        self.DEV_streamActive.clear()
        self.close_TCP()
        self.close_udp_solo()
        
    def open_debug_port(self):
        try:
            self.debug_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.debug_sock.bind(('',self.debug_port_no))
            self.debug_sock.settimeout(0)
            self.debug_port_open = True
            return True
        except socket.timeout:
            return False
    
    def close_debug_port(self):
        try:
            self.debug_sock.close()
            self.debug_port_open = False
            return True
        except socket.timeout:
            return False
    
    def read_debug_port(self):
        if not self.debug_port_open: return False
        try:
            r = self.debug_sock.recv(1024)
            if len(r) > 0:
                return r
        except socket.timeout:
            return False
        
    def init_TCP(self):
        ###############################################################################
        # Initialize TCP Port
        ###############################################################################
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.TCP_IP,self.COMM_PORT)) 
        #TODO error: deal with this exception: [Errno 10013] An attempt was made to access a socket in a way forbidden by its access permissions
        # error: [Errno 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted
        
        self.s.settimeout(10)
        self.s.listen(1)        
        try:
            self.conn,addr = self.s.accept()
            self.conn.settimeout(.0001) # TODO maybe want to make this smaller
            time.sleep(0.01) # time for device to respond
            self.UDP_IP_UNI = addr[0] # TODO this should say TCP_IP
            self.IS_CONNECTED = True
            return True
        except socket.timeout as e:
            self.IS_CONNECTED = False
            self.close_TCP(); # cleanup socket
            return False
            
    def close_TCP(self):
        ################################################################################
        # Close TCP connection
        ################################################################################
        try:
            self.conn.close() #conn might not exist yet
            self.s.close()
            self.IS_CONNECTED = False
        except socket.timeout as e:
            print(e)       
        except AttributeError:
            pass
        
    def close_UDP(self):
        ################################################################################
        # Close UDP connection
        ################################################################################
        try:
            self.sock.close() 
        except socket.timeout as e:
            print(e) 
        except AttributeError as e:
            pass
    
    def DEV_printStream(self):
        global sqwave
        ###############################################################################
        # UDP Stream thread target
        ###############################################################################

        self.skips = 0
        self.reads = 0
        self.unknown_stream_errors = 0
        self.time_interval_count = 0
        self.inbuf = list()
        self.time_intervals = list()
        self.DEV_streamActive.set()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('',self.UDP_PORT))
        self.sock.settimeout(0)
        while self.DEV_streamActive.is_set():
            try:
                self.data = self.sock.recv(128)
                self.inbuf += [ord(self.data[27:])] 
                self.sqwave += [self.data]
                self.outlet.push_sample(self.mysample)
                self.reads += 1
                
                #TODO count interval
                self.count_time_interval()
                
            except socket.error as e:
                if e.errno == 10035:
                    self.skips += 1
                elif e.errno == 9:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.sock.bind(('',self.UDP_PORT))
                    self.sock.settimeout(0)
            except socket.timeout:
                self.unknown_stream_errors += 1
                
    def DEV_printTCPStream_OLD(self):
        global sqwave
        ###############################################################################
        # UDP Stream thread target
        ###############################################################################

        self.reads = 0
        self.unknown_stream_errors = 0
        self.time_interval_count = 0
        self.rx_count = 0
        self.pre_rx = 0
        self.timeout_count = 0
        self.test_inbuf = list()
        self.inbuf = list()
        self.time_intervals = list()
        self.DEV_streamActive.set()
        self.error_array = list()
        
        deviceData = [0 for i in range(8)]
        
        # clear tcp inbuf
        #self.conn.recv(2048) # this is not a proper flush, rx size should be set to match
        self.flush_TCP()
        
        diff = 3
        
        while self.DEV_streamActive.is_set():
            try:
                self.pre_rx += 1
                # TODO Receive and unpack sample from TCP connection
                ready = select.select([self.conn], [], [] , 0)
                if (ready[0]):
                    self.data = self.conn.recv(24+diff)
        
                    self.test_inbuf += [self.data]
                    self.rx_count += 1                
                    
                    #self.inbuf += [ord(self.data)] # #TODO this is suspect since ord should only take 1 character, and will fill quick
                    
                    # Populate fresh channel data into self.mysample
                    for j in range(8):
                        deviceData[j] = [self.data[diff+(j*3):diff+(j*3+3)]] 
                        val = 0
                        for i in range(3):
                            n = deviceData[j][0][i]
                            try:
                                val ^= ord(n) << ((2-i)*8)
                            except ValueError as e:
                                print("value error",e)
                            except TypeError as e:
                                print("value error",e)
                        val = twos_comp(val)
                        self.mysample[j] = val
                    
                    self.sqwave += [self.data]
                    self.outlet.push_sample(self.mysample)
                    self.reads += 1
                    
                    #TODO count interval
                    self.count_time_interval()
                
            except socket.timeout:
                self.timeout_count += 1
                
    def DEV_printTCPStream(self):
        global sqwave
        ###############################################################################
        # UDP Stream thread target
        ###############################################################################

        self.reads = 0
        self.unknown_stream_errors = 0
        self.time_interval_count = 0
        self.rx_count = 0
        self.pre_rx = 0
        self.timeout_count = 0
        self.data_wrong_size = 0
        self.invalid_start = 0
        self.no_valid_start = 0
        self.out_of_data = 0
        self.over_loops = 0
        self.select_not_ready = 0
        self.block_list = list()
        self.test_inbuf = list()
        self.over_loop_list = list()
        self.data_size_list = list()
        self.read_size_list = list()
        self.inbuf = list()
        self.time_intervals = list()
        self.DEV_streamActive.set()
        self.error_array = list()
        self.sqwave = list()
        self.prev_data = None
        
        self.total_buf = ''
        
        deviceData = [0 for i in range(8)]
        
        # clear tcp inbuf
        #self.conn.recv(2048) # this is not a proper flush, rx size should be set to match
        
        self.flush_TCP()
        self.conn.setblocking(0)
        
        while self.DEV_streamActive.is_set():
            try:
                self.pre_rx += 1
                # TODO Receive and unpack sample from TCP connection
                ready = select.select([self.conn], [], [] , 0)
                if (ready[0]):
                    new_data = self.conn.recv(2048)
                    self.total_buf += str(new_data)
                    self.read_size_list += [len(new_data)]
                    self.data += str(new_data)
                    self.total_buf += str(new_data)
                    self.rx_count += 1     
                    self.data_size_list += [len(self.data)]
                
                else:
                    self.select_not_ready += 1
                
                if (len(self.data) >= 29):
                    
                    current_data = None
                    for i in range(len(self.data)):
                        
                        if len(self.data[i:]) >= 29:
                            if ((ord(self.data[i+0]) == 0x7f) and (ord(self.data[i+1]) == 0x7f) and (ord(self.data[i+2]) == 0x7f) and (ord(self.data[i+3]) == 0x7f) and (len(self.data[i+5:]) >= 24)):
                                block_num = ord(self.data[i+4])
                                self.block_list += [int(block_num)]
                                current_data = self.data[i+5:i+29]     
                                if (len(self.data[i+28:]) > 1):
                                    self.data = self.data[i+29:]
                                else:
                                    self.data = ''
                                break
                        else:
                            self.out_of_data += 1
                                                
                        if i == 0:
                            self.over_loops += 1
                            self.over_loop_list += [[self.data[i:],0]]
                        self.over_loop_list[-1][1] += 1
                        
                    if current_data == None:
                        self.no_valid_start += 1
                        continue
        
                    self.test_inbuf += [current_data]
                    
                    #self.inbuf += [ord(self.data)] # #TODO this is suspect since ord should only take 1 character, and will fill quick
                    
                    # Populate fresh channel data into self.mysample
                    for j in range(8):
                        deviceData[j] = [current_data[(j*3):(j*3+3)]] 
                        val = 0
                        for s,n in list(enumerate(deviceData[j][0])):
                            try:
                                val ^= ord(n) << ((2-s)*8)
                            except ValueError as e:
                                print("value error",e)
                            except TypeError as e:
                                print("value error",e)
                        val = twos_comp(val)
                        self.mysample[j] = val
                    
                    self.sqwave += [list(self.mysample)]
                    #self.outlet.push_sample(self.mysample)
                    self.reads += 1
                    
                    #TODO count interval
                    #self.count_time_interval()
                    
                else:
                    self.data_wrong_size += 1
                
            except socket.timeout:
                self.timeout_count += 1
                
        
    def generic_tcp_command_BYTE(self, cmd, extra = ''):
        ###############################################################################
        # Get adc status
        ###############################################################################
        if not self.IS_CONNECTED or (self.DEV_streamActive.is_set() and "ADC_start_stream" not in cmd):
            return "ILLEGAL: Must be connected and not streaming"
        try:
            self.flush_TCP()
            self.conn.send((chr(TCP_COMMAND[cmd]) + extra).encode('utf-8'))
            time.sleep(0.05)
            r_string = self.conn.recv(64) #TODO error: [Errno 10054] An existing connection was forcibly closed by the remote host
        except socket.timeout:
            r_string = 'socket.timeout'
        return r_string
        
    def generic_tcp_command_OPCODE(self, opcode, extra = ''):
        ###############################################################################
        # Get adc status
        ###############################################################################

        self.flush_TCP()
        self.conn.send((chr(opcode) + extra + chr(127)).encode('utf-8'))
        time.sleep(0.05)
        try:
            r_string = self.conn.recv(72) #TODO error: [Errno 10054] An existing connection was forcibly closed by the remote host
        except socket.timeout:
            r_string = 'socket.timeout'
        return r_string
        
    def generic_tcp_command_STRING(self, txt):
        ###############################################################################
        # Get adc status
        ###############################################################################

        self.flush_TCP()
        self.conn.send((txt + chr(127)).encode('utf-8'))
        time.sleep(0.05)
        try:
            r_string = self.conn.recv(64)
        except socket.timeout:
            r_string = 'socket.timeout'
        return r_string
        
    def read_tcp(self, num_bytes=64):
        try:
            r_string = self.conn.recv(num_bytes)
        except socket.timeout:
            r_string = 'socket.timeout'
        return r_string
    
	

    def pull_adc_registers(self): 
     ###############################################################################
     # Get all registers and return as list of lists
     ###############################################################################
     # send generic command to retrieve adc registers
        self.generic_tcp_command_BYTE("ADC_get_register")
        # wait for response, loop a few times to account for possible delay then timeout
        for i in range(4):
            time.sleep(0.5)
            r = self.read_tcp(num_bytes=2048) # ensure this is enough to get whole map
            if (len(r) > 24) and ("bbb" in r) and ("eee" in r):
                self.raw_map = r[r.find("bbb")+len("bbb"):r.find("eee")]
                assert(len(self.raw_map) == 24)               
                for i in range(len(self.raw_map)):
                    for j in range(8):
                        if (ord(self.raw_map[i]) & (0x1 << j) ):
                            self.reg_map[i][j] = True
                        else:
                            self.reg_map[i][j] = False
                return self.reg_map                           
             # return map
            else:
                continue 
        print("RETURNING FALSE")
        return False # Create better error message here, or use proper exception handling...
         
    def push_adc_registers(self, RegMap):
         #TODO push real register map to device
         
         #Build byte characters from reg map
         byte_list = [0 for i in range(24)]
         for i in range(24):
             for j in range(8):
                 if RegMap[i][j]:
                     byte_list[i] |= (0x1 << j)
         
         self.chr_map = ''
         for n in byte_list:
             self.chr_map += chr(n)


         self.flush_TCP()
         self.conn.send((chr(0x0e)))
         time.sleep(0.010)
         self.conn.send('bbb'+self.chr_map+'eee' + chr(127))
         time.sleep(0.05)
         #r = self.generic_tcp_command_BYTE('ADC_set_register', 'bbbhi_there my name is stream shady and i like to cream ladies eee')
         
         return self.chr_map
	
	
    def sync_adc_registers(self):
        ###############################################################################
        # Get all registers and return as list of lists
        ###############################################################################
        return [[True if i % 2 == 0 else False for i in range(8)] for j in range(24)]


    def initiate_UDP_stream(self):
        ###############################################################################
        # Begin UDP adc stream
        ###############################################################################

        # Start UDP rcv thread
        self.LSL_Thread = Thread(target=self.DEV_printStream)
        self.LSL_Thread.start()
        self.DEV_streamActive.set()  
        # Send command to being 
        self.begin = time.time()
        return self.generic_tcp_command_BYTE("ADC_start_stream")
        
    def initiate_TCP_stream(self):
        ###############################################################################
        # Begin TCP adc stream
        ###############################################################################
        
        self.generic_tcp_command_OPCODE(0x03) # begins streaming TCP
        time.sleep(0.100)
        # Start TCP rcv thread
        self.LSL_Thread = Thread(target=self.udp_ack_1_thread)
        self.LSL_Thread.start()
        self.DEV_streamActive.set()  

#        self.FEEDER_THREAD = Thread(target=self.lsl_feeder_thread)
#        self.FEEDER_THREAD = Thread(target=self.stream_router_feeder_thread)
        self.FEEDER_THREAD = Thread(target=self.stream_router_ws_feeder_thread)
        self.FEEDER_THREAD.start()
        self.IMP_THREAD = Thread(target=self.imp_thread)
        self.IMP_THREAD.start()
        # Send command to being 
        self.begin = time.time()
        return "Success"
        
    def initiate_TCP_streamX(self):
        ###############################################################################
        # Begin TCP adc stream
        ###############################################################################

        # Start TCP rcv thread
        self.LSL_Thread = Thread(target=self.udp_ack_1_thread)
        self.LSL_Thread.start()
        self.DEV_streamActive.set()  
        # Send command to being 
        self.begin = time.time()
        return "SUCCESS"
        
    def initiate_TCP_stream_direct(self):
        ###############################################################################
        # Begin TCP adc stream
        ###############################################################################
        self.DEV_streamActive.set()  
        # Send command to being 
        self.begin = time.time()
        self.generic_tcp_command_OPCODE(0x03)
        self.DEV_printTCPStream()

        
    def terminate_UDP_stream(self):
        ###############################################################################
        # End UDP adc stream
        ###############################################################################
        
        #TODO NEED terminatino ACK, if NACK then resend termination command        
        self.end = time.time()
        self.DEV_streamActive.clear()
        time.sleep(0.200) # Give stream thread time to send terminate command
        #self.sock.close() #TODO Confirm its done streaming before closing
        pckt_rate = self.getPdataSize()/(self.end-self.begin)
        return "Not Streaming", str(pckt_rate),  "TODO", str(len(self.inbuf)), "TODO"
        
    def terminate_TCP_stream(self):
        ###############################################################################
        # End UDP adc stream
        ###############################################################################
        
        #TODO NEED terminatino ACK, if NACK then resend termination command        
        self.conn.setblocking(1)
        try:
            self.generic_tcp_command_OPCODE(0xf)
            
        except socket.timeout:
            print("Socket.timeout")
            
        self.end = time.time()
        self.DEV_streamActive.clear()
        time.sleep(0.01)
        pckt_rate = len(self.inbuf)/(self.end-self.begin)
        return "Not Streaming", str(pckt_rate),  "TODO", str(len(self.inbuf)), "TODO"
    
    
    def flush_TCP(self):
        ###############################################################################
        # Clear TCP input buffer
        ###############################################################################
        try:
            self.conn.recv(self.conn.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))
        except socket.timeout:
            print("socket.timeout")
    
    def flush_UDP(self):
        ###############################################################################
        # Clear udp input buffer
        ###############################################################################
        try:
            self.sock.recv(65535)
        except socket.timeout:
            pass
    
    def update_adc_registers(self,reg_to_update):
        #send adc registers to update over tcp
        self.flush_TCP()
        self.conn.send('u'+''.join([str(t) for t in reg_to_update])+chr(127).encode('utf-8'))
        time.sleep(0.01) # Time for device to respond
        return

    def update_command_map(self):
        # create csv string from command map dict
        if not self.IS_CONNECTED or self.DEV_streamActive.is_set():
            return "ILLEGAL: Must be connected and not streaming"
        self.flush_TCP()
        self.conn.send((chr(TCP_COMMAND["GEN_update_cmd_map"]) + "_begin_cmd_map_" + str(TCP_COMMAND) + ',  '+chr(127)).encode('utf-8')) #NOTE: comma is necessary
        time.sleep(0.01)
        try:
            r_string = self.conn.recv(64)
        except socket.timeout:
            r_string = 'timeout'
        return r_string
        
    def get_drop_rate(self):
        i = 0
        drops = 0
        total_pckts = len(self.inbuf)
        if total_pckts == 0: return False
        for n in self.inbuf:
            if i != n:
                drops += 1
                i = n
            if i == 255: #wrap around
                i = 0
            else:
                i += 1
        # return success rate
        return drops
    
    def broadcast_disco_beacon(self):
        # send broadcast beacon for device to discover this host
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(('alpha_scan_beacon_xbx_'+str(self.COMM_PORT)+'_xex').encode(),('255.255.255.255',self.UDP_PORT)) #TODO this subnet might not work on all LAN's (see firmware method)
        # send desired TCP port in this beacon 
        s.close();
        
    def listen_for_device_beacon(self):   
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(('', self.UDP_PORT))
            s.settimeout(0.05) #TODO this blocking causes slight lag while active
            data,addr = s.recvfrom(1024)
            s.close()
            if "I_AM_ALPHA_SCAN" in data:
                return True
        except socket.timeout:
            print("socket.timeout")
        return False
        
    def connect_to_device(self):
        #self.broadcast_disco_beacon() #TODO reimplement
        return self.init_TCP()
        
    def set_udp_delay(self, delay):
        extra = "_b_"+str(delay)+"_e_"
        return self.generic_tcp_command_BYTE("ADC_set_udp_delay", extra)
    
    def parse_sys_commands(self):
        #read tcp buff
        buf = self.read_tcp(1024)
        #check for complete system params respons
        if ('begin_sys_commands' not in buf) or ('end_sys_commands' not in buf):
            return False
        #else begin parsing
        buf_arr = buf.split(",")
        for e in buf_arr:
            for k in self.SysParams.keys():
                if k in e:
                    self.SysParams[k] = e[e.find(":")+1:]
                    break
        return True
    
    def ADC_send_hex_cmd(self,cmd):
        self.generic_tcp_command_BYTE("ADC_send_hex_cmd", chr(cmd))
        
    def count_time_interval(self):
        self.time_beta = time.time()
        self.time_interval_count += 1
        try:        
            if (self.inbuf[-1] == (self.inbuf[-2] + 1)):
                self.time_intervals += [self.time_beta - self.time_alpha]
        except socket.timeout:
            print("socket.timeout")
        self.time_alpha = self.time_beta
            
                
    
    
    
    def unpack_data(data):
        deviceData = [list() for i in range(8)]
        for j in range(8):
            deviceData[j] = [data[3+(j*3):3+(j*3+3)]] 
    
            val = 0
            for s,n in list(enumerate(deviceData[j][0])):
                try:
                    val ^= ord(n) << ((2-s)*8)
                except ValueError as e:
                    print("value error",e)
                except TypeError as e:
                    print("value error",e)
                    
            
            val = twos_comp(val)
            print(val)
            #self.mysample[j] = val
            
    def check_block_list(self):
        p = 255
        errors = 0
        c = 0
        err_list = list()
        for n in self.block_list:
            if n == 0:
                if p != 255: 
                    #print("error",n,p)
                    errors += 1
                    err_list += [(n,p,c)]
            else:
                if p != n-1:
                    #print("error",n,p)
                    errors += 1
                    err_list += [(n,p,c)]
            p = n 
            c += 1
            
        return errors, err_list
            
    def plot_square_wave(self, chan):
        chx = list()
        for d in self.sqwave:
            chx += [d[chan]]
        plt.plot(chx)
        plt.show
                
    def gen_throughput_over_time(self):
        '''
        input: requries that self.red_size_list be populated
        '''
        self.timestamps = [u[0] for u in self.read_size_list]
        read_sizes = [u[1] for u in self.read_size_list]
        self.Bps_ps = list()
        # Cycle over every read event to create an element 
        for i in range(len(self.timestamps)):
            # For every read event take subsequent events in the next second
            t = self.timestamps[i]
            r = read_sizes[i]
            tval = 0
            for j in range(i+1,len(self.timestamps)):
                tval = self.timestamps[j] - t
                if tval < 1.0:
                    r += read_sizes[j]
                else:
                    # Add entry to Bps_ps
                    self.Bps_ps += [(r/tval),tval]
                    # Continue to next Bps_ps entry
                    break 
                
    def plotThroughput(self):
        throughput = [u[0] for u in self.Bps_ps]
        plt.plot(self.timestamps, throughput)
        plt.show()
            
    def gen_block_list(self):
        self.block_list = list()
        packet_size = 29
        for i in range(len(self.total_buf) // packet_size):
            self.block_list += [ord(self.total_buf[4 + packet_size*i])]
                        
    def gen_sq_wave(self):
        deviceData = [0 for i in range(8)]
        packet_size = 29
        self.over_loops = 0
        self.sqwave = list()
        for i in range(len(self.total_buf) // packet_size):    
            current_data = self.total_buf[(5 + (packet_size*i)): (5 + (packet_size*i + 24))]
            header = self.total_buf[(packet_size*i): (packet_size*i) + 4]
            if ord(header[0]) != 0x7f or ord(header[1]) != 0x7f or ord(header[2]) != 0x7f or ord(header[3]) != 0x7f:
                self.over_loops += 1
            for j in range(8):
                deviceData[j] = [current_data[(j*3):(j*3+3)]] 
                val = 0
                for s,n in list(enumerate(deviceData[j][0])):
                    try:
                        val ^= ord(n) << ((2-s)*8)
                    except ValueError as e:
                        print("value error",e)
                    except TypeError as e:
                        print("value error",e)
                val = twos_comp(val)
                self.mysample[j] = val
            
            self.sqwave += [list(self.mysample)]
            
    def debug_overview(self):
        self.gen_block_list()
        self.gen_sq_wave()
        print("ol: ",self.over_loops)
        errs = self.check_block_list()
        if (len(errs) < 10):
            print(errs)
        else:
            print("block miss count: ",len(errs))
        self.plot_square_wave(0)

    def getPdataSize(self):
        return len(self.t_pdata)
        
    def udp_ack_1_thread(self):
        global socket
        UDP_IP = self.UDP_IP_UNI
        UDP_PORT = self.COMM_PORT
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,8192)
        sock.bind(('',UDP_PORT))
        self.sock = sock
        #JCR
        self.raw_vals = list()
        #JCR REMOVE THIS!
        self.resps = []
        def msg(c,token=0x00):
            return bytes([c,ord('_'),0x00])     
        def get_newest_ctr(sock):
            valid = 0
            nctr = -1
            sndr_rc = -1
            data = ''
            while 1:
                try:
                    data = sock.recv(1400)
                    nctr = data[0]
                    sndr_rc = data[2]
                    valid = len(data)
                except socket.timeout:
                    self.resps += ["TIMED"]
                    break
                except socket.error as e:
                # A non-blocking socket operation could not be completed immediately
                    if e.errno == 10035: 
                        self.resps += ["BROKED"]
                        break
                    elif e.errno == 10054:
                        pass #TODO This is not debugged - thrown if UDP on device not ready
                    elif e.errno == 9: #bad file descriptor
                        print("Please stop streaming before exiting GUI")
                        self.DEV_streamActive.clear()
                        return 0,0,0,0
                    else:
                        raise e  
            return nctr,valid,sndr_rc,data
        def get_queue_size(data):
            msb = data[1]
            lsb = data[2]
            return ((msb << 8) | lsb)
        def get_heap_size(data):
            msb = data[3]
            csb = data[4]
            lsb = data[5]
            return ((msb << 16) | (csb << 8) | lsb)
        def parse_and_push(data):
            deviceData = [list() for i in range(8)]
            mysamples = [[0 for i in range(8)] for j in range(57)]
            timestamp_base = 0            
            for idx in range(6,14):
                timestamp_base |= data[idx] << (((idx-6)) * 8)
            self.raw_vals += [data[x] for x in range(6,14)]
            for i in range(57):
                #TODO update calculation below for variable sample rates
                # i.e. 4000 = 1000/250 * 1000 so adjust 250 to variable srate
                timestamp_inc = timestamp_base + (i*4000) # assuming 4,000 microsecond elapse b/w samples
                for j in range(8):
                    deviceData[j] = [data[(24+24*i)+(j*3):(24+24*i)+(j*3+3)]] 
                    val = 0
                    for s,n in list(enumerate(deviceData[j][0])):
                        try:
                            val ^= n << ((2-s)*8)
                        except ValueError as e:
                            print("value error",e)
                        except TypeError as e:
                            print("value error",e)
                    val = twos_comp(val)
                    mysamples[i][j] = val
                self.fifo_queue.put((list(mysamples[i]), timestamp_inc))
            return (mysamples,timestamp_base)
        
        # Stat vars
        self.rtt = list() # delay list
        rp = time.time() # rx previous
        t_data = list() # raw data
        t_q = list() # queue
        t_heap = list() # heap
        self.t_pdata = list() # parsed data
        self.local_qsize = list()
        
        # Core vars
        self.DEV_streamActive.set()
        sleep = 0.033 #TODO may want to tune this down for queue population
        sock.settimeout(0)
        self.totrx = 0
        self.skip = -1
        self.miss = 0
        ctr = 0x00
        
        #####################################
        # Begin Core Loop
        #####################################
        while self.DEV_streamActive.is_set():                                  # Only loop while lock is set 
            sock.sendto(msg(ctr), (UDP_IP, UDP_PORT))                          # Send ack for data block with id==ctr
            time.sleep(sleep)                                                  # Give device time to respond 
            nctr,valid,x,d = get_newest_ctr(sock)                              # Get most recent received message
            self.resps += [nctr,valid,x,d]
            if not valid: self.miss+=1;                                        # If rx message not valid, restart
            elif nctr != (ctr+1)%256: ctr=nctr;self.skip+=1                    # TODO(analyze) If rx message not expected count skip 
            else:
                ctr=nctr;
                self.totrx+=valid;
                rc=time.time();
                self.rtt+=[rc-rp];
                rp=rc;
#                t_data+=[d];
#                t_q+=[get_queue_size(d)];
#                t_heap+=[get_heap_size(d)];
                self.t_pdata+=parse_and_push(d)   # If valid, increment counter and extract data + metrics
                  
        #####################################
        # End Core Loop
        #####################################
        
        # Try to close connection (3x for reliability)
        time.sleep(0.100)
        try:
            for i in range(3):
                sock.sendto(bytes([0xff]*3), (UDP_IP, UDP_PORT))  
            sock.close()
        except socket.error as e:
            if e.errno == 9:
                print("UDP sock closed before sending terminate...")
            else:
                raise e
        # Share stats
        self.t_q = list(t_q)
        self.t_heap = list(t_heap)
        self.t_rawbuf = t_data
        
        
            
    def close_udp_solo(self):
        UDP_IP = self.UDP_IP_UNI
        UDP_PORT = self.COMM_PORT
        try:
            self.sock.sendto(bytes([0xff]*3),(UDP_IP,UDP_PORT))
            self.sock.close()
        except AttributeError: # TODO handle sock not exist exception and create as below
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,8192)
            sock.bind(('',UDP_PORT))
            for i in range(3):
                sock.sendto(bytes([0xff]*3),(UDP_IP,UDP_PORT))
            sock.close()
        except socket.error as e:
            if e.errno == 9: #bad file descriptor, I.e. was already closed...
                pass
            else:
                raise e
    
    def stream_router_ws_feeder_thread(self):
        if not (self.stream_router_ip and self.stream_router_port):
            self.lsl_feeder_thread()
        else:
            self.t_data = list()
            self.t_offsets=list()
            time.sleep(0.500) # was at 0.300
            ws = None
            
            retries = 0
            
            self.ws_uid = None

            # Try connecting to stream router
            while self.DEV_streamActive.is_set():
                if not ws:
                    try:
                        ws = WSClient.create_connection(
                            "ws://" + self.stream_router_ip + ":" + str(self.stream_router_port),
#                            sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY),),
                            timeout=0.1)
                        logging.info("Connection to stream server created")
                        init_msg = {"ASCAN":
                            {"ASCAN_IP":self.UDP_IP_UNI,
                             "ASCAN_PORT":self.COMM_PORT,
                             "ASCAN_CH":["NONE"]*8,
                             "ASCAN_MASTER":True
                             }
                            }
                        ws.send(json.dumps(init_msg))
                        self.ws_uid = json.loads(ws.recv())["UID"]
                        logging.info("Got UID: " + str(self.ws_uid))
                        
                    except socket.timeout as e:
                        logging.error("Webocket client couldn't connect, timed out, retrying...")
                        time.sleep(1)
                        ws = None
                    except Exception as e:
                        print(e)
                else:
                    d = self.fifo_queue.get()
                    self.fifo_queue_imp.put(list(d[0])) # for imp thread
                    # Convert from device time to host time
                    device_timestamp = d[1] 
                    # NOTE: This returns 1D numpy array - NUMPY DOESN'T PLAY NICE WITH JSON!
                    host_timestamp = self.ts.calculate_offset(device_timestamp)
                    self.t_offsets += [[device_timestamp,host_timestamp,local_clock()]]
                    data_msg = {"TYPE":"ASCAN", "TS": host_timestamp[0], "DATA": d[0], "UID":self.ws_uid}

                    # Try to send data to server, break after 5 tries
                    while self.DEV_streamActive.is_set() and ws:
                        try:
                            ws.send(json.dumps(data_msg))
                            retries = 0
                            break
                        except WSClient.WebSocketTimeoutException as e:
                            logging.warning("Sending data to server timed out, retrying...")
                            retries += 1
                        except Exception as e:
                            logging.critical("Unkown exception occurred when sending:\n\t" + str(e))
                            retries += 1
                        finally:
                            if retries > 5:
                                logging.error("Couldn't send data to server, closing connection.")
                                if ws:
                                    ws.close()
                                ws = None

# =============================================================================
#                     # If we want to send binary in the future this is how ir should be done 
#                     ws.send(d[0], opcode=WSClient.ABNF.OPCODE_BINARY)
# =============================================================================
                
                    self.t_data += [d[0]]
                    self.local_qsize += [self.fifo_queue.qsize()]
                    if(self.fifo_queue.qsize() > 250):
                        time.sleep(0.002) # was 0.004
                    else:
                        time.sleep(0.004) # was 0.004
            if ws:
                ws.close()
            ws = None


        
        
        
    
    def stream_router_feeder_thread(self):
        if not (self.stream_router_ip and self.stream_router_port):
            self.lsl_feeder_thread()
        else:
            self.t_data = list()
            self.t_offsets=list()
            time.sleep(0.500) # was at 0.300
            logging.info("Attempting to connect to stream router server, ip: " + self.stream_router_ip + " port: " + str(self.stream_router_port))
            retry_time = 0.5
            sr_sock = None

            # Try connecting to stream router
            while self.DEV_streamActive.is_set():
                if not sr_sock:
                    try:
                        sr_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sr_sock.connect((self.stream_router_ip, self.stream_router_port))
                        logging.info("Succesfully connected to stream router server")
                        import simplejson as json

                        init_msg = {"ALPHASCAN": {"portno":self.COMM_PORT}}
                        sr_sock.send(json.dumps(init_msg).encode())
                        sr_sock.settimeout(0.1)
                        retries = 10
                        ack=""
                        while self.DEV_streamActive.is_set():
                            # Check if socket has data
                            try:
                                ack = sr_sock.recv(3)
                                self.errs = ack
                            except socket.timeout:
                                pass
                            # Check that we received something, if it's not "ACK" then restart comms
                            if ack and "ACK" in ack.decode():
                                logging.info("Received ack")
                                sr_sock.setblocking(False)
                                break
                            elif ack and "ACK" not in ack.decode():
                                logging.error("Did not receive ack from stream router server, restarting communications")
                                sr_sock.close()
                                sr_sock = None
                                break
                            else:
                                # We didn't receive anything, try again
                                retries -= 1

                            # If we're out of retries then restart the communication process
                            if retries < 1:
                                logging.error("Did not receive any data from stream router server, restarting communications")
                                sr_sock.close()
                                sr_sock = None
                                break
                        continue
                    except socket.error as e:
                        logging.error("Error connecting to stream router server, got error: " + str(e.errno) + ", trying again in: " + str(retry_time))
                        logging.debug("Full socket error object: \n" + str(e))
                        time.sleep(retry_time)
                        retry_time = min([retry_time+0.5, 5])
                        sr_sock = None
                        continue
                
                d = self.fifo_queue.get()
                self.fifo_queue_imp.put(list(d[0])) # for imp thread
                # Convert from device time to host time
                device_timestamp = d[1] 
                host_timestamp = self.ts.calculate_offset(device_timestamp)
                self.t_offsets += [[device_timestamp,host_timestamp,local_clock()]]
                sr_sock.send(d[0])
                
                self.t_data += [d[0]]
                self.local_qsize += [self.fifo_queue.qsize()]
                if(self.fifo_queue.qsize() > 250):
                    time.sleep(0.002) # was 0.004
                else:
                    time.sleep(0.004) # was 0.004
        
    def lsl_feeder_thread(self):
        self.t_data = list()
        self.t_offsets=list()
        time.sleep(0.500) # was at 0.300
        while self.DEV_streamActive.is_set():    
            d = self.fifo_queue.get()
            self.fifo_queue_imp.put(list(d[0])) # for imp thread
            
            # Convert from device time to host time
            device_timestamp = d[1] 
            host_timestamp = self.ts.calculate_offset(device_timestamp)
            self.t_offsets += [[device_timestamp,host_timestamp,local_clock()]]
            self.outlet.push_sample(d[0], timestamp=host_timestamp)
            
            self.t_data += [d[0]]
            self.local_qsize += [self.fifo_queue.qsize()]
            if(self.fifo_queue.qsize() > 250):
                time.sleep(0.002) # was 0.004
            else:
                time.sleep(0.004) # was 0.004
            
    def get_ch_impedance(self,ch=4):
        # data to np
        data = np.asarray(self.t_data) # this is not thread-safe
        chdata = data[:,ch]            
        ivt = list()
        win_len = 250
        for i in range(len(chdata)-win_len):
            frame = chdata[i:i+win_len]
            ivt += [get_imp(frame)]
        plt.plot(ivt)
        plt.show()
        return np.mean(ivt)
        
    def get_ch_impedance_threadsafe(self,buf): # buf is list of lists
        imps = [0 for i in range(8)]
        data = np.asarray(buf) # this is not thread-safe
        for ch in range(8):
            chdata = data[:,ch]   
            imps[ch] = get_imp(chdata)
        return imps
        
        
        
    def imp_thread(self):
        window_size = 250
        update_rate = 30.0 #Hz
        buf = deque([[0 for i in range(8)]], window_size)
        # calculate impedances based on slices of the timer series - pull via lsl
        idx = 0
        while self.DEV_streamActive.is_set(): 
            while idx < (window_size/update_rate) and self.DEV_streamActive.is_set():
                buf.append(self.fifo_queue_imp.get())
                idx += 1
            # calculate ch imp and push
            self.imp_outlet.push_sample(self.get_ch_impedance_threadsafe(buf))
            idx = 0
            
            
    def time_sync(self, callback_fn):
        logging.info("Beginning sync on device w/ portno: " + str(self.COMM_PORT))
        self.generic_tcp_command_OPCODE(0x7)
        time.sleep(1.0)
        return self.ts.sync(self.UDP_IP_UNI,self.COMM_PORT - 50007, callback_fn)
        
            
            
          
          
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    a = AlphaScanDevice(50007, "localhost", 5678)
    a.connect_to_device()
    a.time_sync(lambda _,__: a.initiate_TCP_stream())
    def kk(x = 0):
        a.terminate_UDP_stream()
        if x:
            a.close_TCP()
