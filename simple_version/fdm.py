"""
use in main via 

``` python
from <filename> import *
```

adapted from https://inst.eecs.berkeley.edu/~ee123/sp15/lab/lab6/Pre-Lab6-Intro-to-Digital-Communications.html
https://www.cwnp.com/understanding-ofdm-part-2-2/ for baud rate

"""

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
from scipy.signal import find_peaks
import scipy.fft as fft
import itertools #for bit combintatio testing



################
## FDM SIMPLE ##
################

class FDMSimple:

    def __init__(self, Ts=30e-03, fs=44000, fc=1800, df = 100, Nbits=10):
        """
        Ts: symbol duration
        fs: sampling rate
        fc: carrier freq
        df: offset freq
        Nbits: number of bits per encode pass
        generate: whether to genrate a bit array for use in encode, decode otherwise provide one in encode
        """

        self.Ts = Ts
        self.Nbits = Nbits
        self.fs = fs
        self.fc = fc
        self.df = df
        self.baud = 1/self.Ts
        self.lower = self.fc - self.Nbits // 2 * self.df
        self.upper = self.fc + self.Nbits // 2 * self.df
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.t = np.r_[0.0 : self.N] / self.fs

    def generate(self):
        return (np.random.rand(self.Nbits, 1) > 0.5).astype("int")

    def encode(self, bits):
        signal = np.zeros(self.N)
        for idx, bit in enumerate(bits):
            signal += bit * np.sin(2 * np.pi * self.t * (self.lower + idx * self.df))
        return signal

    def _testing_encode(self, bits):
        signal = np.zeros(self.N)
        for idx, bit in enumerate(bits):
            signal += bit * np.sin(2 * np.pi * self.t * (self.lower + idx * self.df))
        return signal

    def decode(self, signal, bits, testing=False):

        Ns = self.Ns
        result = []
        s = np.abs(fft.fft(signal))
        idx , _ = find_peaks(s, height=np.max(s)/ 10.0)
        idx = idx[:len(idx) // 2] #only the postive part
        freq = fft.fftfreq(len(s), self.t[1] - self.t[0])
        freq = freq[:len(s) // 2]

        EPSILON = 10
        idx = list(idx)
        idx.reverse()

        for i in range( self.Nbits ):
            if len(idx) < 1:
                result.append(0)
                continue
            f = self.lower + self.df * i
            if np.abs(freq[idx[-1]] - f) < EPSILON :
                result.append(1)
                idx.pop()
            else:
                result.append(0)
        #comment this out for testing
        #print("in: ", self.bits.flatten())
        #print("out:", np.array(result))
        #print("in == out", np.all(result == self.bits.flatten()))
        if testing :
            assert(np.all(result == bits.flatten()))
        return result

    def plot(self, signal, bits, show=False, title=""):
        s = np.abs(fft.fft(signal))
        idx , _ = find_peaks(s, height=np.max(s)/ 10.0)
        idx = idx[:len(idx) // 2] #only the postive part
        freq = fft.fftfreq(len(s), self.t[1] - self.t[0])
        freq = freq[:len(s) // 2]
        s = s[:len(s) // 2]
        plt.plot(freq, s)
        plt.title(title + "\nFrequenzspektrum bits input: " + "".join([str(b) for b in bits.flatten()]))
        plt.xlabel("f [Hz]")
        for idx, bit in enumerate(bits):
            plt.vlines(self.lower + idx * self.df, np.max(s) * -0.01 , np.max(s) * 1.1, "r", linestyle="dashed")
        plt.xlim([self.lower - self.df * 5, self.upper + self.df * 5])
        if show:
            plt.show()

def test_class(obj, Nbits=10):
    print("Starting test...")
    blist = list(itertools.product([0, 1], repeat=Nbits))
    blist = np.array(blist)
    ex = obj()
    for bits in blist:
        ex._testing_encode(bits)
        ex.decode(testing=True)
    print("passed. All clear.")

def plot_class(obj):
    ex = obj()
    bits = ex.generate()
    signal = ex.encode(bits)
    ex.decode(signal, bits)
    ex.plot(signal, bits)


if __name__ == "__main__":

    plot_class(FDMSimple)
    pass

