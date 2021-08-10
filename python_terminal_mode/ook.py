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


class OOK:
    """
        TODO Some errors here still use OOKSimpleExp
    """
    _count = 0
    def __init__(self, Ts=30e-03, fs=44000, fc=1800, Nbits=10, generate=True):
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
        self.generate = generate
        self.baud = 1/self.Ts
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.t = np.r_[0.0 : self.N] / self.fs

        if generate:
            self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")
            self.M = np.tile(self.bits, (1, self.Ns ))

    def encode(self, bits):
        """ modulation scheme 
        bits: bit array to encode does not overwrite the internal bit array i.e. you have to save signal/bits uses parameters of the class
        returns the signal/data
        """

        temp = None
        if not self.generate:
            assert(len(bits) == self.Nbits)
            temp = self.M
            self.M = np.tile(bits, (1, self.Ns ))
        self.signal = np.zeros(self.N)
        self.signal = self.M.ravel() * np.sin(2 * np.pi * self.fc * self.t)
        if np.all(temp) != None:
            self.M = temp
        return self.signal

    def _testing_encode(self, bits):
        assert(len(bits) == self.Nbits)
        self.bits = bits
        self.M = np.tile(bits, (1, self.Ns))
        self.signal = np.zeros(self.N)
        self.signal = self.M.ravel() * np.sin(2 * np.pi * self.fc * self.t)
        return self.signal


    def decode(self, signal=None):
        """ demodulation scheme 
        signal: a user provided signal to decode does not overwrite the internal signal perhaps uses paramter of the class
        returns the transmitted bits
        """
        temp = None
        if np.all(signal) != None:
            assert(signal.shape == self.signal.shape)
            temp = self.signal
            self.signal = signal
            print("swaped self.signal and signal")
        Ns = self.Ns
        result = []
        count_peaks = self.Ts * self.fc
        print(count_peaks)
        for i in range( self.Nbits ):
            idx, _ = find_peaks(self.signal[i * Ns : (i+1) * Ns])
            print(len(idx), end="\t")
            result.append( int( np.abs( len(idx) - count_peaks) < 1))
        print("")

        if np.all( result == self.bits.flatten() ):
            self._count += 1
        print("in: ", self.bits.flatten())
        print("out: ", np.array(result))
        print("in == out", np.all(result == self.bits.flatten()), "hits:", self._count)
        if np.all(signal) != None and np.all(temp) != None:
            self.signal = temp
        return result

    def plot(self, axis=None):
        """ plotting the encoded(?) signal"""
        if axis != None:
            axis.plot(self.t, self.signal)
            axis.set_xlabel("t [s]")
            axis.set_title("".join([str(b) for b in self.bits]))
            for idx, bit in enumerate(self.bits):
                axis.vlines(idx * self.Ts, -1.1, 1.1, "r")
        else:
            plt.plot(self.t, self.signal)
            plt.xlabel("t [s]")
            plt.title("".join([str(b) for b in self.bits]))
            for idx, bit in enumerate(self.bits):
                plt.vlines(idx * self.Ts, -1.1, 1.1, "r")

    def plot_encode(self, signal, bits):
        """
        plots a signal assumes its enconded with a symbol duration of self.Ts and user provided bits.
        assumes the same parameters as the internal signal
        """
        assert(signal != None and bits != None)
        plt.plot(self.t, signal)
        plt.xlabel("t [s]")
        plt.title("".join([str(b) for b in bits]))
        for idx, bit in enumerate(self.bits):
            plt.vlines(idx * self.Ts, -1.1, 1.1, "r")

    def error_estimate(self):
        pass

class OOKSimpleExp(OOK):
    def _ampl(self, x, t, s=1.0): 
        """
        t: offset
        s: width of exp needs to be roughly bit duration...
        """
        return np.exp(- 0.5 * (x - t) **2 / s**2)
    def encode(self, bits=None):
        """
        bits: bit array to encode user is expected to save the return value since the bit array is not saved
        returns: signal
        """
        temp2 = None
        temp3 = None
        if np.all(bits) != None:
            temp2 = self.M
            temp3 = self.bits
            self.M = np.tile(bits, (1, self.Ns ))
            self.bits = bits

        temp = np.zeros(self.N)
        for i, b in enumerate(self.bits):
            temp += b * self._ampl(self.t, (i + 0.5) * self.Ts, self.Ts / 10)
        self.signal = self.M.ravel() * temp * np.sin(2 * np.pi * self.fc * self.t)

        if np.all(bits != None) and np.all(temp2 != None) and np.all(temp3 != None):
            self.M = temp2
            self.bits = temp3
        return self.signal

    def _testing_encode(self, bits):

        self.bits = bits
        self.M = np.tile(bits, (1, self.Ns ))
        temp = np.zeros(self.N)
        for i, b in enumerate(self.bits):
            temp += b * self._ampl(self.t, (i + 0.5) * self.Ts, self.Ts / 10)
        self.signal = self.M.ravel() * temp * np.sin(2 * np.pi * self.fc * self.t)
        plt.plot(self.t, temp, "g--")
        return self.signal

    def decode(self, signal=None):
        """
        signal: signal to encode not saved
        returns: the decoded bit array
        """
        temp = None
        if np.all(signal) != None:
            assert(signal.shape == self.signal.shape)
            temp = self.signal
            self.signal = signal
            print("swaped self.signal and signal")
        Ns = self.Ns
        result = []
        for i in range( self.Nbits ):
            idx, _ = find_peaks(self.signal[i * Ns : (i+1) * Ns], height=np.max(self.signal) / 4)
            if len(idx) > 1:
                result.append( 1)
            else:
                result.append(0)

        if np.all( result == self.bits.flatten() ):
            self._count += 1
        print("in: ", self.bits.flatten(), "out: ", np.array(result), "in == out", np.all(result == self.bits.flatten()), "hits:", self._count)
        if np.all(signal) != None and np.all(temp) != None:
            self.signal = temp
        return result

    def plot(self, signal=None, bits=None):
        """
        plots the encoded message uses signal and bits if provided
        """
        temp1 = None
        temp2 = None
        if np.all(signal != None) and np.all(bits != None):
            assert(self.signal.shape == signal.shape and bits.shape == bits.shaoe)
            temp1, temp2 = self.signal, self.bits
            self.signal, self.bits = signal, bits
        temp = np.zeros(self.N)
        for i, b in enumerate(self.bits):
            temp += b * self._ampl(self.t, (i + 0.5) * self.Ts, self.Ts / 10)
        plt.plot(self.t, temp, "g--")
        plt.plot(self.t, self.signal)
        plt.xlabel("t [s]")
        plt.title("".join([str(b) for b in self.bits]))
        for idx, bit in enumerate(self.bits):
            plt.vlines(idx * self.Ts, -1.1, 1.1, "r")
        if np.all(signal != None) and np.all(bits != None) and np.all(temp1 != None) and np.all(temp2 != None):
            self.signal, self.bits = temp1, temp2
        plt.show()

    def plot_spectrum(self, signal=None):
        temp = None
        if np.all(signal != None):
            assert(self.signal.shape == signal.shape)
            temp1= self.signal
            self.signal = signal

        f = np.r_[0: self.N/2.0] / self.N * self.fs
        s = fft.fft(self.signal)
        plt.plot(f, np.abs(s[:len(s) //2]))
        if np.all(signal != None) and np.all(temp != None):
            self.signal = temp
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
    plot_class(OOKSimpleExp)
    plt.show()

