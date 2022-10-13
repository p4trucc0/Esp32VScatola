# Patrucco, 28/12/2020
# ESP32-based GPS+IMU serial instrument.

print("PATRUCK V-SCATOLA 2.0")
from gpsh import *
from i2ch import *
import uarduino
import utime

a = uarduino.Uarduino()
u = UartGps(uardu=a)
i = I2cAcc(uardu=a)
i.offsets['ax'] = 175
i.offsets['ay'] = 0
i.offsets['az'] = -670
i.offsets['rx'] = -400
i.offsets['ry'] = -370
i.offsets['rz'] = 20
# Performing turn-on sequence externally
#u.start()
#i.start()

'''spi = machine.SPI(1)
spi.init(baudrate=500000, sck=machine.Pin(18), miso=machine.Pin(19), \
	mosi=machine.Pin(23))
p_sd = machine.Pin(27)
p_sd.init(27, machine.Pin.OUT)
p_cs = machine.Pin(5)'''




i.power_on()
i.set_default_range()

u.start()
utime.sleep_ms(1000)
i.start()

