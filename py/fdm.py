import sys # for exit
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert
from scipy.signal import square
from scipy.signal import find_peaks
import scipy.fft as fft

mode = "simple"  #TODO use class don't be lazy

#generate data
N = 1024
fs = 25e+3 #best choose this atleast x2.3 highest fre
ts = 1 / fs
number_bits = 4
bits = [ 1 if np.random.rand() > 0.5 else 0 for i in range(number_bits)]
#bits = [1, 0, 1, 1]
Nbit = N // len(bits)
Amp = 5
fc = 10e3
df = 1e3 
t = np.linspace(0, N * ts , N)
lower = fc - df * number_bits // 2
flist = [lower + df * k for k in range(len(bits))]

y = np.zeros(N)

if mode == "simple":

    for k, bit in enumerate(bits):
        y += Amp * bit * np.sin(2 * np.pi * t * (lower + df * k))


#fre = fft.fftfreq(len(y), t[1] - t[0])
#s = np.abs(fft.fft(y))
#plt.plot(fre, s)
#plt.plot(flist, [np.max(s) // 2 for _ in range(len(flist))], "ro")
#plt.title("".join([str(i) for i in bits]))
#plt.show()




if mode == "simple":
    y = y  #dummy use np.loadtxt("path-to-file.txt") in prod
    result = []
    spectrum = np.abs(fft.fft(y))
    freq = fft.fftfreq(len(spectrum), t[1] - t[0])
    idx, prop = find_peaks(spectrum)
    index = idx.copy()
    idx = list(idx[: len(idx)//2]) #fftfreq returns something symmetric
    #we need to know the frequency spacing from the transmitter in the receiver 
    idx.reverse()
    epsilon = 1 #some margin
    for f in flist:
        if len(idx) > 0:
            print(freq[idx[-1]])
        if len(idx) < 1:
            result.append(0)
            continue
        if np.abs(f - freq[idx[-1]]) < epsilon:
            result.append(1)
            idx.pop()
        else:
            result.append(0)

    plt.plot(freq, spectrum)
    plt.plot(freq[index], spectrum[index] // 2, "ro")
    plt.title("in: {} result: {}".format(str(bits), str(result)))
    plt.show()


