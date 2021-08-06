# template to implement a modulation scheme for use in main
# import it via 
# ``` python
# from <filename> import *
# ```

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 22})


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


