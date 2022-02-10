from bluetooth import *
from setting import *
import time

#BLUETOOTH_PORT = 0 #some number 

class AndroidApplication(object):

    def __init__(self):
        self.serverSocket = None
        self.clientSocket = None
        self.connection = False

    def isConnected (self):
        return self.connection

    def connectToAndroid (self):
        try:
            print("Bluetooth port number : " + BLUETOOTH_PORT)
            self.serverSocket = BluetoothSocket(RFCOMM)
            self.serverSocket.bind(("", 6))
            self.serverSocket.listen(1)
            self.port = BLUETOOTH_PORT
            print ("Connection via Bluetooth RFCOMM channel %d" %BLUETOOTH_PORT)
            self.clientSocket, clientInfo = self.serverSocket.accept()

            print ("Rpi has accepted connection from ", clientInfo)
            print ("Successfully Connected to Android :)")
            self.connection = True

        except Exception as e:
            print ("Bluetooth connection has failed, waiting to reconnect. ")
            self.serverSocket.close()
            print ("Closing bluetooth connection")
            self.connection = False 

    def disconnectFromAndroid (self):
        self.clientSocket.close()
        print ("Closing bluetooth (client)")
        self.serverSocket.close()
        print ("Closing bluetooth (server)")
        self.connection = False 

    def writeToAndroid (self, msg):
        try:
            self.clientSocket.send(msg)
            print ("Sent to Android : %s" %(msg))

        except Exception as e:
            print("Error with Bluetooth, waiting for rpi to reconnect")
            self.connectToAndroid()

    def readFromAndroid (self):
        try:
            msg = self.clientSocket.recv(1024)
            msg = msg.decode('utf-8')
            print("Received from Android: %s" % str(msg))
            return (msg)

        except Exception as e:
            print("Error with Bluetooth, waiting for rpi to reconnect")
            self.connectToTablet()
