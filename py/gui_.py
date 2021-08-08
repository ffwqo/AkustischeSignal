"""
Plan: 
    fdm, ook, ofdm are implemented as a class which contain a widget called
    main_widget. The class also implements Method i.e. encode, decode, plot,
    error_estimate Call MeasurmentGui to insert the widget we can swap it on
    the fly and then restart the signal (perhaps check for changes?) 
TODO
    - [] ook widget
    - [] fdm widget
    - [] ofdm widget
    - [] AWG parameters...
    - [] implement the BLOCK / STREAM mode selection
"""
import time 
import os
from array import array
import libtiepie
from printinfo import *

import sys
import matplotlib
import numpy as np
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class Test(QtWidgets.QWidget):
    """
        random test
    """
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)

        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.sc2 = MplCanvas(self, width=5, height=4, dpi=100)
        self.k = 1.0
        self.xdata = np.linspace(0, 10, 100)
        self.ydata = np.sin( self.k * 2 * np.pi * self.xdata)
        self.sc.axes.plot(self.xdata, self.ydata)
        self.sc.axes.set_title(f"f: {self.k}")
        self.sc2.axes.plot(self.xdata, np.cos(self.k * 2 * np.pi * self.xdata))
        
        self.toolbar = NavigationToolbar2QT(self.sc, self)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMaximum(1_000_000)
        self.slider.setMinimum(10)
        self.slider.setValue(200)
        self.slider.valueChanged.connect(self.update_slider)
        self.button = QtWidgets.QPushButton("Hide toolbar")
        self.button.clicked.connect(self.hide_toolbar)
        self.hidden = False


        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.sc)
        layout.addWidget(self.sc2)
        layout.addWidget(self.slider)
        layout.addWidget(self.button)


        self.setLayout(layout)

        self.show()
    def hide_toolbar(self):
        self.hidden = not self.hidden
        self.toolbar.setHidden( self.hidden)
    def update_slider(self):
        self.k = float(self.slider.value())
        self.sc.axes.cla()
        self.ydata = np.sin( self.k * 2 * np.pi * self.xdata)
        self.sc.axes.plot(self.xdata, self.ydata)
        self.sc.axes.set_title(f"f: {self.k}")
        self.sc.draw()



app = QtWidgets.QApplication(sys.argv)
#w = MainWindow()


class MeasurementTask(QtCore.QObject):
    """
    for use with QThread
    do I need a mutex?
    """
    finished     = QtCore.pyqtSignal(np.ndarray)
    finished_gen = QtCore.pyqtSignal()
    progress     = QtCore.pyqtSignal()

    def __init__(self, scp, gen, chunks, mode):
        """
        chunks: lsit of data chunks if mode is block chunks should be just
                [data]
        mode: either STREAM or BLOCk
        """
        QtCore.QObject.__init__(self)
        self.scp = scp
        self.gen = gen
        assert( mode == "BLOCK" and len(chunks) == 1)
        self.chunks = chunks
        self.mode = mode
        self.filename="measure_data.txt"

    def run(self):

        scp = self.scp
        gen = self.gen
        chunks = self.chunks
        mode = self.mode
        result = []

        try:
            scp.start()

            for i in range(len(chunks)):
                gen.set_data(chunks[i])
                gen.start()

                while not (scp.is_data_ready or scp.is_data_overflow):
                    time.sleep(0.01)
                if scp.is_data_overflow:
                    print("Data overflow")
                d = np.array(scp.get_data())
                """
                scp returns data like 
                     --------->
                #Ch1 | 2 3 5 6 
                #Ch2 | 2 -3 -2 -2
                     V
                result[i] looks like
                | 2 2
                | 3 -3
                | 5 -2
                V 6  -2
                """
                result.append(d.transpose())
                gen.stop()
            
            self.finished_gen.emit()
            scp.stop()

            #result will be a list of data arrays need to append them each other
            #TODO might have to transpose first
            #TODO need to figure out the right order here
            data = np.concatenate(result)

            header = ""
            filename = self.filename
            i = 0
            while os.path.isfile(filename):
                filename = f"measure_data_{i}_{mode}.txt"
                i += 1


            for i in range(len(scp.channels)):
                header += f"Ch{i+1}\t"
            np.savetxt(filename, np.array(data).transpose(), header=header)
        except:
            print("Cannot start measurement")
            raise Exception
        self.finished.emit(result)
        pass




class MeasurmentGui(QtWidgets.QMainWindow):
    def __init__(self, obj, *args, **kwargs):
        super(MeasurmentGui, self).__init__(*args, **kwargs)
        self.setWindowTitle("GUI -- MP2")

        self.vlayout = QtWidgets.QVBoxLayout()
        self.vwidget = QtWidgets.QWidget()
        self.vlayout.addWidget(obj)
        #self.method_obj = obj
        #self.vlayout.addWidget(self.method_obj.main_widget)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hwidget = QtWidgets.QWidget()

        startButton = QtWidgets.QPushButton("Start")
        startButton.clicked.connect(self.start)
        restartButton = QtWidgets.QPushButton("Restart")
        restartButton.clicked.connect(self.restart)
        stopButton = QtWidgets.QPushButton("Stop")
        stopButton.clicked.connect(self.stop)
        self.hlayout.addWidget(startButton)
        self.hlayout.addWidget(restartButton)
        self.hlayout.addWidget(stopButton)
        self.hwidget.setLayout(self.hlayout)

        self.vlayout.addWidget(self.hwidget)
        self.vwidget.setLayout(self.vlayout)
        self.setCentralWidget(self.vwidget)

        #self._osci_setup()
        self.show()
    def start(self):
        self.gen.start()
        self.scp.start()
        pass
    def stop(self):
        pass
    def restart(self):
        pass
    def _measurement(self):
        #need to start this in thread I think...
        #result = run(scp, gen)
        pass
    def _gen_set_data(self, data):
        try:
            self.gen.set_data(data)
        except:
            print("Error cannot set gen data")
            raise Exception

    def _scp_gen_set_param(self):
        """
        Important! does not set data!!
        """
        try:
            self.scp.measure_mode = self.measure_mode 
            self.scp.sample_frequency = self.sample_frequency 
            self.scp.record_length = self.record_length 

            for ch in self.scp.channels:
                ch.enabled = True
                ch.range = 0
                ch.coupling = libtiepie.CK_DCV

            self.gen.signal_type = self.signal_type 
            self.gen.frequency_mode = self.frequency_mode 
            self.gen.frequency = self.gen_frequency 
            self.gen.amplitude = self.gen_amp 
            self.gen.offset = self.gen_offset 
            self.gen.output_on = self.gen_ouput_on 
        except:
            print("Cannot set scp and gen data")
            raise Exception
    def _osci_setup(self, debug=False):
        """
        Initializes scp and gen but does not set any data for gen
        Debug uses the printinfo library
        """

        if debug:
            print_device_info()

        libtiepie.network.auto_detect_enabled = True
        libtiepie.device_list.update()

        #TODO make gui elements for this
        self.measure_mode = libtiepie.MM_BLOCK
        self.sample_frequency = 20e3
        self.record_length = 10000
        self.signal_type = libtiepie.STB_ARBITRARY
        self.frequency_mode = libtiepie.FMB_SAMPLEFREQUENCY
        self.gen_frequency = 20e3
        self.gen_amp = 4
        self.gen_offset = 0
        self.gen_ouput_on = True
        self.scp_dict = {}
        self.gen_dict = {}
        self.mode_stringify = { libtiepie.MM_BLOCK : "BLOCK", libtiepie.MM_STREAM : "STRAM"}

        scp = None
        gen = None

        #get for MM_BLOCK
        for item in libtiepie.device_list:
            if ( item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE)) and (item.can_open(libtiepie.DEVICETYPE_GENERATOR)):
                scp = item.open_oscilloscope()
                if scp.measure_modes & libtiepie.MM_BLOCK:
                    gen = item.open_generator()
                    if gen.signal_type & libtiepie.ST_ARBITRARY:
                        break
                else:
                    scp = None
        if scp != None:
            self.scp_dict[libtiepie.MM_BLOCK] = scp
            self.gen_dict[libtiepie.MM_BLOCK] = gen
        else:
            print("SCP/GEN NOT FOUND FOR MM_BLOCK")
        scp = None
        gen = None
        for item in libtiepie.device_list:
            if ( item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE)) and (item.can_open(libtiepie.DEVICETYPE_GENERATOR)):
                scp = item.open_oscilloscope()
                if scp.measure_modes & libtiepie.MM_STREAM:
                    gen = item.open_generator()
                    if gen.signal_type & libtiepie.ST_ARBITRARY:
                        break
                else:
                    scp = None
        if scp != None:
            self.scp_dict[libtiepie.MM_STREAM] = scp
            self.gen_dict[libtiepie.MM_STREAM] = gen
        else:
            print("SCP/GEN NOT FOUND FOR MM_STREAM")
        if self.measure_mode in self.scp_dict:
            self.scp = self.scp_dict[self.measure_mode]
            self.gen = self.gen_dict[self.measure_mode]
        else:
            self.scp = None
            self.gen = None

        scp = self.scp #takes a reference
        gen = self.gen


        if scp and gen:
            try:
                self._scp_gen_set_param()
                if debug:
                    print_device_info(scp)
                    print_device_info(gen)
            except Exception as e:
                print("Exception: " + str(e))
                print(sys.exc_info()[0], flush=True)
                sys.exit(1)
        else:
            print("No device avaible for measurement in", self.mode_stringify[self.measure_mode], "mode")
            sys.exit(1)

            



        

        
if __name__ == "__main__":
    ex = Test()
    a = MeasurmentGui(ex)
    app.exec_()

