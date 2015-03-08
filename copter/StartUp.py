#!/usr/bin/python

import sys, getopt
import thread
import time
import logging
sys.path.append('.')
import RTIMU
import os.path
import math
from Adafruit_PWM_Servo_Driver import PWM
import socket

def ReadSensor(status):
	SETTINGS_FILE = "RTIMULib"
	
	#print("Using settings file " + SETTINGS_FILE + ".ini")
	#if not os.path.exists(SETTINGS_FILE + ".ini"):
	  #print("Settings file does not exist, will be created")
	
	s = RTIMU.Settings(SETTINGS_FILE)
	imu = RTIMU.RTIMU(s)
	
	#print("IMU Name: " + imu.IMUName())
	
	if (not imu.IMUInit()):
	    #print("IMU Init Failed");
	    sys.exit(1)
	#else:
	    #print("IMU Init Succeeded");
	
	poll_interval = imu.IMUGetPollInterval()
	#print("Recommended Poll Interval: %dmS\n" % poll_interval)
	logging.debug('ReadSensor, Thread started')
	while status["start"]:
		if imu.IMURead():
			# x, y, z = imu.getFusionData()
			tmpgyrox = math.degrees(imu.getIMUData()["fusionPose"][0])
			tmpgyroy = math.degrees(imu.getIMUData()["fusionPose"][1])
			tmpgyroz = math.degrees(imu.getIMUData()["fusionPose"][2])
			status["gyro-x"] = tmpgyrox
			status["gyro-y"] = tmpgyroy
			status["gyro-z"] = tmpgyroz
			if (status["gyro-y"] > 35) or status["gyro-y"] < -35: 
				status["start"] = 0
				print "Emergency stop!"

		
		#time.sleep(0.001)
		#logging.debug("Sensor Loop: x: " + str(status["gyro-x"]) + " y: " + str(status["gyro-y"]) + " z: " + str(status["gyro-z"]))
		#GPS
		#altitude by barometric sensor
		#read altitude by google api
		#roll & pitch
		#yaw compass
		# read distance sensor
		# set ready preflight check 1
		# read sonsors for ~30sec if no change set ready for flight 1
		# update sonsors roll & pitch every 1ms
		# update gps barometric sensor, yaw, distane sensor 100ms
		# update altitude over ground every 1sec
		# if something missing, set emergency state (hold position as possible)
	return


def PrintData(status):
	logging.debug('ReadSensor, Thread PrintData')
	while status["start"]:
		time.sleep(1)
		logging.debug('PrintData, Loop')
		#for i in status:
			#print str(i) + " :" + str(status[i])

def CalcProps(status):
	servoMin = 230  # Min pulse length out of 4096
	servoMax = 650  # Max pulse length out of 4096
	print "CalcProps gestartet"
	time.sleep(1)
	gyroy = [0,0]
	try:
		while status["start"]:
			del gyroy[0]
			gyroy.append(status["gyro-y"])
			y = 0
			for i in gyroy:
				y += i
			y /= len(gyroy)
			#make the counterforce much less powerfull if negative
			if y > status["gyro-y"]:
				#y = 0	
				y = status["gyro-y"] / 4
			else:
				y /= 2	

			valuey = y

			#prevent to much force
			if valuey > 4:
				valuey = 4
			if valuey < -4:
				valuey = -4

			if status["throttle"] < 0:
				status["throttle"] = 0

			prop1 = (valuey * -1) + servoMin + status["throttle"]
			prop2 = valuey + servoMin + status["throttle"]
			prop3 = (valuey * -1) + servoMin + status["throttle"]
			prop4 = valuey + servoMin + status["throttle"]
			status["PropValue"] = [prop1, prop2, prop3, prop4]
			logging.debug("valuey: " + str(valuey) + " ,resulting to prop2: " + str(prop2))
			#logging.debug( "1: " + str(status["PropValue"][0])  + " 2: " + str(status["PropValue"][1])+ " 3: " + str(status["PropValue"][2]) + " 4: " + str(status["PropValue"][3]))
			time.sleep(0.01)
		return
	except:
		print "Fuck!!"
		raise

def ControlProps(status):
	logging.debug('ReadSensor, Thread ControlProps')
	pwm = PWM(0x40)
	pwm.setPWMFreq(50)                        # Set frequency to 60 Hz
	print "Starting Control of Props according Input"
	time.sleep(2)
	print "Starting Loop to Control Sleep"
	try:
		while status["start"]:
			if status["debug"]:
				print("Propeller 1:" + str(status["PropValue"][0]) + " Propeller 2:" + str(status["PropValue"][1]) + " Propeller 3:" + str(status["PropValue"][2]) + " Propeller 4:" + str(status["PropValue"][3]))
				time.sleep(0.1)
			else:
				time.sleep(0.02) #makes no sence to control prop more often with 50Hz
				#pwm.setPWM(0, 0, int(status["PropValue"][0]))
				pwm.setPWM(1, 0, int(status["PropValue"][1]))
				#pwm.setPWM(2, 0, int(status["PropValue"][2]))
				pwm.setPWM(3, 0, int(status["PropValue"][3]))

		print "Stopping Motors"
		pwm.setPWM(0, 0, 180)
		pwm.setPWM(1, 0, 180)
		pwm.setPWM(2, 0, 180)
		pwm.setPWM(3, 0, 180)
	except KeyboardInterrupt:
		pwm.setPWM(0, 0, 180)
		pwm.setPWM(1, 0, 180)
		pwm.setPWM(2, 0, 180)
		pwm.setPWM(3, 0, 180)
		print "Reset Servo!!"
		raise
	except:
		raise
	return

def ReadInput(status):
	logging.debug('ReadInput, Thread ReadInput')
	while 1:
		logging.debug('ReadInput, Loop')
		input = raw_input("Please insert your command: ")
		print "Got command: " + str(input)


		if input == "stop":
			status["start"] = 0
		elif input == "t":
			throttle = raw_input("Insert throttle position: ")
			print "Got throttle: " + str(input)
			status["throttle"] = int(throttle)
		elif input == "throttle":
			throttle = raw_input("Insert throttle position: ")
			print "Got throttle: " + str(input)
			status["throttle"] = int(throttle)
		elif input == "w":
			status["throttle"] += 1
		elif input == "s":
			status["throttle"] -= 1
		elif input == "test":
			status["throttle"] = 10
			print "Set Trottle to 10"
			time.sleep(0.5)
			status["throttle"] = 100
			print "Set Trottle to 100"
			time.sleep(0.5)
			status["throttle"] = 10
			print "Set Trottle to 10"
			time.sleep(0.5)
			status["throttle"] = 100
			print "Set Trottle to 100"
			time.sleep(0.5)
			status["throttle"] = 10
			print "Set Trottle to 10"
			time.sleep(0.5)
			status["throttle"] = 100
			print "Set Trottle to 100"
			time.sleep(0.5)
			status["throttle"] = 10
			print "Set Trottle to 10"
			time.sleep(1)
		elif input == "esc-reset":
			print "Disconnect ESC from Controller and power"
			print "Press 'y' when done"
			input = raw_input("Done?: ")
			status["start"] = 0
			time.sleep(2)
			if input == "y":
				pwm = PWM(0x40)
				pwm.setPWMFreq(50)                        # Set frequency to 60 Hz
				print "now enter the % of throttle you need"
				while 1:
					try:
						foo = raw_input("procent: ")
						if int(foo) > 100:
							break
						value = (int(foo) * 450 / 100) + 150
						pwm.setPWM(0, 0, value)
						pwm.setPWM(1, 0, value)
						pwm.setPWM(2, 0, value)
						pwm.setPWM(3, 0, value)
						del foo
					except:
						print "Try again"
				print "Done...."
			
def NetworkSoket(status):
	logging.debug('Starting Up Networks socket')
	HOST = ''   # Symbolic name, meaning all available interfaces
	PORT = 16016 # Arbitrary non-privileged port
	 
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	logging.debug('Socket Created')
	 
	#Bind socket to local host and port
	try:
		s.bind((HOST, PORT))
	except socket.error as msg:
		logging.debug('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
		status["start"] = 0
		raise
	     
	print 'Socket bind complete'
	#Start listening on socket
	s.listen(10)
	logging.debug('Socket now listening')
	 
	#now keep talking with the client
	conn, addr = s.accept()
	logging.debug('Connected with ' + addr[0] + ':' + str(addr[1]))
	while 1:
		#Receiving from client
		data = conn.recv(1024)
		data = data.rstrip()
		print data
		if not data:
		    break
		reply = "invalid\n\n"
		if data == "stop":
			reply = "OK...\n\n"
			s.close()
			status["start"] = 0
		if data == "status":
			reply = "Running: " + str(status["start"]) + "\nPropeller 1:" + str(status["PropValue"][0]) + "\nPropeller 2:" + str(status["PropValue"][1]) + "\nPropeller 3:" + str(status["PropValue"][2]) + "\nPropeller 4:" + str(status["PropValue"][3]) + "\n...End\n\n"
		conn.sendall(reply)

	S.close()

def CAM(status):
	logging.debug('CAM, Thread ReadInput')
	while status["start"]:
		time.sleep(1)
		logging.debug('CAM, Loop')
	return

status={}
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='/var/log/copter.log',level=logging.DEBUG)
logging.debug('Main: Started Up')
status["debug"] = 0
status["start"] = 1
status["throttle"] = 15
# check stare of vpn tunnel MUST be online

try:
	thread.start_new_thread( ReadSensor, (status, ) )
	thread.start_new_thread( CalcProps, (status, ) )
	thread.start_new_thread( PrintData, (status, ) )
	thread.start_new_thread( ControlProps, (status, ) )
	thread.start_new_thread( ReadInput, (status, ) )
	thread.start_new_thread( CAM, (status, ) )
	thread.start_new_thread( NetworkSoket, (status, ) )
	while status["start"]:
		time.sleep(5)
	time.sleep(1)
	quit()
except:
	logging.warning('Main: WARNNG a thread gave back some error')

while 1:
   pass
