import numpy as np
import matplotlib.pyplot as plt
Nbits = 5
bits = np.array(np.random.rand(Nbits) > 0.5, dtype=int)
#bits = np.array([1, 1, 1, 1, 1])
fc = 10e+3 #carrier
df = 500
fre = []
lower_fre = fc - len(bits) * df
for i in range(len(bits)):
	f = lower_fre + i * 2 * df
	fre.append(f)

A = 10
data = np.zeros(8192)
N = 8192 # final data size...
fs = 25e+3 #best choose this atleast x2.3 highest fre
T = 1/ fs #sample spacing?
x = np.linspace(0.0, N*T, N) # time
print(bits, flush=True)
for i in range(Nbits):
    data = data + bits[i] * A * np.sin(2*np.pi * fre[i] * x)
    print("freq: {}".format(fre[i]))

#xf = np.linspace(0.0, 1.0/(2.0 * T), N)



#aook
#naive 
#dx = x[1] - x[0]
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert
from scipy.signal import find_peaks
y = np.loadtxt("data.dat") #TODO load the data here for OOK
idx, _ = find_peaks(y, height=0.5)
plt.plot(x, y)
plt.plot(x[idx], y[idx])
plt.show()
#TODO create a pulse and do it with hilbert to find the env



#demodulation
#fdm
import numpy as np
import matplotlib.pyplot as plt
import scipy.fft as fft
from scipy.signal import find_peaks
# need the xdata to be uniformly distributed => equal spacing
# fft spectrum will always be symmetric thus you need to somehow splice it
freq = fft.fftfreq(len(x), x[1] - x[0])
spectrum = fft.fft(data)
idx, _ = find_peaks(np.abs(spectrum))
print("peaks idx: ", idx)
print("peaks half idx: ", idx[len(idx)//2:])
#only interested in positve freq otherwise wrong order
freq_peak = np.abs(freq[idx[len(idx)//2:]])
print("peaks freq idx: ", freq_peak)
#reconstruct
TOLARANZ = 4
received = []
freq_peak = list(freq_peak)

for i, f in enumerate(fre):
    if len(freq_peak) > 0:
        print("Difference: ", np.abs(f-freq_peak[-1]))
        if np.abs(f - freq_peak[-1]) < TOLARANZ:
            print("bit found")
            received.append(1)
            freq_peak.pop()
            continue
    received.append(0)
print(received)
        
plt.plot(freq, np.abs(spectrum))
plt.plot(freq[idx], np.abs(spectrum)[idx], "ro")
plt.show()


