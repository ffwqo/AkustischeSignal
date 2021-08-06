"""
Base python setup for block measurement
writes to a file called measure_data.txt
if the file already exist measure_data_i is used where i is a integer
Before starting the measurement the data used by the AWG needs to be setup
see [Record length](http://api.tiepie.com/libtiepie/0.9.15/group__scp__timebase__record_length.html) for more information on the buffer size for MM_BLOCK mode

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
#from printinfo import * 
import numpy as np



N = 20000
data = np.zeros(N)
data = array("f", data)
libtiepie.network.auto_detect_enabled = True

libtiepie.device_list.update()

scp = None 
gen = None
for item in libtiepie.device_list:
    if ( item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE)) and (item.can_open(libtiepie.DEVICETYPE_GENERATOR)):
        scp = item.open_oscilloscope()
        if scp.measure_modes & libtiepie.MM_BLOCK:
            gen = item.open_generator()
            if gen.signal_type & libtiepie.ST_ARBITRARY:
                break
        else:
            scp = None
print(scp, gen, flush=True)

if scp and gen:
    try:
        scp.measure_mode = libtiepie.MM_BLOCK
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
        
        print("Starting scp ...", flush=True)
        scp.start()
        print("Starting gen ...", flush=True)
        gen.start()
        print("Both started!", flush=True)

        while not (scp.is_data_ready or scp.is_data_overflow):
            time.sleep(0.01)
        if scp.is_data_overflow:
            print("Data overflow")
            #TODO something eror
        data = scp.get_data()
        print("Got scp data..." , flush=True)
        header = ""
        filename="measure_data.txt"
        i = 0
        while os.path.isfile(filename):
            filename = "measure_data_{}.txt".format(i)
            i += 1


        for i in range(len(scp.channels)):
            header += "Ch{}\t".format(i+1) 

        np.savetxt(filename, np.array(data).transpose(), header=header)
        print("Written file!", flush=True)

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
