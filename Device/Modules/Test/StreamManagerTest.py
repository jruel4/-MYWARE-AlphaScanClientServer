# -*- coding: utf-8 -*-
"""
Created on Tue Aug 08 14:55:11 2017

@author: marzipan
"""

import time
from AlphaScan.Controller.Modules.StreamManager import StreamManager

if __name__ == "__main__":

    ch_names = ["F7","Fz","F8","C3","C4","Pz","O1","O2","Fp1","Fp2","F3","F4","Cz","P3","P4","None"]
    description = """
    Testing out NeuroMon GUI, looking for
    frontal theta increase with workload
    increase and sustained occipital / parietal alpha
    decrease while working.
    """

    marker_map = {
            "0 pressed" : "Test_BAD", "NUMPAD0 pressed" : "Test_BAD",
            "1 pressed" : "Test_GOOD", "NUMPAD1 pressed" : "Test_GOOD"
            }

    print("Launching stream manager...\n")
    s = StreamManager()
    metadata = s.create_metadata(
        filename=time.strftime("%Y-%m-%d_%H-%M-%S"),
        user="JCR",
        proctor="Self",
        ch_names=ch_names,
        recording_desc=description,
        marker_desc={"Test_BAD":"Testing bad marker", "Test_GOOD":"Testing good marker"},
        other_metadata={"Test":True})
    
    
    s.select_streams("type='EEG' or type='Markers'")
#    s.map_marker_streams(marker_map)
    s.begin_saving(metadata)
    
    doRun = True
    while doRun:
        i = raw_input("Input 'X' to stop, 'C' to cycle (clear RAM): ")
        if i == "X":
            doRun = False
            print("Stopping...")
            if s.stop_saving() == -1:
                print("Error stopping saving.")
        if i == "C":
            print("Cycling stream saver...")
            if s.stop_saving() == -1:
                print("Error stopping saving.")
            if s.begin_saving(metadata):
                print("Error beginning saving.")
        if i == "R":
            print("Cycling stream saver AND clearing RAM...")
            if s.stop_saving() == -1:
                print("Error stopping saving.")
            if s.begin_saving(metadata):
                print("Error beginning saving.")
            s.clear() #clear buffers
            
            
            