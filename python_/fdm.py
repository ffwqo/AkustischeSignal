"""
use in main via 

``` python
from <filename> import *
```

from https://inst.eecs.berkeley.edu/~ee123/sp15/lab/lab6/Pre-Lab6-Intro-to-Digital-Communications.html
https://www.cwnp.com/understanding-ofdm-part-2-2/ for baud rate

"""

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
from scipy.signal import find_peaks


class _PrivateMethod:
    """ private class will not be imported by default """
    def __init__(self):
        pass
class Method:
    def __init__(self):
        self.fs = None
        self.N = None
        self.t = None
        self.signal = None
        print("Hi form method")
        pass
    def encode(self):
        """ modulation scheme """
        pass
    def decode(self):
        """ demodulation scheme """
        pass
    def plot(self):
        """ plotting the encoded(?) signal"""
        pass
    def error_estimate(self):
        pass

class OOK:
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
        self.baud = 1/self.Ts
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.t = np.r_[0.0 : self.N] / self.fs
        self.generate = generate

        if generate:
            self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")
            self.M = np.tile(self.bits, (1, self.Ns ))

    def encode(self, bits):
        """ modulation scheme 
        bits: bit array to pay per encode
        returns the signal/data
        """

        if not self.generate:
            assert(len(bits) == self.Nbits)
            self.M = np.tile(bits, (1, self.Ns ))
        self.signal = np.zeros(self.N)
        self.signal = self.M.ravel() * np.sin(2 * np.pi * self.fc * self.t)
        return self.signal

    def decode(self):
        """ demodulation scheme 
        returns the transmitted bits
        """
        Ns = self.Ns
        result = []
        count_peaks = self.Ts / (1/self.fc)
        for i in range( self.Nbits ):
            idx, _ = find_peaks(self.signal[i * Ns : (i+1) * Ns])
            result.append( int( np.abs( len(idx) - count_peaks) < 1))

        print("in: ", self.bits.flatten())
        print("out: ", np.array(result))
        print("in == out", np.all(result == self.bits.flatten()))
        return result

    def plot(self):
        """ plotting the encoded(?) signal"""
        plt.plot(self.t, self.signal)
        plt.xlabel("t [s]")
        plt.title("".join([str(b) for b in self.bits]))
        for idx, bit in enumerate(self.bits):
            plt.vlines(idx * self.Ts, -1.1, 1.1, "r")
        plt.show()

    def error_estimate(self):
        pass

class _Simple:

    def __init__(self):
        self.Ts = 33e-03
        self.Nbits = 10
        self.fs = 44000
        self.fc = 1800
        self.baud = 1/self.Ts
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")
        #self.bits = np.array([ 0 for _ in range(self.Nbits)])
        #self.bits[-1] = 1 #TODO work on this case
        #self.bits.reshape(self.Nbits, 1)
        self.M = np.tile(self.bits, (1, self.Ns ))
        self.t = np.r_[0.0 : self.N] / self.fs

    def encode(self):
        self.signal = np.zeros(self.N)
        self.signal = self.M.ravel() * np.sin(2 * np.pi * self.fc * self.t)
        return self.signal
    def decode(self):
        Ns = self.Ns
        result = []
        count_peaks = self.Ts / (1/self.fc)
        for i in range( self.Nbits ):
            idx, _ = find_peaks(self.signal[i * Ns : (i+1) * Ns])
            result.append( int( np.abs( len(idx) - count_peaks) < 1))

        print("in: ", self.bits.flatten())
        print("out:", np.array(result))
        print("in == out", np.all(result == self.bits.flatten()))
        #assert(np.all(result == self.bits.flatten()))
        return result
    def plot(self):
        assert( np.all(self.signal != None))
        plt.plot(self.t, self.signal)
        plt.xlabel("t [s]")
        plt.title("".join([str(b) for b in self.bits]))
        for idx, bit in enumerate(self.bits):
            plt.vlines(idx * self.Ts, -1.1, 1.1, "r")
        plt.show()

def test_class(obj):
    """
    Special Case [0, 0, ..., 0, 0, 1] does not work..
    """
    for _ in range(100):
        ex = obj()
        ex.encode()
        ex.decode()

class _SimpleExp(_Simple):
    def encode(self):
        def ampl(x, t, s=1.0): 
            """
            t: offset
            s: width of exp needs to be roughly bit duration...
            """
            return np.exp(- (x - t) **2 / s)
        temp = np.zeros(self.N)
        for idx in range(len(self.bits)):
            temp += ampl(self.t, idx * self.Ts, self.Ts / self.fs)
        self.signal = self.M.ravel() * temp * np.sin(2 * np.pi * self.fc * self.t)
        plt.plot(self.t, temp, "g--")
        return self.signal

test_class(_Simple)
ex = _Simple()
ex.encode()
ex.decode()
ex.plot()
