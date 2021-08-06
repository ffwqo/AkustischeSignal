import time 
from array import array
import numpy as np
import os
import sys
import libtiepie
#from printinfo import * 
import numpy as np
import matplotlib.pyplot as plt

Nbits = 10
bits = np.array(np.random.rand(Nbits) > 0.5, dtype=int)
fc = 10e+3 #carrier
df = 100
fre = []
lower_fre = fc - len(bits) * df
for i in range(len(bits)):
	f = lower_fre + i * 2 * df
	fre.append(f)

A = 10
data = np.zeros(8192)
N = 8192 # final data size...
fs = 20e+3
T = 1/ fs #sample spacing?
x = np.linspace(0.0, N*T, N) # time

#--------------FDM
#for i in range(Nbits):
#    data = data + bits[i] * A * np.sin(2*np.pi * fre[i] * x)


#--------------OOK
for i in range(Nbits):
    interval = len(x) // Nbits
    data[i * interval: (i+1) * interval] = bits[i] * A
    #data[i * interval: (i+1) * interval] = bits[i] * A * np.sin(np.pi * 2 * fc * x[i * interval: (i+1)* interval])



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
        
        
        
        
        #csv_file = open("OscilloscopeStream.csv", "w") 
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
        filename="measure_data.dat"
        i = 0
        while os.path.isfile(filename):
            filename = "measure_data_{}.out".format(i)
            i += 1


        for i in range(len(scp.channels)):
            header += "Ch{}\t".format(i+1) 

        np.savetxt(filename, np.array(data).transpose(), header=header)
        print("Written file!", flush=True)

        #try:
        #    csv_file.write("Sample")
        #    for i in range(len(scp.channels)):
        #        csv_file.write(";Ch" + str(i+1))
        #    csv_file.write(os.linesep)
        #    print() 
        #    sample = 0
        #    for chunk in range(10): 
        #        print("Data chunk " + str(chunk + 1))
        #        while not (scp.is_data_ready or scp.is_data_overflow):
        #            time.sleep(0.01)
        #        if scp.is_data_overflow:
        #            print("Data overflow")
        #            break
        #        data = scp.get_data()
        #        for i in range(len(data[0])):
        #            csv_file.write(str(sample + i))
        #            for j in range(len(data)):
        #                csv_file.write(";" + str(data[j][i]))
        #            csv_file.write(os.linesep)
        #        sample += len(data[0])
        #
        # data:
        #    ----------------------->
        # C1| 1 2 3 4 5 6 7 
        # C2| 2 5 9 8 8 2
        #   v 
        #
        #
        #
        #

        #    print()
        #    print("Data written to: " + csv_file.name)
        #finally:
        #    csv_file.close()
        scp.stop()
        print("Stopped scp ", flush=True)
        gen.stop()
        print("Stopped gen ", flush=True)
    except Exception as e:
        print("Exception: " + str(e))
        print(sys.exc_info()[0], flush=True)
        #print("Exception: " + e.message)
        sys.exit(1)

    del scp
    del gen

else:
    print("No device avaible for measurement")
    sys.exit(1)
sys.exit(0)
