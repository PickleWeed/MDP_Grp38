#from operator import truediv
#from tkinter import E
from stm import *
from android import *
from pc import *
import threading
import os
from utils import format_for
from multiprocessing import Process, Queue

#import argparse
#import cv2
import numpy as np
#import sys
import time
#import serial
from threading import Thread
#import importlib.util


class RaspberryPi(threading.Thread):
	def __init__(self):
		self.STMThread = STMRobot()
		self.pcThread = PCInterface()
		self.androidThread = AndroidApplication()

		#True if there is path content
		self.pathReady = False

		#True if everything is ready
		self.primed = False

		self.nextPath = True

		#number of paths
		self.path_data = []

		#initalize Queue
		self.path_queue = Queue()
		#self.manual_queue = Queue()
		self.android_queue = Queue()
		self.rpi_queue = Queue()

		threading.Thread(target=self.forwarder).start()

		#get algo path from txt file
		coursePath = self.readTxtFile()

		#insert algo path to queue
		self.pathReady = self.insertPath(coursePath)

		self.serialMsg = None
		

	def printPath(self):
		while True:
			if not self.path_queue.empty():
				msg = self.path_queue.get()
				print(msg)
			else:
				break


	def insertPath(self, coursePath):
		coursePath = self.readTxtFile()
		for i in coursePath:
			#print(i)
			self.path_queue.put(i)
		#check list is not empty
		if coursePath:
			return True
		else:
			return False
		#self.printPath()
	
	def run(self):
		# PC control loop
		'''if self.pcThread.isConnected == False:
			self.pcThread.connectToPC()
		elif self.pcThread.isConnected == True and self.pcThread.threadListening == False:
			try:
				threading.Thread(target=self.readFromPC).start() # start PC socket listener thread
			except Exception as e:
				print("PC threading error: %s" %str(e))
				self.pcThread.isConnected = False'''
		# Android control loop
		if self.androidThread.isConnected == False:
				self.androidThread.connectToAndroid()
		elif self.androidThread.isConnected == True:
			if self.androidThread.threadListening == False:
				try:
					threading.Thread(target=self.readFromAndroid).start() # start Android socket listener thread
				except Exception as e:
					print("Android threading error: %s" %str(e))
					self.androidThread.isConnected = False
		# STM control loop
		if self.STMThread.isConnected == False:
			self.STMThread.connectToSTM()
		elif self.STMThread.isConnected == True:
			if self.STMThread.threadListening == False:
				try:
					threading.Thread(target=self.STMThread.readFromSTM).start() # start STM listener thread
				except Exception as e:
					print("STM threading error: %s" %str(e))
					self.STMThread.isConnected = False

	'''def multithread(self):
		#Android read and write thread
		readAndroidThread = threading.Thread(target = self.readFromAndroid, args = (), name = "read_android_thread")
		writeAndroidThread = threading.Thread(target = self.writeToAndroid, args = (), name = "write_android_thread")


		# STM read and write thread
		readSTMThread = threading.Thread(target = self.readFromSTM, args = (), name = "read_STM_thread")
		writeSTMThread = threading.Thread(target = self.writeToSTM, args = (), name = "write_STM_thread")

		# PC read and write thread
		readPCthread = threading.Thread(target = self.readFromPC, args = (), name = "read_pc_thread")
		writePCthread = threading.Thread(target = self.writeToPC, args = (), name = "write_pc_thread")

		# Set daemon for all thread      
		readPCthread.daemon = True
		writePCthread.daemon = True

		readAndroidThread.daemon = True
		writeAndroidThread.daemon = True

		readSTMThread.daemon = True
		writeSTMThread.daemon = True

		# start running the thread for PC
		readPCthread.start()

		# Start running thread for Android
		readAndroidThread.start()
 
		# Start running thread for STM
		readSTMThread.start()'''

	def disconnectAll(self):
		self.STMThread.disconnectFromSTM()
		self.androidThread.disconnectFromAndroid()
		self.pcThread.disconnectFromPC()

	def writeToAndroid(self, message):
		if self.androidThread.isConnected and message is not None:
			self.androidThread.writeToAndroid(message)

	def readFromAndroid(self):
		while True:
			androidMessage = self.androidThread.readFromAndroid()
			self.android_queue.put(androidMessage)
			if androidMessage is not None:
				print("Read From Android: ", str(androidMessage))

							
		
	def readTxtFile(self):
		with open('algofile.txt') as f:
			lines = f.read().splitlines()
			return lines

	def readFromPC(self):
		while True:
			pcMessage = self.pcThread.readFromPC()
			if len(pcMessage) > 0:
				print("Read From PC: ", pcMessage)
				#target = parsedMsg[0]
			if pcMessage == 'Hello from algo team':
				print("Load algorithm data..")
				self.pathReady = False
				continue	
			elif pcMessage != 'Goodbye from algo team':
				self.algoRun(pcMessage)
			else:
				self.pathReady = True
				self.saveToTxtFile()

	#read algorithm to txt file object
	def algoRun(self, msg):
		parsedMsg = msg.split(',')
		if parsedMsg[0] == 'ST':
			print("Reading algorithm data: ", parsedMsg)	
			self.path_data+= parsedMsg
	def saveToTxtFile(self):
		#save to txt file
		print("Saving list to txt file. Data: ", self.path_data)
		with open('algofile.txt', 'w') as filehandle:
			for listitem in self.path_data:
				filehandle.write('%s\n' % listitem)


	def writeToPC(self, message):
		if self.pcThread.isConnected and message is not None:
			self.pcThread.writeToPC(message)

	def writeToSTM (self, message):
		if (self.STMThread.isConnected and message):
			self.STMThread.writeToSTM(message)
			return True
		return False
	def readFromSTM (self):
		while True:
			self.serialMsg = self.STMThread.readFromSTM()
			if self.serialMsg is not None:
				print("Read from STM: ", str(self.serialMsg))
			

	def sentPath(self, coursePath):
		for index in range(self.indexPath,len(coursePath)):
			value = coursePath[index]
			if value == 'ST':
				continue
			self.writeToAndroid(value)
			#print(index, value)
			if value == 'w':
				self.indexPath = index+1
				break
	def forwarder(self):
		while True:
			time.sleep(0.5)
			print("Forwarder is running")
			if not self.android_queue.empty():
				msg = self.android_queue.get()
				#msg validation to be changed
				#add an or msg
				#if msg == 'R' or self.nextPath == True:
				if msg == 'START' and self.nextPath == True:
					while True:
						if not self.path_queue.empty():
							path = self.path_queue.get()
							if path == 'ST':	
								continue
							#to be removed
							#self.androidThread.writeToAndroid(path)
							elif path == 'w':
								self.nextPath = False
								break
							self.STMThread.writeToSTM(path)				
				#android msg to PC
				if msg in ["f010", "b010", "r010", "l010", "v010", "s000", "w000"]:
					print("run STM")
					self.STMThread.writeToSTM(msg)
			#if STM send finish route
			#stop when route is finish
			#STM send message to RPI when it finally stop
			# ['target']:['payload']
			#RPI received msg to take picture
			#RPI send picture to PC
			#if self.serialMsg == 'Finish Route':
				#RPI received msg to take picture
				#RPI send picture to PC
			#	print()
			#PC send to RPI image_id 'AN','String' or ['target']:['payload']
			#image_id send to android
			#repeat send android Msg 
			#nextPath = True

	

if __name__ == "__main__":
	print("Program Starting")
	main = RaspberryPi()	
	try:
		print("Starting MultiTreading")
		while True:
			#main.multithread()
			main.run()
			#Priming
			#add STM and PC is connected
			if main.primed is False and main.pathReady is True and main.androidThread.isConnected is True:
				main.primed = True
				time.sleep(3)
				main.writeToAndroid("Ready To Start")

			

	except Exception as e:
		print(str(e))
		#main.disconnectAll()
	except KeyboardInterrupt as e:
		print("Terminating program")
		#main.disconnectAll()
		print("Program Terminated")
