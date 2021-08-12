import sys # for exit
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert
from scipy.signal import square
from scipy.signal import find_peaks
from scipy.fft import fft

mode = "square-simple"  #TODO uses class don't be lazy
mode = "pulse-simple"

#generate data
N = 8194
number_bits = 4
bits = [ 1 if np.random.rand() > 0.5 else 0 for i in range(number_bits)]
#bits = [1, 0, 1, 1]
Nbit = N // len(bits)
Amp = 5
fc = 5
t = np.linspace(0, N, N)

y = np.zeros(N)

if mode == "square-simple":
    for k, bit in enumerate(bits):
        y[k * Nbit: (k+1) * Nbit] = Amp * bit 
elif mode == "pulse-simple":



#demod 
if mode == "square-simple":
    y = y  #dummy use np.loadtxt("path-to-file.txt") in prod
    result = []
    for k, bit in enumerate(bits):
        temp = np.average( y[k * Nbit: (k+1) * Nbit]) 
        if temp > Amp / 4: #random threshhold
            result.append(1)
        else:
            result.append(0)
    print(bits)
    print(result)



sys.exit()
plt.plot(t, y)
plt.title("".join([str(b) for b in bits]))
plt.show()

