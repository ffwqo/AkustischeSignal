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


QAM16 = { 2: -2+2j, 6: -1+2j, 14: 1+2j, 10: 2+2j,
        3: -2+1j, 7: -1-1j, 15: 1+1j, 11: 2+1j,
        1: -2-1j, 5: -1-1j, 13: 1-1j, 9: 2-1j,
        0: -2-2j, 4: -1-2j, 12: 1-2j, 8: 2-2j}


class OFDM:
    def __init__(self, Ts=30e-03, fs=44000, fc=1800, df = 100, Nbits=10, generate=True):
        """
        Ts: symbol duration
        fs: sampling rate
        fc: carrier freq
        Nbits: number of bits per encode pass
        generate: whether to genrate a bit array for use in encode, decode otherwise provide one in encode
        """

        self.Ts = Ts
        self.Nbits = Nbits
        self.fs = fs
        self.fc = fc
        self.baud = 1/self.Ts
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.t = np.r_[0.0 : self.N] / self.fs
        self.generate = generate

        if generate:
            self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")

    def encode(self, bits=None):
        """
        bits = [1,1,1,0,0,0,0]
        right padding => [0,1,1,1,0,0,0,0]
        """
        temp = None
        if bits is not None:
            assert(len(bits) == self.Nbits)
            temp = self.bits 
            self.bits = bits

        assert(len(bits) <= 4 * 42) #40 data carriers
        pad = len(bits) % 4
        internal = np.r_ [ [0 for _ in range(pad)], bits] #padded array
        chunks = np.split(internal, len(internal) % 4)
        chunks = [ int( "".join([str(i) for i in chunk]), 2) for chunk in chunks]
        mapped_bits = [ QAM16[i] for i in chunks]

        self.signal = np.zeros(self.N)
        for idx, bit in enumerate(self.bits):
            self.signal += bit * np.sin(2 * np.pi * self.t * (self.lower + idx * self.df))
        if bits is not None and temp is not None:
            self.bits = temp
        return self.signal

    def decode(self, signal=None, testing=False):
        """
        signal: signal to decode make sure its the signal we generated from encode...
                assuming same t is being used otherwise someone has to fix the spacing
                does not save the modified state i.e. you need to save the result
        returns: the decoded bits
        """
        temp = None
        if np.all(signal) != None:
            print("using user provided signal")
            assert( signal.shape == self.signal.shape)
            temp = self.signal.copy()
            self.signal = signal

        result = []
        s = np.abs(fft.fft(self.signal))
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
        if testing:
            assert(np.all(result == self.bits.flatten()))
        if np.all(signal) != None and np.all(temp) != None:
            self.signal = temp
        return result


    def plot(self, axis=None):
        assert( np.all(self.signal != None))
        s = np.abs(fft.fft(self.signal))
        idx , _ = find_peaks(s, height=np.max(s)/ 10.0)
        idx = idx[:len(idx) // 2] #only the postive part
        freq = fft.fftfreq(len(s), self.t[1] - self.t[0])
        freq = freq[:len(s) // 2]
        s = s[:len(s) // 2]

        if axis != None:
            axis.plot(freq, s)
            axis.set_xlabel("f [Hz]")
            axis.set_title("".join([str(b) for b in self.bits]))
            for idx, bit in enumerate(self.bits):
                axis.vlines(self.lower + idx * self.df, np.max(s) * -0.01 , np.max(s) * 1.1, "r", linestyle="dashed")
            axis.set_xlim([self.lower - self.df * 5, self.upper + self.df * 5])
        else:
            plt.plot(freq, s)
            plt.title("".join([str(b) for b in self.bits]))
            for idx, bit in enumerate(self.bits):
                plt.vlines(self.lower + idx * self.df, np.max(s) * -0.01 , np.max(s) * 1.1, "r", linestyle="dashed")
            plt.xlim([self.lower - self.df * 5, self.upper + self.df * 5])
            plt.show()

    def error_estimate(self):
        pass


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
    ex.encode()
    ex.decode()
    ex.plot()

if __name__ == "__main__":
    test_class(OFDM)
    pass

