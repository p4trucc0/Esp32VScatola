#class to communicate with the (limited) Arduino UART

import machine
import utime

UARDUINO_PIN_TX = 16
UARDUINO_PIN_RX = 17
UARDUINO_BAUDRATE = 38400
UARDUINO_UART_ID = 1
UARDUINO_BUFFER_LIMIT = 128

class Uarduino:
	def __init__(self, pin_tx=UARDUINO_PIN_TX, pin_rx=UARDUINO_PIN_RX, \
		baudrate=UARDUINO_BAUDRATE, uartid=UARDUINO_UART_ID):
		self.pin_tx = pin_tx
		self.pin_rx = pin_rx
		self.uartid = uartid
		self.baudrate = baudrate
		self.uart = machine.UART(self.uartid, baudrate=self.baudrate, \
			tx=self.pin_tx, rx=self.pin_rx)
		self.str2send = ""
		pass
	
	def send_str(self, str_in):
		self.str2send = self.str2send + str_in + '\r\n'
		keep_writing = True
		while keep_writing:
			b = bytearray()
			b.extend(self.str2send[0:UARDUINO_BUFFER_LIMIT])
			self.str2send = self.str2send[UARDUINO_BUFFER_LIMIT:]
			self.uart.write(b)
			if len(self.str2send) < 1:
				keep_writing = False
			else:
				utime.sleep_ms(50)
		#self.uart.write('\r\n')
		pass
		
		
	

