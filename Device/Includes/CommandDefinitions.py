# -*- coding: utf-8 -*-
"""
Created on Sat Feb 06 15:36:27 2016

@author: marzipan
"""

# Declare command dict
TCP_COMMAND = dict()
command_index = 0

def addCommand(name):
    global TCP_COMMAND, command_index
    TCP_COMMAND[name] = command_index
    command_index += 1

###############################################################################    
# General 
###############################################################################
addCommand("GEN_update_cmd_map") #NOTE: this must ALWAYS be first i.e. 0x00
addCommand("GEN_start_ota")      #NOTE: this must ALWAYS be second i.e. 0x01
addCommand("ACC_get_status")
addCommand("GEN_alive_query")    #NOTE: this must ALWAYS be second i.e. 0x02
addCommand("GEN_get_status")
addCommand("GEN_start_ap")
addCommand("GEN_get_dev_ip")
addCommand("GEN_listen_beacon")
addCommand("GEN_get_sys_params")
addCommand("GEN_reset_device")
addCommand("GEN_web_update")

###############################################################################
# ADC
###############################################################################
addCommand("ADC_start_stream")
addCommand("ADC_stop_stream")
addCommand("ADC_get_register")
addCommand("ADC_set_register")
addCommand("ADC_update_register")
addCommand("ADC_set_udp_delay")
addCommand("ADC_send_hex_cmd")

###############################################################################
# POWER
###############################################################################
addCommand("PWR_get_status")

###############################################################################
# ACCEL
###############################################################################
#==============================================================================
# addCommand("ACC_get_status")
#==============================================================================

###############################################################################
# SPIFFS
###############################################################################
addCommand("FS_format_fs")
addCommand("FS_get_net_params")
addCommand("FS_get_fs_info")
addCommand("FS_get_command_map")





