
<video src="doc/example_gui.mp4"></video>
py/ or python_/ contains the python impl

python_terminal_mode/ contains the terminal app see below on how to run

matlab/ contains the matlab impl TODO...

misc/ contains test functions and WIP

data/ contains example data

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

for terminal 
```
cd python_terminal_mode
python3 main.py
//or for help mode 
python main.py --help 
//or measurment with default values will plot by default
python main.py ook 
```



