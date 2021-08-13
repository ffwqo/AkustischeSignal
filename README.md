

src/ the program 

- main.py terminal mode
- main_gui.py dearpygui

misc/ misc old files 

# Installation

```
pip install -r requirements.txt
```

Make sure matlab is in $PATH refer to [Matlab API for python install](https://de.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)
to install the matlab engine for python for use in the py/ or python/ scripts

# Run

for gui
```
cd python_terminal_mode
python3 main_gui.py
```
set osci parameter > check OOK/FDM > set OOK/FDM parameter = executes !

for terminal 
```
cd python_terminal_mode
python3 main.py
//or for help mode 
python main.py --help 
//or measurment with default values will plot by default
python main.py ook 
```



