There are two primary routes of communication, GUI <-> Command Server and anything routed through the Stream Router, which includes anything passed between the GUI, the LISP client, the Stream Saver client, and data streaming from the AlphaScan.  
  
# GUI <-> Command Server
All GUI commands sent to the command server are passed as JSON strings and have the following format: ```{"OPCODE": Codename, "param1_name": param1, ...}  ``` where ```Codename``` is one of the valid codes listed below in the "Command Server Reference". The parameter names must correspond **EXACTLY** with the parameter names of the Python functions. Again, you can check the "Command Server Reference" for the expected parameter names and types.  
  
All  commmand server responses to the GUI are also JSON strings and have the following format: ```{"RESP":error_name, "CODE":error_code, "MSG":msg,"DATA":data}``` where:  
- ```RESP``` is an response name (see CommandServerResponses.py)
- ```CODE``` is the numeric code
- ```MSG``` is the response message correspondnig the the response name / code
- ```DATA``` is any data associated with the response, in whatever format

# Stream Router
All clients connecting to the Stream Router **MUST** send an "INTRO" message specifying what type of client it is as well as any required information about itself. The intro messages all have the same general format which is the following: ``` {"CLIENT_TYPE":client_type_str , ...}``` where ```...``` indicates additional k,v pairs for any required information. Templates for the different types of clients are as follows:  
  
GUI: ```{ "CLIENT_TYPE":"GUI" }```  
LISP: ```{ "CLIENT_TYPE":"LISP" }```  
Stream Saver: ```{ "CLIENT_TYPE":"STREAM_SAVER" }```  
AlphaScan Data Streamer: ```{ "CLIENT_TYPE":"ASCAN" "ASCAN_IP":str, "ASCAN_PORT":int, "ASCAN_CH":[str]*8, "ASCAN_MASTER":bool}```  
  
All messages sent to the stream router should have a "RECIPIENT" field, an optional "RECIPIENT_IP" field, and a "MSG" field. The following are valid values for the "RECIPIENT" field:
- ```SERVER```, sent internally to the server (mostly for debugging purposes)
- ```LISP```, sends the message to the LISP server
- ```STREAM_SAVER```, sends the message to the stream saver
- ```DATA```, sends the message to both the stream saver and to the LISP server | NOTE: this field is only for use by the AlphaScan streamer
- ```GUI```, sends the message to the GUI at IP address specified in the "RECIPIENT_IP"field | NOTE: "RECIPIENT_IP" field is mandatory here!
  
The following paragraphs will focus on the contents of the "MSG" field.  
  
## GUI <-> LISP
All GUI commands sent to the LISP client are passed as JSON strings and have the following format:   
```{"OPCODE": Codename, "param1_name": param1, ...}  ```  
where ```Codename``` is one of the valid codes listed below in the "LISP Client Reference".  
  
## \* -> Stream Saver
All commands sent to the stream saver are passed as JSON strings and have the following format: ```{"OPCODE": Codename, "NAME": save_name, ...}  ``` where ```Codename``` is one of the valid codes listed below in the "Stream Saver Client Reference".  
  
## AlphaScan Data Stream -> \*
All data sent from the AlphaScan data streamer will be passed as JSON strings and have the following format:
``` {"TYPE":"ASCAN", "TS": int, "DATA": [int]*nchan, "UID":int} ```


```
NEW_SAVE(name, **metadata_and_options)
UPDATE_METADATA(name, **metadata_and_options)
START_SAVE(name)
PAUSE_SAVE(name)
STOP_SAVE(name)
```

```
CONNECT_DEVICE(ports, stream_server_ip, stream_server_port)
DISCONNECT_DEVICE(ports)
SYNC_DEVICE_TIME()
BEGIN_STREAMING()
STOP_STREAMING()
RESET_DEVICE()

ENTER_OTA_MODE()
ENTER_WEB_UPDATE_MODE()

ENTER_AP_MODE()
IS_VALID_AP_MODE()
LOAD_NETWORK_PARAMETERS()
SAVE_NETWORK_PARAMETERS(STRUCT_network_parameters)
UPDATE_DEVICE_NETWORK_PARAMETERS(STRUCT_network_parameters)
PULL_DEVICE_NETWORK_PARAMETERS(port)

LOAD_ACQUISITION_SETTINGS(acquisition_settings_name_or_id)
SAVE_ACQUISITION_SETTINGS(STRUCT_acquisition_settings)
UPDATE_DEVICE_ACQUISITION_SETTINGS(ports, STRUCT_acquisition_settings)
PULL_DEVICE_ACQUISITION_SETTINGS(port)

GET_ACQUISITION_STATS(ports)
GET_STREAMING_STATS(ports)
```







