"""
references: 
    https://de.wikipedia.org/wiki/Orthogonales_Frequenzmultiplexverfahren
    https://www.cwnp.com/understanding-ofdm-part-2-2/ 
    https://dspillustrations.com/pages/posts/misc/python-ofdm-example.html

TODO
- [x] mapping
- [] pilots 
    => insert at every 6 data point a known value for channel estimation i.e 1+1j
- [] fft
    => just signal = fft.ifft(dat)
- [] cp
    => signal = np.append(signal, signal[ -len(signal) // 4 : ]  ?
- [] guard do we need one?
    => done with cp otherwise just pad the signal with zeros. Need to figure
       out how extacle gen and scp receive/transmit signals here..

"""
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
from scipy.signal import find_peaks
import scipy.fft as fft
import itertools #for bit combintatio testing

####
# mapping table
####
QAM = { (0,0) : 1+1j, (1,0) : 1-1j, (1,1): -1-1j, (0,1): -1+1j}
QAM16 = {
    (0,0,0,0) : -3-3j,
    (0,0,0,1) : -3-1j,
    (0,0,1,0) : -3+3j,
    (0,0,1,1) : -3+1j,
    (0,1,0,0) : -1-3j,
    (0,1,0,1) : -1-1j,
    (0,1,1,0) : -1+3j,
    (0,1,1,1) : -1+1j,
    (1,0,0,0) :  3-3j,
    (1,0,0,1) :  3-1j,
    (1,0,1,0) :  3+3j,
    (1,0,1,1) :  3+1j,
    (1,1,0,0) :  1-3j,
    (1,1,0,1) :  1-1j,
    (1,1,1,0) :  1+3j,
    (1,1,1,1) :  1+1j
}


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

class OFDM:
    def __init__(self, Ts=30e-03, fs=44000, fc=1800, df = 100, Nbits=12, generate=True):
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
        self.baud = 1/self.Ts
        self.Ns = int( self.fs / self.baud ) #number of samples points per symbol
        self.N = self.Nbits * self.Ns
        self.t = np.r_[0.0 : self.N] / self.fs
        self.generate = generate

        if generate:
            self.bits = (np.random.rand(self.Nbits, 1) > 0.5).astype("int")

    def encode(self, bits=None):
        """
            for convinence bits should be a multilpe of 2 or 4 or 6 since we are using
            QAM or 16QAM. we are not going to bother with padding or checking anything else

            bits also should not be larger than 2 * 40 or 4 * 40 since we are using 40 subcarries...

        """
        if np.all(bits) != None and not self.generate:
            assert(len(bits) == self.Nbits)
            self.bits = bits
        assert( len(bits) & 2 == 0)
        mode = len(bits) % 4 != 0
        if mode:
            mapping = QAM16
            mode = 4
        else:
            mapping = QAM
            mode = 2
        def split(x, size):
            t = []
            for i in range(len(x) // size):
                t.append(x[ i * size : (i+1) * size])
            return t
        tupleList = [tuple(s) for s in split(self.bits, mode)]
        mappedBits = [ mapping[tup] for tup in tupleList]

        self.signal = np.zeros(self.N)
        for idx, bit in enumerate(self.bits):
            self.signal += bit * np.sin(2 * np.pi * self.t * (self.lower + idx * self.df))
        return self.signal

    def decode(self):
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
        #assert(np.all(result == self.bits.flatten()))
        return result

    def plot(self):
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

    def error_estimate(self):
        pass

def test_class(obj, Nbits=10):
    blist = list(itertools.product([0, 1], repeat=Nbits))
    blist = np.array(blist)
    ex = obj()
    for bits in blist:
        ex.encode(bits)
        ex.decode()

def plot_class(obj):
    ex = obj()
    ex.encode()
    ex.decode()
    ex.plot()

if __file__ == "__main__":
    plot_class(OFDM)
