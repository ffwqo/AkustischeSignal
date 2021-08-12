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


class FDM:
    def __init__(self, Ts=30e-03, fs=44000, fc=1800, df = 100, Nbits=10, generate=True):
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
        self.generate = generate

        if generate:
            self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")

    def encode(self, bits=None):
        temp = None
        if bits is not None:
            assert(len(bits) == self.Nbits)
            temp = self.bits
            self.bits = bits
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
        if signal is not None:
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
        if signal is not None and temp is not None:
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

################
## FDM SIMPLE ##
################

class FDMSimple:

    def __init__(self, Ts=30e-03, fs=44000, fc=1800, df = 100, Nbits=10, generate=True):
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
        self.generate = generate

        if generate:
            self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")

    def encode(self, bits=None):
        temp = None
        if bits is not None:
            temp = self.bits
            assert(len(bits) == self.Nbits)
            self.bits = bits
        self.signal = np.zeros(self.N)
        for idx, bit in enumerate(self.bits):
            self.signal += bit * np.sin(2 * np.pi * self.t * (self.lower + idx * self.df))

        if bits is not None and temp is not None:
            self.bits = temp
        return self.signal

    def _testing_encode(self, bits):
        if bits is not None:
            assert(len(bits) == self.Nbits)
            self.bits = bits
        self.signal = np.zeros(self.N)
        for idx, bit in enumerate(self.bits):
            self.signal += bit * np.sin(2 * np.pi * self.t * (self.lower + idx * self.df))
        return self.signal

    def decode(self, testing=False, signal=None, bits=None):
        temp1 = None
        temp2 = None
        if bits is not None and signal is not None:
            assert(len(bits) == len(self.bits))
            assert(len(signal) == len(self.signal))
            temp1, temp2 = self.signal, self.bits
            self.signal, self.bits = signal, bits

        Ns = self.Ns
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
        #comment this out for testing
        #print("in: ", self.bits.flatten())
        #print("out:", np.array(result))
        #print("in == out", np.all(result == self.bits.flatten()))
        if testing :
            assert(np.all(result == self.bits.flatten()))
        if bits is not None and signal is not None and temp1 is not None and temp2 is not None:
            self.signal, self.bits = temp1, temp2
        return result

    def plot(self, signal=None, bits=None):
        temp1 = None
        temp2 = None
        if bits is not None and signal is not None:
            assert(len(bits) == len(self.bits))
            assert(len(signal) == len(self.signal))
            temp1, temp2 = self.signal, self.bits
            self.signal, self.bits = signal, bits
        assert( np.all(self.signal != None))
        s = np.abs(fft.fft(self.signal))
        idx , _ = find_peaks(s, height=np.max(s)/ 10.0)
        idx = idx[:len(idx) // 2] #only the postive part
        freq = fft.fftfreq(len(s), self.t[1] - self.t[0])
        freq = freq[:len(s) // 2]
        s = s[:len(s) // 2]
        plt.plot(freq, s)
        plt.title("".join([str(b) for b in self.bits]))
        for idx, bit in enumerate(self.bits):
            plt.vlines(self.lower + idx * self.df, np.max(s) * -0.01 , np.max(s) * 1.1, "r", linestyle="dashed")
        plt.xlim([self.lower - self.df * 5, self.upper + self.df * 5])
        plt.show()
        if bits is not None and signal is not None and temp1 is not None and temp2 is not None:
            self.signal, self.bits = temp1, temp2

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

def fdm_decode(signal, t, lower, df, Nbits, testing=False, bits=None):
    result = []
    s = np.abs(fft.fft(signal))
    idx , _ = find_peaks(s, height=np.max(s)/ 10.0)
    idx = idx[:len(idx) // 2] #only the postive part
    freq = fft.fftfreq(len(s), t[1] - t[0])
    freq = freq[:len(s) // 2]

    EPSILON = 10
    idx = list(idx)
    idx.reverse()

    for i in range( Nbits ):
        if len(idx) < 1:
            result.append(0)
            continue
        f = lower + df * i
        if np.abs(freq[idx[-1]] - f) < EPSILON :
            result.append(1)
            idx.pop()
        else:
            result.append(0)
    if testing and np.all(bits) != None:
        assert(np.all(result == bits.flatten()))
    return result

if __name__ == "__main__":
    test_class(FDMSimple)
    pass

