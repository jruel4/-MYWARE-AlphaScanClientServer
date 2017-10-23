# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

''' the first line is to show Tam how to use an IDE '''
from pylsl import *

streams = resolve_stream('type','EEG')
for s in streams:
    print(s.source_id())
    
inlet = StreamInlet(streams[0])

while True:
	# get a new sample (you can also omit the timestamp part if you're not interested in it)
	sample, timestamp = inlet.pull_sample()	
	print(timestamp, sample)



