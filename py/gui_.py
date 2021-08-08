"""
Plan: 
    fdm, ook, ofdm are implemented as a class which contain a widget called
    main_widget. The class also implements Method i.e. encode, decode, plot,
    error_estimate Call MeasurmentGui to insert the widget we can swap it on
    the fly and then restart the signal (perhaps check for changes?) 
TODO
    - [x] ook widget
        - [] plotting?
            => Method.plot(axis) handles plotting the main widget handles the canvas.
    - [x] fdm widget
        - [] plotting?
    - [] ofdm widget
        - [] plotting?
    - [x] AWG parameters...
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
from PyQt5 import uic
from ook_widget import OOKWidget
from fdm_widget import FDMWIDGET
from ook import OOK, test_class, plot_class
from fdm import FDM, test_class, plot_class
from osci_param_widget import OSCIWIDGET

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

class InvalidModulationMode(Exception):
    pass

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class PlotWindowWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(PlotWindowWidget, self).__init__(*args, **kwargs)
        self.canvas = MplCanvas(self, width=4, height=4, dpi=120)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        layout = QtWidgets.QVBoxLayout()
        btn = QtWidgets.QPushButton("Redraw")
        btn.clicked.connect(self._update_draw)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(btn)
        self.setLayout(layout)

    def plot_from_device(self, device):
        """
        device: modulation class such as FDM or OOKSimpleExp which implements plot(self, axes)
        """
        self.canvas.axes.cla()
        device.plot(self.canvas.axes)
        self.canvas.draw()

    def _update_draw(self):
        self.canvas.axes.cla()
        self.canvas.draw()


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


class MeasurementTask(QtCore.QObject):
    """
    for use with QThread
    do I need a mutex?
    """
    finished     = QtCore.pyqtSignal(np.ndarray)
    finished_gen = QtCore.pyqtSignal()
    progress     = QtCore.pyqtSignal()

    def __init__(self, scp, gen, chunks : list, mode : str):
        """
        chunks: list of data chunks if mode is block chunks should be just
                [data]
        mode: either STREAM or BLOCK
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



class MeasurmentGui(QtWidgets.QMainWindow):
    mode_stringify = { libtiepie.MM_BLOCK : "BLOCK", libtiepie.MM_STREAM : "STRAM"}
    def __init__(self, *args, **kwargs):
        super(MeasurmentGui, self).__init__(*args, **kwargs)
        self.setWindowTitle("GUI -- MP2")
        self.method_selection = QtWidgets.QComboBox()
        self.method_selection.addItem("OOK")
        self.method_selection.addItem("FDM")
        self.method_selection.currentIndexChanged.connect(self._method_selection_callback)
        self._construct_param_ui()
        self._init_plot_area()

        self.method_result = None

        self._osci_setup()
        #self.setGeometry(0, 0, 600, 800)
        self.show()
    def _init_plot_area(self):
        self.input_plot_widget = PlotWindowWidget()
        self.input_plot_widget.setWindowTitle("Input Signal Plot")
        self.input_plot_widget.show()

        self.output_plot_widget = PlotWindowWidget()
        self.output_plot_widget.setWindowTitle("Output Scp Plot")
        self.output_plot_widget.show()

    def _osci_set_default_params(self):
        self.measure_mode     = libtiepie.MM_BLOCK
        self.sample_frequency = 20e3
        self.record_length    = 10000
        self.signal_type      = libtiepie.STB_ARBITRARY
        self.frequency_mode   = libtiepie.FMB_SAMPLEFREQUENCY
        self.gen_frequency    = 20e3
        self.gen_amp          = 4
        self.gen_offset       = 0
        self.gen_ouput_on     = True

        self.osci_param_widget.set_scp_mode(self.mode_stringify[self.measure_mode])
        self.osci_param_widget.set_scpfs(self.sample_frequency)
        self.osci_param_widget.set_scp_record_length(self.record_length)
        #self.osci_param_widget.set_gen_signal_type(self.signal_type)
        #self.osci_param_widget.set_gen_fre_mode(self.frequency_mode)
        self.osci_param_widget.set_gen_fs(self.gen_frequency)
        self.osci_param_widget.set_gen_amp(self.gen_amp)
        self.osci_param_widget.set_gen_amp(self.gen_amp)
        self.osci_param_widget.set_gen_offset(self.gen_offset)
        self.osci_param_widget.set_gen_output_on(self.gen_ouput_on)

    def _osci_update_params(self, result : list):
        self.measure_mode     = self.osci_param_widget.scp_mode #returns STREAM or BLOCK
        self.sample_frequency = self.osci_param_widget.scp_fs
        self.record_length    = self.osci_param_widget.scp_record_length
        self.signal_type      = self.osci_param_widget.gen_signal_type
        self.frequency_mode   = self.osci_param_widget.gen_fre_mode
        self.gen_frequency    = self.osci_param_widget.gen_fs
        self.gen_amp          = self.osci_param_widget.gen_amp
        self.gen_offset       = self.osci_param_widget.gen_offset
        self.gen_output_on    = self.osci_param_widget.gen_output_on

        #for k, v in self.__dict__.items():
        #    print(k, v)

    def _modulation_parameters_updated(self, result: dict):
        """
        connects to method_parameters_updated and gets the result as a dict
        the keys are the variable names of the parameters of the function (in the code)
        """
        self.method_result = result

        for k, v in result.items():
            print(k, v)

    def _construct_param_ui(self):

        self.method_label = QtWidgets.QLabel("Modulation Method")
        self.method_layout = QtWidgets.QHBoxLayout()
        self.method_layout.addWidget(self.method_label)
        self.method_layout.addWidget(self.method_selection)
        self.method_selection_widget = QtWidgets.QWidget()
        self.method_selection_widget.setLayout(self.method_layout)

        if self.method_selection.currentText() == "OOK":
            self.method_widget = OOKWidget()
        elif self.method_selection.currentText() == "FDM":
            self.method_widget = FDMWIDGET()
        self.method_widget.method_parameters_updated.connect(self._modulation_parameters_updated)
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.paramlayout = QtWidgets.QVBoxLayout()
        self.paramlayout.addWidget(self.method_selection_widget)
        self.paramlayout.addWidget(line)
        self.paramlayout.addWidget(self.method_widget)
        self.paramlayout.addWidget(line)

        self.osci_param_widget = OSCIWIDGET()
        self._osci_set_default_params()
        self.osci_param_widget.parameters_updated.connect(self._osci_update_params)
        self.paramlayout.addWidget(self.osci_param_widget)
        self.paramlayout.addWidget(line)
        self.paramWidget = QtWidgets.QWidget()
        self.paramWidget.setLayout(self.paramlayout)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hwidget = QtWidgets.QWidget()
        startButton = QtWidgets.QPushButton("Start")
        startButton.clicked.connect(self._start_measurement)
        restartButton = QtWidgets.QPushButton("Restart")
        restartButton.clicked.connect(self.restart)
        stopButton = QtWidgets.QPushButton("Stop")
        stopButton.clicked.connect(self.stop)
        self.hlayout.addWidget(startButton)
        self.hlayout.addWidget(restartButton)
        self.hlayout.addWidget(stopButton)
        self.hwidget.setLayout(self.hlayout)
        self.paramlayout.addWidget(self.hwidget)

        self.main_widget =  QtWidgets.QWidget()
        self.centerLayout = QtWidgets.QHBoxLayout()
        self.centerLayout.addWidget(self.paramWidget)
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.centerLayout.addWidget(line)

        self.main_widget.setLayout(self.centerLayout)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.main_widget)

        self.setCentralWidget(self.scroll_area)

    def _method_selection_callback(self):
        if self.method_selection.currentText() == "OOK":
            method_widget = OOKWidget()
        elif self.method_selection.currentText() == "FDM":
            method_widget = FDMWIDGET()
        self.paramlayout.replaceWidget(self.method_widget, method_widget)
        self.method_widget = method_widget
        self._construct_param_ui()

    def _start_measurement(self):
        print("Starting measurement")
        self._measurement()
    def stop(self):
        print("Stopping measurement")
        scp.stop()
        gen.stop()

    def restart(self):
        pass
    def _measurement(self):
        #need to start this in thread I think...
        if self.method_result == None:
            print("Need to first set parameters")
            return
        self.basethread = QtCore.QThread()

        #self.method_result #params method
        method_result = self.method_result
        if method_result["mode"] == "OOK":
            Ts = method_result["Ts"]
            fs = method_result["fs"]
            fc = method_result["fc"]
            Nbits = method_result["Nbits"]
            generate = method_result["generate"]
            bits = method_result["bits"]
            for k, v in method_result.items():
                print(k, v, type(v))
            self.method_device = OOK(Ts, fs, fc, Nbits, generate)
        elif method_result["mode"] == "FDM":
            Ts = method_result["Ts"]
            fs = method_result["fs"]
            fc = method_result["fc"]
            df = method_result["df"]
            Nbits = method_result["Nbits"]
            generate = method_result["generate"]
            bits = method_result["bits"]
            self.method_device = FDM(Ts, fs, fc, df, Nbits, generate)
        else:
            print("invalid modulation mode")
            raise InvalidModulationMode

        if len(bits) < 1:
            bits = None
        self.input_signal = self.method_device.encode(bits)
        self.input_plot_widget.plot_from_device(self.method_device)
        chunks = [self.input_signal] 

        self.worker = MeasurementTask(self.scp, self.gen, chunks, self.mode_stringify[self.measure_mode])
        self.worker.moveToThread(self.basethread)
        self.basethread.started.connect(self.worker.run)
        self.worker.finished.connect(self.basethread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.basethread.finished.connect(self.basethread.deleteLater)

        self.worker.progress.connect(
                lambda: print("Measurment in progress...")
        )

        self.worker.finished.connect(self._measurement_get_result)
        self.basethread.start()

    def _measurement_get_result(self, result):
        self.output_signal = result
        #TODO important
        #self.output_plot_widget.plot_from_device(self. #TODO


    def _gen_set_data(self, data : array):
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
        self.scp_dict = {}
        self.gen_dict = {}

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
                return
                #sys.exit(1)
        else:
            print("No device avaible for measurement in", self.mode_stringify[self.measure_mode], "mode")
            return
            #sys.exit(1)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    a = MeasurmentGui()
    app.exec_()

