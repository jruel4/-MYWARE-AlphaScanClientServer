# -*- coding: utf-8 -*-
"""
Created on Mon Feb 01 18:54:23 2016

@author: marzipan
"""

import requests
import subprocess # NOTE: we use Windows-specific command 'netsh' commands
import socket
import time

class ApConnection:
    
    def __init__(self):
        ''' 
        ApConnection Class Initialization routine'''
        self.interfaces = str()
        self.networks = str()
        self.ApIsAvailable = False
        self.ApConnected = False
        self.associated = False
        self.network_keyword = "esp-open-rtos AP 666"
        
    def read_network_card(self):
        ''' Populate available interfaces and networks, then check to see if 
            AlphaScan access point is available and/or connected.'''
        self.interfaces = subprocess.check_output(["netsh","wlan","show","interfaces"])
        self.networks = subprocess.check_output(["netsh","wlan","show","networks"])
        self.ApIsAvailable = (self.network_keyword in self.networks)
        self.ApConnected = self.ap_connection_status(self.interfaces)

    def ap_connection_status(self,i):
        ''' Parse the interfaces return string to check whether there is a current
            connection to the AP.'''
        i = i.replace('\r','')
        i = i.split('\n')
        n = list()
        for e in i:
            if (len(e) > 1) and ':' in e:
                n += [(e.split(':'))]
        # Check if SSID == AlphaScanAP and State = 'connected'
        connected = False
        associated = False
        for e in n:
            if 'SSID' in e[0]:
                if self.network_keyword in e[1]:
                    associated = True
            if 'State' in e[0]:
                if 'connected' in e[1]:
                    connected = True
        if associated and connected:
            return True
        else:
            return False

    def connect_to_ap(self):
        ''' If the AP is available but not connected, connect to it. '''
        # TODO trouble shoot if profile not currently available - researsh says not possible...
        if self.ApIsAvailable and not self.ApConnected:
            r = subprocess.check_output(["netsh","wlan","connect","name="+self.network_keyword])
            if 'successfully' in r:
                return True
            else:
                return False
 
#   3) If not: request to do so, if so: attempt to communicate is AlphaScan
    def test_ap_connection(self):
        ''' Query to see if connection to AlphaScanAP is valid. '''
        r = self.query_ap("alive?")        
        if 'IAMALPHASCAN' in r:
            return True
        else:
            return False
            
    def query_ap(self,query_text):
        ''' Send arbitrary query text to ap '''
        #TODO make this request to a connected tcp socket, not a http server.
        try:
            r = requests.get("http://192.168.4.1/"+query_text, timeout=4.0)
            return r.text
        except requests.exceptions.Timeout:
            return "timed out"
        except:
            return "unknown exception"
            
    def init_TCP(self):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 50007))
        s.settimeout(2)
        s.listen(10)        
        time.sleep(0.5)
        self.conn,self.dev_addr = s.accept()
        return self.dev_addr
            
    def send_net_params(self, ip, ssid, password,port):
        self.conn.send("ssid_key::"+ssid+"* ,\
                   pass_key::"+password+"* ,\
                   ip_key::"+ip+"* ,\
                   port_key::"+port+"* ,")

#==============================================================================
# # Test Driver
# conn = ApConnection()
# conn.read_network_card()
# conn.connect_to_ap()
# print("connected:        "+str(conn.ApConnected))
# print("available:        "+str(conn.ApIsAvailable))
# conn.init_TCP()
# conn.send_net_params()
#==============================================================================



