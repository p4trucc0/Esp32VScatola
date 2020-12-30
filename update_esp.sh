ampy -p /dev/ttyUSB0 rm main.py
ampy -p /dev/ttyUSB0 rm gpsh.py
ampy -p /dev/ttyUSB0 rm i2ch.py
ampy -p /dev/ttyUSB0 put src/main.py
ampy -p /dev/ttyUSB0 put src/gpsh.py
ampy -p /dev/ttyUSB0 put src/i2ch.py
