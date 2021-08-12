"""
Base python setup for stream measurement
writes to a file called measure_stream_data.txt
if the file already exist measure_stream__data_i is used where i is a integer
Before starting the measurement the data used by the AWG needs to be setup
see [Osci Modes](http://api.tiepie.com/libtiepie/0.9.15/group__scp__measurements__mode.html) for more information
see http://api.tiepie.com/libtiepie/0.9.15/group__gen__signal_data.html
we measure in chunks thus the data has to be wrapped in a [] for a single measurement
and append to a list of chunks for something continous. TODO change this

Fileformat is
Ch1 Ch2
------------------>
| 1.2 23.2
| 0.7 11.
| 0.1 -12
v
"""
import time 
import os
import sys
from array import array
import libtiepie
from printinfo import *  #from github check for other files on error
import numpy as np




N = 20000
data = np.zeros(N)
data = array("f", data)


"""
we are measuring in chunks therefore we need to _somehow_ devide our data
we do the following:
    set gen data
    start gen, scp
    for chunk in chunks
        append scp data into result
        stop gen
        set gen data to chunk + 1 
    concatenate result
N = 20000 should be a safe buffer/chunk size
"""
chunks = [data]


debug = False #debug flag for additonal information

if debug:
    print_library_info()

libtiepie.network.auto_detect_enabled = True

libtiepie.device_list.update()

scp = None 
gen = None
result = [] #list to hold the data
for item in libtiepie.device_list:
    if ( item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE)) and (item.can_open(libtiepie.DEVICETYPE_GENERATOR)):
        scp = item.open_oscilloscope()
        if scp.measure_modes & libtiepie.MM_STREAM:
            gen = item.open_generator()
            if gen.signal_type & libtiepie.ST_ARBITRARY:
                break
        else:
            scp = None

if scp and gen:
    try:
        scp.measure_mode = libtiepie.MM_STREAM
        scp.sample_frequency = 20e3
        scp.record_length = 10000
        for ch in scp.channels:
            ch.enabled = True
            ch.range = 8
            ch.coupling = libtiepie.CK_DCV

        gen.signal_type = libtiepie.ST_ARBITRARY
        gen.frequency_mode = libtiepie.FM_SAMPLEFREQUENCY
        gen.frequency = 20e3
        gen.amplitude = 4
        gen.offset = 0
        gen.output_on = True 
        gen.set_data(data)
        
        if debug:
            print_device_info(scp)
            print_device_info(gen)
        scp.start()
        gen.start()

        for i in range(len(chunks)):
            #we measure len(chunks) with scp TODO make sure the buffer is small enough
            while not(scp.is_data_ready or scp.is_data_overflow):
                time.sleep(0.01)
            if scp.is_data_overflow:
                break
            d = np.array(scp.get_data())
            """
            scp returns data like 
                 --------->
            #Ch1 | 2 3 5 6 
            #Ch2 | 2 -3 -2 -2
                 V
            result[i] looks like
            | 2 2
            | 3 -3
            | 5 -2
            V 6  -2
            """
            result.append(d.transpose())

            gen.stop()
            if i < len(chunks) -1:
                gen.set_data(chunks[i+1])

        #result will be a list of data arrays need to append them each other
        #TODO might have to transpose first
        #TODO need to figure out the right order here
        data = np.concatenate(result)



        header = ""
        filename="measure_stream_data.txt"
        i = 0
        while os.path.isfile(filename):
            filename = "measure_stream_data_{}.txt".format(i)
            i += 1


        for i in range(len(scp.channels)):
            header += "Ch{}\t".format(i+1) 

        np.savetxt(filename, np.array(data), header=header)

        scp.stop()
        print("Stopped scp ", flush=True)
        gen.stop()
        print("Stopped gen ", flush=True)
    except Exception as e:
        print("Exception: " + str(e))
        print(sys.exc_info()[0], flush=True)
        sys.exit(1)

    del scp
    del gen

else:
    print("No device avaible for measurement")
    sys.exit(1)
sys.exit(0)
