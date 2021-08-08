from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

class ValidationError(Exception):
    pass

class OOKWidget(QWidget):
    method_parameters_updated = pyqtSignal(dict)
    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __init__(self):
        super(OOKWidget, self).__init__()

        self.widget = uic.loadUi("./ook_widget.ui")
        ok_btn = QPushButton("Set Parameters")
        ok_btn.clicked.connect(self._ok_clicked)
        
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(ok_btn)
        self.setLayout(layout)

    def _ok_clicked(self):

        try:
            self._validate_parameters()
        except ValidationError:
            print("ValidationError")
            return
        result = { 
                "mode" : "OOK",
                "Ts" : self.Ts, 
                "fs" : self.fs, 
                "fc" : self.fc,
                "bits": self.bits,
                "Nbits": self.Nbits,
                "generate": self.generate
                }
        self.method_parameters_updated.emit(result)

    def _validate_parameters(self):

        Ts = self.widget.TsInput.text()
        fs = self.widget.fsInput.text()
        fc = self.widget.fcInput.text()
        bits = self.widget.bitsInput.text()
        Nbits = self.widget.NbitsInput.value()
        generate = self.widget.generateInput.isChecked()

        if Ts == "" or fs == "" or fc == "" or ( bits == "" and generate == False):
            print("Empty field in parameters input")
            raise ValidationError
        def validate_float(x, name):
            temp = None
            try:
                temp = float(x)
            except ValueError:
                print(f"{name} has to be a float or integer")
                raise ValidationError
            return temp
        def validate_positve(temp, name):
            if temp < 0: 
                print(f"{name} cannot be negative")
                raise ValidationError
            return temp
        try:
            Ts = validate_float(Ts, "Ts")
            Ts = validate_positve(Ts, "Ts")
        except Exception as e:
            raise e

        try:
            fs = validate_float(fs, "fs")
            fs = validate_positve(fs, "fs")
        except Exception as e:
            raise e

        try:
            fc = validate_float(fc, "fc")
            fc = validate_positve(fc, "fc")
        except Exception as e:
            raise e

        bits = list(bits)
        if set(bits) != {"1", "0"} and not generate:
            print(' only "1" or "0" are valid characters for bits ')
            raise ValidationError
        bits = [int(b) for b in bits]

        print("Parameters set")
        self.Ts = Ts 
        self.fs = fs 
        self.fc = fc 
        self.bits = bits 
        self.Nbits = Nbits 
        self.generate = generate 

    def set_ts(self, Ts):
        self.Ts = Ts
        self.widget.TsInput.setText(str(Ts))
    def set_fs(self, fs):
        self.fs = fs
        self.widget.fsInput.setText(str(fs))
    def set_fc(self, fc):
        self.fc = fc
        self.widget.fcInput.setText(str(fc))
    def set_bits(self, bits):
        self.bits = bits
        self.widget.bitsInput.Text(str(bits))
    def set_nbits(self, Nbits):
        self.Nbits = Nbits
        self.widget.NbitsInput.setText(str(Nbits))
    def set_generate(self, generate):
        self.generate = generate
        self.widget.generateInput.setChecked(str(generate))

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main = OOKWidget()
    main.show()
    app.exec_()
