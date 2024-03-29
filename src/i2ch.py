# Handle I2C accelerometer
# freely inspired by https://github.com/larsks/py-mpu6050/blob/master/mpu6050.py


import machine
from ustruct import unpack
import utime

I2C_PIN_VCC = 25
I2C_PIN_SDA = 21
I2C_PIN_SCL = 22

MPU_DEFAULT_ADDR = 0x68
MPU_REG_PWR_MGMT1 = 107
MPU_REG_RANGE_MGM = 28
MPU_REG_SENSORVAL = 59
MPU_LSB_TO_MS2 = (9.806/4096.0)
MPU_LSB_TO_RADS = (3.1415/180.0)*(205.0/32768.0)
MPU_SAMPLING_RATE_DEFAULT = 50

MPU_OFFSETS = dict({'ax': 0, 'ay': 0, 'az': 0, 'temp': 0, 'rx': 0, 'ry': 0, 'rz': 0})
IMU_TIMER_ID = 0

class I2cAcc:
	def __init__(self, addr=MPU_DEFAULT_ADDR, pin_vcc=I2C_PIN_VCC, \
		pin_sda=I2C_PIN_SDA, pin_scl=I2C_PIN_SCL, offsets=MPU_OFFSETS, \
		dt_sampling_ms=MPU_SAMPLING_RATE_DEFAULT, uardu=None, raw_print = False):
		self.addr = addr
		self.id_pin_vcc = pin_vcc
		self.id_pin_sda = pin_sda
		self.id_pin_scl = pin_scl
		self.uardu = uardu
		self.pin_vcc = machine.Pin(self.id_pin_vcc, machine.Pin.OUT)
		self.pin_sda = machine.Pin(self.id_pin_sda, machine.Pin.IN, machine.Pin.PULL_UP)
		self.pin_scl = machine.Pin(self.id_pin_scl, machine.Pin.IN, machine.Pin.PULL_UP)
		self.offsets = offsets.copy()
		self.raw_print = raw_print
		self.dt_sampling_ms = dt_sampling_ms
		self.i2c = None
		self.is_powered = False
		self.buffer = bytearray(16)
		self.bytebuf = memoryview(self.buffer[0:1])
		self.wordbuf = memoryview(self.buffer[0:2])
		self.sensors = bytearray(14)
		self.sensor_dict_raw = dict({'t': 0.0, 'ax': 0, 'ay': 0, 'az': 0, 'temp': 0, 'rx': 0, 'ry': 0, 'rz': 0})
		self.sensor_dict = dict({'t': 0.0, 'ax': 0.0, 'ay': 0.0, 'az': 0.0, 'temp': 0.0, 'rx': 0.0, 'ry': 0.0, 'rz': 0.0})
		self.timer = machine.Timer(IMU_TIMER_ID)
		self.paused = True
		pass
	
	def start(self):
		print("Starting IMU Timer...")
		self.timer.init(period=self.dt_sampling_ms, callback=self._timed_cb)
		print("Timer started.")
		self.paused = False
		pass
		
	def pause(self):
		if self.paused:
			self.start()
		else:
			self.timer.deinit()
			self.paused = True
		pass
	
	def _power_on(self):
		self.pin_vcc.value(1)
		self.is_powered = True
		pass
	
	def power_on(self):
		self._power_on()
		machine.sleep(200)
		self.i2c = machine.I2C(1, scl=self.pin_scl, sda=self.pin_sda)
		machine.sleep(200)
		self.write_byte(MPU_REG_PWR_MGMT1, 0)
		#machine.sleep(200)
		#self.set_default_range()
		pass
	
	def power_on_withpauses(self, p1, p2, p3):
		self._power_on()
		machine.sleep(p1)
		self.i2c = machine.I2C(1, scl=self.pin_scl, sda=self.pin_sda)
		machine.sleep(p2)
		self.write_byte(MPU_REG_PWR_MGMT1, 0)
		machine.sleep(p3)
		self.set_default_range()
		pass
		
	
	def _timed_cb(self, t_obj):
		self.sample_all()
		self._print_on_repl()
		pass
		
	# prints the current contents of sensor_dict on the repl prompt.
	def _print_on_repl(self):
		#s2send="{t:.1f}\tACC\t{ax:.7f},{ay:.7f},{az:.7f},{rx:.7f},{ry:.7f},{rz:.7f}".format(**self.sensor_dict)
		s2send="{t:.1f}\tACC\t{ax:.4f},{ay:.4f},{az:.4f},{rx:.4f},{ry:.4f},{rz:.4f}".format(**self.sensor_dict)
		if self.raw_print:
			print(s2send)
		if not (self.uardu is None):
			self.uardu.send_str(s2send)
		pass
	
	def _power_off(self):
		self.pin_vcc.value(0)
		self.is_powered = False
		pass
	
	def _create_i2c_connection(self):
		self.i2c = machine.I2C(1, scl=self.pin_scl, sda=self.pin_sda)
		pass
	
	def write_byte(self, reg, val):
		self.bytebuf[0] = val
		self.i2c.writeto_mem(self.addr, reg, self.bytebuf)
		pass
	
	def read_uint8(self, reg):
		self.i2c.readfrom_mem_into(self.addr, reg, self.bytebuf)
		return self.bytebuf[0]
	
	def set_default_range(self): # +/-8g, +/-205°/s
		self.write_byte(MPU_REG_RANGE_MGM, 16)
		pass
	
	def _read_sensors_buffer(self):
		self.i2c.readfrom_mem_into(self.addr, MPU_REG_SENSORVAL, self.sensors)
		pass
	
	def _unpack_sensors_values(self):
		self.sensor_dict_raw['ax'] = unpack('>h', self.sensors[0:2])[0]
		self.sensor_dict_raw['ay'] = unpack('>h', self.sensors[2:4])[0]
		self.sensor_dict_raw['az'] = unpack('>h', self.sensors[4:6])[0]
		self.sensor_dict_raw['temp'] = unpack('>h', self.sensors[6:8])[0]
		self.sensor_dict_raw['rx'] = unpack('>h', self.sensors[8:10])[0]
		self.sensor_dict_raw['ry'] = unpack('>h', self.sensors[10:12])[0]
		self.sensor_dict_raw['rz'] = unpack('>h', self.sensors[12:14])[0]
		self.sensor_dict_raw['t'] = utime.ticks_ms()
		pass
	
	def _to_physical_units(self):
		self.sensor_dict['ax'] = (self.sensor_dict_raw['ax'] - self.offsets['ax']) * MPU_LSB_TO_MS2
		self.sensor_dict['ay'] = (self.sensor_dict_raw['ay'] - self.offsets['ay']) * MPU_LSB_TO_MS2
		self.sensor_dict['az'] = (self.sensor_dict_raw['az'] - self.offsets['az']) * MPU_LSB_TO_MS2
		self.sensor_dict['rx'] = (self.sensor_dict_raw['rx'] - self.offsets['rx']) * MPU_LSB_TO_RADS
		self.sensor_dict['ry'] = (self.sensor_dict_raw['ry'] - self.offsets['ry']) * MPU_LSB_TO_RADS
		self.sensor_dict['rz'] = (self.sensor_dict_raw['rz'] - self.offsets['rz']) * MPU_LSB_TO_RADS
		self.sensor_dict['t'] = self.sensor_dict_raw['t']
		pass
	
	def sample_all(self):
		self._read_sensors_buffer()
		self._unpack_sensors_values()
		self._to_physical_units()
		pass
		
	


