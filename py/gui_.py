"""
Plan: 
    fdm, ook, ofdm are implemented as a class which contain a widget called
    main_widget. The class also implements Method i.e. encode, decode, plot,
    error_estimate Call MeasurmentGui to insert the widget we can swap it on
    the fly and then restart the signal (perhaps check for changes?) 
"""
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
        self.sc.axes.set_title("f: {}".format(self.k))
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
        self.sc.axes.set_title("f: {}".format(self.k))
        self.sc.draw()



app = QtWidgets.QApplication(sys.argv)
#w = MainWindow()



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

        self.show()
    def start(self):
        pass
    def stop(self):
        pass
    def restart(self):
        pass
        

class Exampole:
    def __init__(self):
        self.main_widget = QtWidgets.QPushButton("MAINWIDGET")
        
ex = Test()
a = MeasurmentGui(ex)
app.exec_()

