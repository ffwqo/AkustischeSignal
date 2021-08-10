from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QApplication, QScrollArea
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

class ValidationError(Exception):
    pass

class OSCIWIDGET(QWidget):
    parameters_updated = pyqtSignal(list)
    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
    def __init__(self):
        super(OSCIWIDGET, self).__init__()

        self.widget = uic.loadUi("./osci_param.ui")
        ok_btn = QPushButton("Set Osci Parameters")
        ok_btn.clicked.connect(self._ok_clicked)
        
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(ok_btn)
        self.setLayout(layout)

    def _ok_clicked(self):

        try:
            self._validate_parameters()
        except ValidationError:
            print("ValidationError in setting osci parameters")
            return
        result = [  self.scp_mode         , 
                    self.scp_fs           , 
                    self.scp_record_length, 
                    self.gen_signal_type  , 
                    self.gen_fre_mode     , 
                    self.gen_fs           , 
                    self.gen_amp          , 
                    self.gen_offset       , 
                    self.gen_output_on    
                ]
        self.parameters_updated.emit(result)

    
    def _validate_parameters(self):


        scp_mode          = self.widget.scpmodeInput.currentText()
        scp_fs            = self.widget.scpfsInput.text()
        scp_record_length = self.widget.scprecordInput.text()
        gen_signal_type   = self.widget.genSignalTypeInput.currentText()
        gen_fre_mode      = self.widget.genFreModeInput.currentText()
        gen_fs            = self.widget.genFrequencyInput.text()
        gen_amp           = self.widget.genAmpInput.text()
        gen_offset        = self.widget.genOffsetInput.text()
        gen_output_on      = self.widget.genOutputonInput.isChecked()

        if scp_fs == "" or scp_record_length == "" or gen_fs == "" or gen_amp == "" or gen_offset == "" or gen_output_on == "":
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
        def validate_int(x, name):
            temp = None
            try:
                temp = int(x)
            except ValueError:
                print(f"{name} has to be integer")
                raise ValidationError
            return temp
        def validate_positve(temp, name):
            if temp < 0: 
                print(f"{name} cannot be negative")
                raise ValidationError
            return temp

        try:
            scp_fs = validate_float(scp_fs, "scp_fs")
            scp_fs = validate_positve(scp_fs, "scp_fs")
        except Exception as e:
            raise e
        try: 
            scp_record_length = validate_int(scp_record_length, "scp_record_length")
            scp_record_length = validate_positve(scp_record_length, "scp_record_length")
        except Exception as e:
            raise e
        try: 
            gen_fs = validate_float(gen_fs, "gen_fs")
            gen_fs = validate_positve(gen_fs, "gen_fs")
        except Exception as e:
            raise e
        try: 
            gen_amp = validate_float(gen_amp, "gen_amp")
            gen_amp = validate_positve(gen_amp, "gen_amp")
        except Exception as e:
            raise e
        try: 
            gen_offset = validate_float(gen_offset, "gen_offset")
            gen_offset = validate_positve(gen_offset, "gen_offset")
        except Exception as e:
            raise e
        try: 
            gen_output_on = validate_float(gen_output_on, "gen_output_on")
            gen_output_on = validate_positve(gen_output_on, "gen_output_on")
        except Exception as e:
            raise e

        print("Osci parameters set")
        self.scp_mode          = scp_mode          
        self.scp_fs            = scp_fs            
        self.scp_record_length = scp_record_length 
        self.gen_signal_type   = gen_signal_type   
        self.gen_fre_mode      = gen_fre_mode      
        self.gen_fs            = gen_fs            
        self.gen_amp           = gen_amp           
        self.gen_offset        = gen_offset        
        self.gen_output_on      = gen_output_on      
    def set_scp_mode(self, scp_mode):
        self.scp_mode          = scp_mode          
        self.widget.scpmodeInput.setCurrentText(scp_mode)
    def set_scpfs(self, scp_fs):
        self.scp_fs            = scp_fs            
        self.widget.scpfsInput.setText(str(scp_fs))
    def set_scp_record_length(self, scp_record_length):
        self.scp_record_length = scp_record_length 
        self.widget.scprecordInput.setText(str(scp_record_length))
    #def set_gen_signal_type(self, gen_signal_type):
    #    self.gen_signal_type   = gen_signal_type   
    #    self.widget.genSignalTypeInput.setCurrentText(gen_signal_type)
    #def set_gen_fre_mode(self, gen_fre_mode):
    #    self.gen_fre_mode      = gen_fre_mode      
    #    self.widget.genFreModeInput.setCurrentText(gen_fre_mode)
    def set_gen_fs(self, gen_fs):
        self.gen_fs            = gen_fs            
        self.widget.genFrequencyInput.setText(str(gen_fs))
    def set_gen_amp(self, gen_amp):
        self.gen_amp           = gen_amp           
        self.widget.genAmpInput.setText(str(gen_amp))
    def set_gen_offset(self, gen_offset):
        self.gen_offset        = gen_offset        
        self.widget.genOffsetInput.setText(str(gen_offset))
    def set_gen_output_on(self, gen_output_on):
        self.gen_output_on      = gen_output_on      
        self.widget.genOutputonInput.setChecked(gen_output_on)




if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main = OSCIWIDGET()
    main.show()
    app.exec_()

