# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 00:11:24 2017

@author: marzipan
"""

"""

Messages should be in the following format:
    "OPCODE|PARAM1|PARAM2|..."
If an array is passed as a parameter it should be in the format:
    "ELEM0,ELEM1,..."

Example DEV_CON message:
    "DEV_CON|50007,50008,50009"

"OK" if operation succeeded    
"ERR_BAD_OPCODE" if opcode is unrecognized
"ERR_BAD_PARAMS" is valid for all messages with a valid
opcode if the correct number of parameters is not provided

Host communication:
    General:
        DEV_CON:
            Params:
                - Portnos | INT | Device port numbers
            Response:
                - OK
                - ERR_WHEN_CONNECTING
                    - "DEVS_CONNECTED" | ARR, INT | Device numbers which were succesfully connected to 
        DEV_DISCON:
            Params:
                - None
            Response:
                - OK
                - ERR_STIll_STREAMING
                - ERR_BAD_COMM

        BEG_STREAM:
            Params:
                - None
            Response:
                - OK
                - ERR_STILL_STREAMING
                - ERR_NOT_CONNECTED
                - ERR_BAD_COMM

        STOP_STREAM:
            Params:
                - None
            Response:
                - OK
                - ERR_NOT_STREAMING
                - ERR_NOT_CONNECTED
                - ERR_BAD_COMM

        SYNC_TIME:
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

        ENTER_OTA_MODE:
            Params:
                - Devno, INT, which device to sent into OTA
            Response:
                - OK
                - ERR_STILL_STREAMING
                - ERR_NOT_CONNECTED
                - ERR_BAD_COMM

        ENTER_AP_MODE:
            Params:
                - Devno, INT, which device to sent into OTA
            Response:
                - OK
                - ERR_STILL_STREAMING
                - ERR_NOT_CONNECTED
                - ERR_BAD_COMM

        ENTER_WEB_UPDATE_MODE:
            Params:
                - Devno, INT, which device to sent into OTA
            Response:
                - OK
                - ERR_STILL_STREAMING
                - ERR_NOT_CONNECTED
                - ERR_BAD_COMM

        DEV_RESET:
            Params:
                - Devno, INT, which device to sent into OTA
            Response:
                - OK
                - ERR_STILL_STREAMING
                - ERR_NOT_CONNECTED
                - ERR_BAD_COMM

    Access Point Mode:
        Check AP Status:
            Params:
            Response:
        Test AP Validity:
            Params:
            Response:
        Connect to AP:
            Params:
            Response:
        Finalize Configuration:
            Params:
            Response:
    ADC Configuration:
        Push registers:
            Params:
            Response:
        Pull Registers:
            Params:
            Response:
        Load Regmap:
            Params:
            Response:
        Save Regmap:
            Params:
            Response:
    Stats:
        Get LSL Streams:
            Params:
        !STREAM LSL Stream Info:
            Params:
        !STREAM LSL Stream Data (for debugging):
            Params:
    Storage:
        Upload XDF to Server:
        Download XDF from Server:

Slave (Server) commands:
    

"""