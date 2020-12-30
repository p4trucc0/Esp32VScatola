# Patrucco, 28/12/2020
# ESP32-based GPS+IMU serial instrument.

print("PATRUCK V-SCATOLA 2.0")
from gpsh import *
from i2ch import *

u = UartGps()
i = I2cAcc()
i.offsets['ax'] = 175
i.offsets['ay'] = 0
i.offsets['az'] = -670
i.offsets['rx'] = -400
i.offsets['ry'] = -370
i.offsets['rz'] = 20
