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
import matplotlib.pyplot as plt
import time 
import os
import sys
from array import array
import libtiepie
#from printinfo import * 
import numpy as np

from ook import OOKSimpleExp
from fdm import FDMSimple
from ofdm import OFDM


#ook
#Ts=30e-03
#fs=20000
#fc=1800
#Nbits=10
#device = OOKSimpleExp(Ts, fs, fc, Nbits)
#device_header = f"device: Ts: {Ts} fs: {fs} fc: {fc} Nbits: {Nbits}\n"
#bits = device.generate()
#bits[0] = 0
#signal = device.encode(bits)
#print(signal.shape)
#device.plot(signal, bits, show=False)


#fdm
Ts=30e-03
fs=44000
fc=1800
df = 100
Nbits=10
device = FDMSimple(Ts, fs, fc, df, Nbits)
device_header = f"Ts: {Ts} fs: {fs} fc: {fc} df: {df} Nbits: {Nbits}"
bits = device.generate()
signal = device.encode(bits)
##device.plot(signal, bits, show=False)

#ofdm
#802.11a standard 312.5kHz carrier seperation BW 20MHz OBW 16.6 MHz
#Nsubcarrier = 64
#Npilot = 8
#pilot_amp = 3+3j
#Nbits = 220 #should be k * 220 , k = 1,2,3,4,...
#device = OFDM(Nsubcarrier, Npilot, pilot_amp)
#bits = device.generate(Nbits)
#signal = device.encode(bits)
#device_header = f"Nsubcarrier: {Nsubcarrier} Npilot: {Npilot} pilot_amp: {pilot_amp} Nbits: {Nbits}"
##device.plot(signal, bits, show=False) #not implemented yet

print(signal.shape)



TEST_RUNS = 10
N = 20000
scp_fs = 20e3
scp_record_length = 20000 #len(data)
gen_fs = 20e3
gen_amp = 8
gen_offset = 0
data = array("f", signal)


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

if os.path.isdir("./messdaten"):
    filename="messdaten/measure_data_block"
else:
    filename="measure_data_block"

i = 0
while os.path.isfile(filename):
    if os.path.isdir("./messdaten"):
        filename=f"messdaten/measure_data_block_{i}"
    else:
        filename=f"measure_data_block_{i}"
    i += 1
if not os.path.isdir("./messdaten/testrun"):
    os.mkdir("./messdaten/testrun")
    filename = f"measure_data_block"
else:
    while(os.path.isfile(f"./messdaten/{filename}")):
        filename = f"measure_data_block_{i}"
        i += 1

print(filename)
header = f"bits: {list(bits.flatten())}\n"
header += f"N: {N} scp_fs: {scp_fs } scp_rl: {scp_record_length } gen_fs: {gen_fs } gen_amp: {gen_amp } gen_offset: {gen_offset }\n"
header += f"{device}\n"
header += device_header
header += f"{time.asctime()}\n"

#ook
Ts=30e-03
fs=44000
fc=1800
Nbits=10


if scp and gen:
    try:

        scp.measure_mode = libtiepie.MM_BLOCK
        scp.sample_frequency = scp_fs
        scp.record_length = scp_record_length
        for ch in scp.channels:
            ch.enabled = True
            ch.range = 8
            ch.coupling = libtiepie.CK_DCV

        gen.signal_type = libtiepie.ST_ARBITRARY
        gen.frequency_mode = libtiepie.FM_SAMPLEFREQUENCY
        gen.frequency = gen_fs
        gen.amplitude = gen_amp
        gen.offset = gen_offset
        gen.output_on = True 

        
        test_result = []
        signal_list = []
        bits_list = []
        scp.start()
        print("scp started!")
        for i in range(TEST_RUNS):
            signal_list.append(data)
            bits_list.append(bits)
            gen.set_data(data)
            print("Set data")
            scp.get_data() # hack to clear buffer
            gen.start()
            print("gen started")

            while not (scp.is_data_ready or scp.is_data_overflow):
                time.sleep(0.01)
            if scp.is_data_overflow:
                print("Data overflow")
                #TODO something eror
            data = scp.get_data()
            data = np.array(data)
            test_result.append(data)
            print(data.shape)


            header += f"Run#{i}\n"
            for i in range(len(scp.channels)):
                header += f"Ch{i+1}\t" 
            result = data.transpose()
            if( TEST_RUNS > 1):
                np.savetxt(filename +f"_testrun_{i}.txt", result, header=header)
                print("Written file!", flush=True)
            else:
                np.savetxt(filename+ ".txt", result, header=header)
                print("Written file!", flush=True)

            gen.stop()
            print("Stopped gen ", flush=True)
            bits = device.generate(Nbits)
            signal = device.encode(bits)
            data = array("f", signal)
        np.savetxt(filename + "_testrun_all.txt", np.array(test_result), header=header)
        scp.stop()
        
        print("Stopped scp ", flush=True)
    except Exception as e:
        print("Exception: " + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

        print(sys.exc_info()[0], flush=True)
        #sys.exit(1)

    del scp
    del gen
    i = 0
    for result, signal, bits in zip(test_result, signal_list, bits_list):
        print(f"#run {i}")
        i += 1
        signal_scp = result[:, 1]
        signal_gen = result[:, 0]
        print(f"scp_shape: {signal_scp.shape}, gen_shape: {signal_gen.shape}")
        bits_decode = device.decode(signal_scp, bits)
        print("bits in: ", bits.flatten())
        print("bits decode: ", bits_decode)
        #device.plot(signal_scp[:len(signal)], bits, title="Ch2 Signal")
        #plt.show()
        #device.plot(signal_gen[:len(signal)], bits, title="Ch1 Signal")
        #plt.show()


else:
    print("No device avaible for measurement")
    sys.exit(1)


