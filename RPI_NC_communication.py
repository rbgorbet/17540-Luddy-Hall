
# Living Architecture Systems
# Testing code for 1 Sound Sensor Scout unit 
# test code Feb 06 Amber Ma
# 
# Will eventually add all necessary functions to become one general code that will be loaded to all NCs
# and let the NCs check their IDs and decide their types to do the corresponding demands.

# * Hardware 1 Sound Sensor Scout unit
#1 Rpi
#1 NC
#1 Teensy 3.2
#1 Teensy Audio Board
#2 Device Module B HCDM
#3 IR sensor
#1 Sound detector sensor
#6 Rebel Star LEDs
#2 Moths

#* Connection
#Sound Sensor: NC_P1_HCDM1_A = pin A17
#IR Sensor_1: NC_P1_HCDM1_B = pin 13
#RBLED1: NC_P1_HCDM1_C = pin 25
#RBLED2: NC_P1_HCDM1_D = pin 32
#RBLED3: NC_P1_HCDM1_E = pin 6
#RBLED4: NC_P1_HCDM1_F = pin 21
#RBLED5: NC_P1_HCDM1_G = pin 26
#RBLED6: NC_P1_HCDM1_H = pin 31

#IR Sensor_2: NC_P2_HCDM2_A = pin A0
#IR Sensor_3: NC_P2_HCDM2_B = pin A1
#MOTH_1: NC_P2_HCDM_E = pin A8
#MOTH_2: NC_P2_HCDM_F = pin A9

# pySerial documentation for reference
# http://pyserial.readthedocs.io/en/latest/shortintro.html
# Drag from RPI. wokring


import serial
from serial import SerialException
import time


#Initialized Serial Comm Locations based on the showing results on TyQt from RPi, will change later
node_addresses = ['/dev/ttyACM0', '/dev/ttyACM1']


numNodes = len(node_addresses) # should be same as len(self.serial_list) I believe?

#Teensy ID's in Physical Locations
#teensy_ids = [1291620, 2588460]

################################################################
#CHANGE THIS DEPENDING ON HOW MANY NODES ARE CURRENTLY CONNECTED
##############################################################
serial_list = [None,None]

# incoming action
# action we expect to recieve from the nodes
# 4 byte structure
# <SOM><LED><MOTH/LED><TRACK> 4 Bytes from NC 

#incomingDemand defined in NC 

#define ACTIVE_TRACK 0x0A //10
#define PLAY_TRACK 0X0B   //11

#define ACTIVE_MOTH 0X14  //20
#define VIB_MOTH 0X15     //21

#define ACTIVE_LED 0x1E   //30
#define ON_LED 0x1F       //31

#define NOTHING 0x64	  //100 

SOM = b'\xff' # if we receive this message, we know there should be one more byte coming that is an action

ACTIVE_TRACK = b'\x0A'

ACTIVE_MOTH = b'\x14' # To tell the RPI what type of Node controller it is

ACTIVE_LED = b'\x1E'

NITGUBG = b'\x64'

# outgoing action
# action we want to send to nodes
# 4 byte structure
# <SOM><LED><MOTH/LED><TRACK> 4 Bytes from Pi
PLAY_TRACK = b'\x0B'

VIB_MOTH = b'\x15'

ON_LED = b'\x1F'
###############################################################################
def waitUntilSerialPortsOpen():
    # only continue once we are able to open all serial ports
    print("Attempting to open serial ports...")
    while True:
        try:
            for i in range(numNodes):
                serial_list[i] = serial.Serial(node_addresses[i],9600) # does 57600 the barud rate affect LED?? IR sensor? or just sepecifially for WAV Trigger?
                serial_list[i].flush()
                serial_list[i].flushInput()
            break # if we are able to open all, break out of loop

        # catch the exception, wait one second before trying again
        except SerialException:
                time.sleep(1)
    print("Serial ports successfully opened")

###############################################################################
def checkIncomingMessageFromNode(nodeNumber):
    # Check if port has minimum message length in buffer

    # the serial port for that node
    ser = serial_list[nodeNumber]

    # check if port has a byte in the buffer
    if ser.inWaiting()>3:
        # <action> 1 byte structure

        # aread the byte
        incomingByte = ser.read()

        print("incomingByte from node" + str(nodeNumber) + "(" + node_addresses[nodeNumber] + "):" + str(incomingByte))

        if incomingByte == SOM:
            incomingAction1 = ser.read()
            print("incomingCommand from node " + str(nodeNumber) + " (" + node_addresses[nodeNumber] + "): " + str(incomingAction1))
            
            incomingAction2 = ser.read()
            print("incomingCommand from node " + str(nodeNumber) + " (" + node_addresses[nodeNumber] + "): " + str(incomingAction2))

            incomingAction3 = ser.read()
             print("incomingCommand from node " + str(nodeNumber) + " (" + node_addresses[nodeNumber] + "): " + str(incomingAction3))
            
            return incomingAction1, incomingAction2, incomingAction3
        # otherwise, we do not expect a message to be sent
        else:
            #ser.flushInput();
            # remember to flush input buffer
            return "no message"
    else:
        #ser.flushInput();
        # remember to flush input buffer
        return "no bytes"
###############################################################################
def handleIncomingAction(nodeNumber, incomingAction1, incomingAction2, incomingAction3):
     #<1.SOM><2.LED><3.MOTH/LED><4.TRACK> 4 Bytes from Pi

     if incomingAction1 == ACTIVE_LED:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(ON_LED) # this byte tells the node to expect a message byte sequence

        return 1

     elif incomingAction1 == NOTHING:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(NOTHING) # this byte tells the node to expect a message byte sequence

        return 1
    ###################################################
     if incomingAction2 == ACTIVE_LED:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(ON_LED) # this byte tells the node to expect a message byte sequence

        return 1

     elif incomingAction2 == ACTIVE_MOTH:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(VIB_MOTH) # this byte tells the node to expect a message byte sequence

        return 1

     elif incomingAction1 == NOTHING:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(NOTHING) # this byte tells the node to expect a message byte sequence

      ###################################################
      if incomingAction3 == ACTIVE_TRACK:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(PLAY_TRACK) # this byte tells the node to expect a message byte sequence

        return 1

     elif incomingAction == NOTHING:
        # send a message for each cell on each node

        ser = serial_list[nodeNumber]
        ser.write(SOM)
        ser.write(NOTHING) # this byte tells the node to expect a message byte sequence

        return 1
    ###################################################
    else
        return 0


     
###############################################################################
def main():
    while True:
        try:
            # for each node
            for nodeNumber in range(len(serial_list)):


                #check to see if that node sent a message
                incomingAction = checkIncomingMessageFromNode(nodeNumber)


                #if an action came through, hanlde it
                if incomingAction != "no message" and incomingAction != "no bytes":
                    handleIncomingAction(nodeNumber, incomingAction)

        # cath serial port errors
        except SerialException:
            print("SerialException, closing serial ports")
            for i in range(numNodes):
                serial_list[i].close()

            waitUntilSerialPortsOpen()

        # catch serial port errors
        except IOError:
            print("IOError, closing serial ports")
            for i in range(numNodes):
                serial_list[i].close()

            waitUntilSerialPortsOpen()

        # pressing ctrl-c closes the program
        except KeyboardInterrupt:
            print("stopping");

            count = 0

            for ser in serial_list:
                print("stopping serial " + str(count))
                ser.close()
                count += 1

            print("stopped")
            break
###############################################################################
if __name__ == '__main__':
    waitUntilSerialPortsOpen()
    print("Starting main program")
    main()
