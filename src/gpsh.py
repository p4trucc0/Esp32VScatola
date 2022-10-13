#Patrucco, 2020
# GPS Handler for ESP32

import machine
import utime

#defines
GPS_BAUDRATE = 9600
GPS_RX_PIN = 32
GPS_TX_PIN = 33
GPS_UART_ID = 2
GPS_TIMER_ID = 1
GPS_ENABLED_SENTENCES = 2

#ublox-specific strings
GPS_CMD_UBLOX_SETFREQ_5HZ  = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0xC8, 0x00, 0x01, 0x00, 0x01, 0x00, 0xDE, 0x6A])
GPS_CMD_UBLOX_SETFREQ_10HZ = bytes([0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x64, 0x00, 0x01, 0x00, 0x01, 0x00, 0x7A, 0x12])
GPS_CMD_UBLOX_DISABLE_VTG = bytes([0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x05, 0x47])
GPS_CMD_UBLOX_DISABLE_GGA = bytes([0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x24])
GPS_CMD_UBLOX_DISABLE_GLL = bytes([0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x2B])
GPS_CMD_UBLOX_DISABLE_GSA = bytes([0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x32])
GPS_CMD_UBLOX_DISABLE_GSV = bytes([0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x03, 0x39])

#empty dict containing general positioning info
GPS_POS_DICT = dict({'t': 0.0, 'UtcTime': "000000.00", 'Status': 'N', 'Latitude': 100.0, \
	'Longitude': 190.0, 'SpeedKts': -1.0, 'CourseDeg': -1.0, 'UtcDate': "000000", \
	'MVar': 0.0, 'Mode': 'N', 'FixStatus': -1, 'NoSats': -1, 'HDOP': 100.0, \
	'Alt': -1.0, 'AltRef': -1.0, 'DiffAge': 0.0, 'DGPStation': 0.0})

class UartGps:
	def __init__(self, uart_id = GPS_UART_ID, rx_pin = GPS_RX_PIN, \
	tx_pin = GPS_TX_PIN, baudrate = GPS_BAUDRATE, autostart = False, \
	uardu=None, raw_print=False):
		self.uart_id = uart_id
		self.rx_pin = rx_pin
		self.tx_pin = tx_pin
		self.baudrate = baudrate
		self.uardu = uardu
		self.uart = machine.UART(self.uart_id, tx=self.tx_pin,rx=self.rx_pin)
		self.uart_initialized = False
		self.raw_print = raw_print
		self.timer = machine.Timer(GPS_TIMER_ID)
		self.paused = False
		self.pos_dict = GPS_POS_DICT.copy()
		if autostart:
			self.start()
		pass
	
	def start(self):
		self._initialize_uart()
		self._disable_sentences()
		self._set_freq(5)
		self.timer.init(period=200, callback=self._timed_cb)
		pass
	
	def pause(self):
		if self.paused:
			self.timer.init(period=200, callback=self._timed_cb)
			self.paused = False
		else:
			self.timer.deinit()
			self.paused = True
		pass
	
	def stop(self):
		self.timer.deinit()
		self._deinitialize_uart()
		pass
	
	def _timed_cb(self, t_obj):
		for i in range(GPS_ENABLED_SENTENCES):
			rln = str(self._non_blocking_readln())[2:-5]
			parse_nmea_sentence(rln, self.pos_dict)
			#print(self.pos_dict)
		self.pos_dict['t'] = utime.ticks_ms()
		self._print_on_repl()
		pass
	
	# prints contents of position dict on REPL
	def _print_on_repl(self):
		#s2send = "{t:.1f}\tGPS\t{UtcDate:s},{UtcTime:s},{Latitude:.10f},{Longitude:.10f},{Alt:.4f},{SpeedKts:.4f},{CourseDeg:.4f},{HDOP:.2f},{NoSats:d}".format(**self.pos_dict)
		s2send = "{t:.1f}\tGPS\t{UtcDate:s},{UtcTime:s},{Latitude:.6f},{Longitude:.6f},{Alt:.2f},{SpeedKts:.2f},{CourseDeg:.2f},{HDOP:.2f},{NoSats:d}".format(**self.pos_dict)
		if self.raw_print:
			print(s2send)
		if not (self.uardu is None):
			self.uardu.send_str(s2send)
		pass

	def _initialize_uart(self):
		self.uart.init(baudrate=self.baudrate,bits=8,parity=None,stop=1,tx=self.tx_pin,rx=self.rx_pin,timeout=0) #no timeout to try avoid locking.
		self.uart_initialized = True
		pass
	
	#TODO: Check if writing operations succeeded.
	def _disable_sentences(self):
		print("Disabling undesired sentences.")
		error_state = False
		nw = self.uart.write(GPS_CMD_UBLOX_DISABLE_VTG)
		#nw = self.uart.write(GPS_CMD_UBLOX_DISABLE_GGA)
		nw = self.uart.write(GPS_CMD_UBLOX_DISABLE_GLL)
		nw = self.uart.write(GPS_CMD_UBLOX_DISABLE_GSV)
		nw = self.uart.write(GPS_CMD_UBLOX_DISABLE_GSA)
		if not error_state:
			print("Success!")
		else:
			print("Error!")
		pass
		
	def _set_freq(self, hzv = 5):
		print("Setting frequency to " + str(hzv) + "Hz...")
		if (hzv == 5):
			nw = self.uart.write(GPS_CMD_UBLOX_SETFREQ_5HZ)
			print("OK")
		elif (hzv == 10):
			nw = self.uart.write(GPS_CMD_UBLOX_SETFREQ_10HZ)
			print("OK")
		else:
			print("Fail: unsupported frequency!")
		pass
	
	def _deinitialize_uart(self):
		self.uart.deinit()
		self.uart_initializized = False
		pass
	
	def _readln(self):
		if self.uart_initialized:
			return self.uart.readline()
		else:
			return None
	
	def _non_blocking_readln(self):
		if self.uart_initialized:
			n_avail = self.uart.any()
			if n_avail > 0:
				return self.uart.readline()
			else:
				return None
		else:
			return None
	
	def _non_blocking_read(self):
		n_avail = self.uart.any()
		if n_avail > 0:
			return self.uart.read(n_avail)
		else:
			return None

# For now, it only supports GPRMC and GPGGA				 
def parse_nmea_sentence(line_in, pd):
	list_in = line_in.replace('*', ',').split(',')
	if list_in[0][3:] == "RMC":
		pd['UtcTime'] = list_in[1]
		if list_in[2] == 'A':
			pd['Active'] = 'A'
		else:
			pd['Active'] = 'V'
		if len(list_in[3]) > 2:
			lat = float(list_in[3][0:2]) + float(list_in[3][2:]) / 60.0
			if list_in[4] == 'N':
				pd['Latitude'] = lat
			else:
				pd['Latitude'] = -lat
		else:
			pd['Latitude'] = 100.0
		if len(list_in[5]) > 2:
			lon = float(list_in[5][0:3]) + float(list_in[5][3:]) / 60.0
			if list_in[6] == 'E':
				pd['Longitude'] = lon
			else:
				pd['Longitude'] = -lon
			pd['SpeedKts'] = float(list_in[7])
		else:
			pd['Longitude'] = 190.0
		if len(list_in[7]) > 0:
			pd['SpeedKts'] = float(list_in[7])
		else:
			pd['SpeedKts'] = -1.0
		if len(list_in[8]) > 0:
			pd['CourseDeg'] = float(list_in[7])
		else:
			pd['CourseDeg'] = -1.0
		pd['UtcDate'] = list_in[9]
		if len(list_in[10]) > 0:
			pd['MVar'] = float(list_in[10])
		else:
			pd['MVar'] = 0.0
		if len(list_in[11]) > 0:
			pd['Mode'] = list_in[11]
		else:
			pd['Mode'] = 'N'
	elif list_in[0][3:] == "GGA":
		pd['UtcTime'] = list_in[1]
		if len(list_in[2]) > 2:
			lat = float(list_in[2][0:2]) + float(list_in[2][2:]) / 60.0
			if list_in[3] == 'N':
				pd['Latitude'] = lat
			else:
				pd['Latitude'] = -lat
		else:
			pd['Latitude'] = 100.0
		if len(list_in[4]) > 2:
			lon = float(list_in[4][0:3]) + float(list_in[4][3:]) / 60.0
			if list_in[5] == 'E':
				pd['Longitude'] = lon
			else:
				pd['Longitude'] = -lon
		else:
			pd['Longitude'] = 190.0
		if len(list_in[6]) > 0:
			pd['FixStatus'] = int(list_in[6])
		else:
			pd['FixStatus'] = -1
		pd['NoSats'] = int(list_in[7])
		if len(list_in[8]) > 0:
			pd['HDOP'] = float(list_in[8])
		else:
			pd['HDOP'] = 100.0
		if len(list_in[9]) > 0:
			pd['Alt'] = float(list_in[9])
		else:
			pd['Alt'] = -1.0
		if len(list_in[11]) > 0:
			pd['AltRef'] = float(list_in[9])
		else:
			pd['AltRef'] = -1.0
		
	pass


