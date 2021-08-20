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
import itertools

class OOKSimpleExp():
    _count = 0

    def __init__(self, Ts=30e-03, fs=44000, fc=1800, Nbits=10, thres=25):
        """
        Ts: symbol duration
        fs: sampling rate
        fc: carrier freq
        Nbits: number of bits per encode pass
        generate: whether to genrate a bit array for use in encode, decode
        """

        self.Ts = Ts
        self.Nbits = Nbits
        self.fs = fs
        self.fc = fc
        self.thres = thres
        self.baud = 1/self.Ts
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.t = np.r_[0.0 : self.N] / self.fs

    def generate(self):
        """generates random bits and tiling M"""
        bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")
        M = np.tile(bits, (1, self.Ns ))
        return bits
        

    def _ampl(self, x, t, s=1.0): 
        """
        t: offset
        s: width of exp needs to be roughly bit duration...
        """
        return np.exp(- 0.5 * (x - t) **2 / s**2)
    def encode(self, bits):
        print(self.fs)
        """
        bits: bit array of size Nbit
        returns: signal
        """
        assert(len(bits) == self.Nbits)
        M = np.tile(bits, (1, self.Ns ))
        signal = M.ravel() * np.sin(2 * np.pi * self.fc * self.t)
        return signal

        #temp = np.zeros(self.N)
        #for i, b in enumerate(bits):
        #    temp += b * self._ampl(self.t, (i + 0.5) * self.Ts, self.Ts / 10)
        #signal = M.ravel() * temp * np.sin(2 * np.pi * self.fc * self.t)
        #return signal

    def _testing_encode(self, bits):
        assert(len(bits) == self.Nbits)
        M = np.tile(bits, (1, self.Ns ))
        temp = np.zeros(self.N)
        for i, b in enumerate(bits):
            temp += b * self._ampl(self.t, (i + 0.5) * self.Ts, self.Ts / 10)
        signal = M.ravel() * temp * np.sin(2 * np.pi * self.fc * self.t)
        plt.plot(self.t, temp, "g--")
        return signal

    def decode(self, signal, bits):
        """
        signal: signal to encode not saved
        returns: the decoded bit array
        """
        Ns = self.Ns
        result = []
        for i in range( self.Nbits ):
            tseg = self.t[i*self.Ns:(i+1)*self.Ns]
            sseg = signal[i*self.Ns:(i+1)*self.Ns]
            x = pow(sum(np.sin(2 * np.pi * self.fc * tseg) * sseg), 2)+pow(sum(np.cos(2 * np.pi * self.fc * tseg) * sseg), 2)
            print(x)
            if x > self.thres:
                result.append(1)
            else:
                result.append(0)

        if np.all( result == bits.flatten() ):
            self._count += 1
        print("in: ", bits.flatten(), "out: ", np.array(result), "in == out", np.all(result == bits.flatten()), "hits:", self._count)
        return result

    def plot(self, signal, bits, show=False, title=""):
        """
        plots the encoded message uses signal and bits if provided
        """
        temp = np.zeros(self.N)
        for i, b in enumerate(bits):
            temp += b * self._ampl(self.t, (i + 0.5) * self.Ts, self.Ts / 10)
        plt.plot(self.t, temp, "g--")
        plt.plot(self.t, signal)
        plt.xlabel("t [s]")
        plt.title(title)#+"\nbits input: "+ "".join([str(b) for b in bits.flatten()])
        for idx, bit in enumerate(bits):
            plt.vlines(idx * self.Ts, -1.1, 1.1, "r")
        if show:
            plt.show()

    def plot_spectrum(self, signal, show=False):
        temp = None

        f = np.r_[0: self.N/2.0] / self.N * self.fs
        s = fft.fft(signal)
        plt.plot(f, np.abs(s[:len(s) //2]))
        if show:
            plt.show()


def test_class(obj, Nbits=10):
    """
    Special Case [0, 0, ..., 0, 0, 1] does not work..
    """
    blist = list(itertools.product([0, 1], repeat=Nbits))
    blist = np.array(blist)
    ex = obj()
    for bits in blist:
        ex._testing_encode(bits)
        ex.decode()
def plot_class(obj):
    ex = obj()
    ex.encode()
    ex.decode()
    ex.plot()

if __name__ == "__main__":
    ook = OOKSimpleExp()
    bits = ook.generate()
    signal = ook.encode(bits)
    result = ook.decode(signal, bits)
    ook.plot(signal, bits)
    plt.show()

