#!/usr/bin/python
import requests
import socket
import threading
import logging
#import mraa
import sys
import time
import time, RPi.GPIO as GPIO
# change this to the values from MCS web console
DEVICE_INFO = {
    'device_id' : 'DpwJPYEJ',
    'device_key' : '1mOUe8ZVclT0CimZ'
}

# change 'INFO' to 'WARNING' to filter info messages
logging.basicConfig(level='INFO')

heartBeatTask = None

def establishCommandChannel():
	# Query command server's IP & port
	connectionAPI = 'https://api.mediatek.com/mcs/v2/devices/DpwJPYEJ/connections.csv'
	r = requests.get(connectionAPI % DEVICE_INFO,headers = {'deviceKey' : DEVICE_INFO['device_key'],
'Content-Type' : 'text/csv'})
	logging.info("Command Channel IP,port=" + r.text)
	(ip, port) = r.text.split(',')

	# Connect to command server
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((ip, int(port)))
	s.settimeout(None)

	# Heartbeat for command server to keep the channel alive
	def sendHeartBeat(commandChannel):
		keepAliveMessage = '%(device_id)s,%(device_key)s,0' % DEVICE_INFO
		commandChannel.sendall(keepAliveMessage)
		logging.info("beat:%s" % keepAliveMessage)

	def heartBeat(commandChannel):
		sendHeartBeat(commandChannel)
		# Re-start the timer periodically
		global heartBeatTask
		heartBeatTask = threading.Timer(40, heartBeat, [commandChannel]).start()

	heartBeat(s)
	return s

def waitAndExecuteCommand(commandChannel):
	while True:
		command = commandChannel.recv(1024)
		logging.info("recv:" + command)
		# command can be a response of heart beat or an update of the LED_control,
		# so we split by ',' and drop device id and device key and check length
		fields = command.split(',')[2:]

		if len(fields) > 1:
			timeStamp, dataChannelId, commandString = fields
			if dataChannelId == 'LED_Control':
				# check the value - it's either 0 or 1
				commandValue = int(commandString)
				logging.info("led :%d" % commandValue)
				setLED(commandValue)


def setupLED():
	
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(17,GPIO.OUT)
	LEDon = GPIO.output(17, 1)
	time.sleep(1)
	LEDoff = GPIO.output(17, 0)


def setLED(state):
	if state:
		GPIO.output(17, 1)
        else:
		GPIO.output(17, 0)

if __name__ == '__main__':
	setupLED()
	channel = establishCommandChannel()
	waitAndExecuteCommand(channel)