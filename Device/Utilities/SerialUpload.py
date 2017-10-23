# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 16:27:37 2016

@author: marzipan
"""

import serial

###############################################################################
#Serial Upload of Network Parameters###########################################
###############################################################################

def openSerial(self):
    self.ser = serial.Serial(self.port, self.baudrate)  
    self.ser.timeout = 1
    
def autoConnect(self):
    #TODO add support for: OSError: [Errno 16] Device or resource busy: '/dev/ttyACM1'
    self.connected = False
    #get device files with correct vendor id and product id
    ports = list(serial.tools.list_ports.grep('VID:PID=0451:bef3'))
    for p in ports:
        self.port=p[0]
        #connect and flush buffer
        self.openSerial()  
        self.ser.flushOutput()
        self.sendTest('2')
        self.ser.flushInput()  
        #test each for correct identifying response
        self.sendTest('+')
        resp = self.ser.read(20) # if sending '2' failed to stop board tx, this wont work
        if 'IAMEEG64!' in resp:
            self.connected = True
    if self.connected:
        print("succesful connection")
    else:
        print("failure to connect")
        
        
        
        
        
        
        
        
        
        