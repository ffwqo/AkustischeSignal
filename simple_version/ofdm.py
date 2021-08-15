"""
use in main via 

``` python
from <filename> import *
```

adapted from 
https://rfmw.em.keysight.com//wireless/helpfiles/89600b/webhelp/subsystems/wlan-ofdm/Content/ofdm_basicprinciplesoverview.htm
https://colab.research.google.com/github/varun19299/wireless-lab-iitm/blob/notebooks/4-ofdm-python.ipynb#scrollTo=AzE6CH2CUs4s
https://de.mathworks.com/help/lte/ug/channel-estimation.html

"""

import scipy
from scipy import signal as scipysignal
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})
from scipy.signal import find_peaks
import scipy.fft as fft
import itertools #for bit combintatio testing

QAM16 = {
  int( "".join([str(i) for i in list( (0,0,0,0) )]), 2) : -3-3j,
  int( "".join([str(i) for i in list( (0,0,0,1) )]), 2) : -3-1j,
  int( "".join([str(i) for i in list( (0,0,1,0) )]), 2) : -3+3j,
  int( "".join([str(i) for i in list( (0,0,1,1) )]), 2) : -3+1j,
  int( "".join([str(i) for i in list( (0,1,0,0) )]), 2) : -1-3j,
  int( "".join([str(i) for i in list( (0,1,0,1) )]), 2) : -1-1j,
  int( "".join([str(i) for i in list( (0,1,1,0) )]), 2) : -1+3j,
  int( "".join([str(i) for i in list( (0,1,1,1) )]), 2) : -1+1j,
  int( "".join([str(i) for i in list( (1,0,0,0) )]), 2) :  3-3j,
  int( "".join([str(i) for i in list( (1,0,0,1) )]), 2) :  3-1j,
  int( "".join([str(i) for i in list( (1,0,1,0) )]), 2) :  3+3j,
  int( "".join([str(i) for i in list( (1,0,1,1) )]), 2) :  3+1j,
  int( "".join([str(i) for i in list( (1,1,0,0) )]), 2) :  1-3j,
  int( "".join([str(i) for i in list( (1,1,0,1) )]), 2) :  1-1j,
  int( "".join([str(i) for i in list( (1,1,1,0) )]), 2) :  1+3j,
  int( "".join([str(i) for i in list( (1,1,1,1) )]), 2) :  1+1j
}


################
## OFDM SIMPLE ##
################

class OFDM:
    """ofdm after 802.11a standard"""

    def __init__(self, Nsubcarrier=64, Npilot=8, pilot_amp=3+3j):

        self.Nsubcarrier = Nsubcarrier
        self.Npilot = Npilot
        self.pilot_amp = pilot_amp
        allidx = np.arange(Nsubcarrier)
        pilot_idx = allidx[::Nsubcarrier // Npilot]
        pilot_idx = np.r_ [ pilot_idx, [allidx[-1] ]]
        self.Npilot += 1
        data_idx = np.delete(allidx, pilot_idx)

        self.allidx = allidx
        self.pilot_idx = pilot_idx
        self.data_idx = data_idx
        self.Ndata = len(data_idx)
        self.cp = int(0.25 * Nsubcarrier)

    def generate(self, Nbits=220):
        """Nbits= 4 * 52 for a single batch"""
        assert(Nbits % 4 == 0)
        return np.array( [ int(i) for i in (np.random.rand(Nbits) > 0.5)])

    def encode(self, bits):
        """use bit array of length 220, 440, 660, etc. for no pad"""
        assert(len(bits) % 4 == 0)
        Ndata = self.Ndata
        chunks = np.split(bits, len(bits) // 4)
        chunks = [ int( "".join([str(i) for i in chunk]), 2) for chunk in chunks]
        mapped_bits = [ QAM16[i] for i in chunks]
        pad = (-1* len(mapped_bits)) % Ndata# i.e. (-12) % 48 = 36 
        print(f"padding chunks with: {pad} zeros")
        chunks = np.r_ [mapped_bits, [0 for _ in range(pad)]]

        pilot_idx = self.pilot_idx
        data_idx = self.data_idx
        Nsubcarrier = self.Nsubcarrier
        pilot_amp = self.pilot_amp
        datalist = []
        for i in range(len(chunks) // Ndata):
            temp = chunks[i*Ndata: (i+1)*Ndata]
            data = np.zeros(Nsubcarrier, dtype=complex)
            data[pilot_idx] = pilot_amp
            data[data_idx] = temp
            datalist.append(data)

        #add cp 
        signal = []
        cp = self.cp
        for i in range(len(datalist)):
            complex_signal = fft.ifft(datalist[i] )
            temp = np.r_ [ complex_signal[-cp:], complex_signal]
            signal.append(temp)
        result = np.concatenate(signal)
        return result

    def decode(self, signal, testing=False):
        """returns a list of demod complex data symbols per burst i.e. should be of length 55 per burst"""

        #demod 
        numberOfBurst = len(signal) // (self.cp + self.Nsubcarrier)
        offset = self.cp + self.Nsubcarrier

        demodlist = []
        for i in range(numberOfBurst):
            temp = signal[i * offset : (i+1) * offset]
            temp = temp[self.cp:]
            demod = fft.fft(temp)
            
            channel_estimate = self._channel_estimate(demod) #estimate
            equalize = self._equalize(demod, channel_estimate) #equalize

            demodlist.append(demod[self.data_idx])
        return demodlist

    def _equalize(self, demod, hest):
        return demod / hest
    def _channel_estimate(self, demod):
        """demod: demodulated signal and cp removed to estimate the effect of transmission for use in equalize"""
        transmittedPilots = demod[self.pilot_idx]
        h = transmittedPilots / self.pilot_amp
        #simple linear fit
        estimate = scipy.interpolate.interp1d(self.pilot_idx, np.abs(h), kind="linear")(self.allidx)
        estimatePhase = scipy.interpolate.interp1d(self.pilot_idx, np.angle(h), kind="linear")(self.allidx)
        hest = estimate * np.exp(1j * estimatePhase)
        return hest


    def plot(self, signal, bits, show=False, title="", style="b"):
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
    bits = ex.generate()
    signal = ex.encode(bits)
    ex.decode(signal, bits)
    ex.plot(signal, bits)


if __name__ == "__main__":
    device = OFDM()
    bits = device.generate()
    signal = device.encode(bits)
    demod = device.decode(signal)[0]
    print(demod)


