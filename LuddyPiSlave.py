# LuddyPiSlave.py - LASG/PBAI
# Created by Adam Francey, March 16 2018
# This code resides on each Raspberry Pi within Amatria at Luddy Hall
# Reads serial data from each connected node and sends received bytes to the laptop over UDP
# Reads UDP packets from the laptop and sends it to the appropriate node

import NodeSerial # LASG library for reading serial ports
import PiUDP # LASG library for UDP communication
from serial import SerialException

IP_LAPTOP = '192.168.2.23' #IP address of master laptop
PORT_RECEIVE = 4001 # receive input on this port
PORT_SEND = 4000 # send output on this port

# number of nodes we expect to be connected to this Pi
num_nodes = 1

# object for managing serial communication to and from each node
serial_manager = NodeSerial.NodeSerial(num_nodes)

# object for managing UDP communication to and from master laptop
UDP_manager = PiUDP.PiUDP(IP_LAPTOP, PORT_RECEIVE, PORT_SEND)

# run forever
while True:

    try:

        # check nodes for a message
        for i in range(num_nodes):
            code, data, tid, raw_bytes = serial_manager.checkIncomingMessageFromNode(i)
            if code != 'error':
                # if we get a message, pass it on to the laptop
                UDP_manager.send_bytes(raw_bytes)

        # check for waiting message
        if UDP_manager.bytes_waiting:
            code, data, tid = UDP_manager.decode_bytes(UDP_manager.data_bytes)
            node_number = serial_manager.getNodeNumberFromId(tid)
            serial_manager.sendMessage(code, data, node_number)
            UDP_manager.bytes_waiting = False

    # catch serial port errors
    except SerialException:
        print("SerialException, closing serial ports")
        serial_manager.close()
        break

    # catch serial port errors
    except IOError:
        print("IOError, closing serial ports")
        serial_manager.close()
        break
   
    # pressing ctrl-c closes the program
    except KeyboardInterrupt:
        print("Closing Main Program and Serial Ports")
        serial_manager.close()
        UDP_manager.close()
        print("Completed, Goodbye!")
        break

    
        

    
            
        



