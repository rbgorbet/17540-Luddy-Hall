# LuddyPiSlave.py - LASG/PBAI
# Created by Adam Francey, March 16 2018
# This code resides on each Raspberry Pi within Amatria at Luddy Hall
# Reads serial data from each connected node and sends received bytes to the laptop over UDP
# Reads UDP packets from the laptop and sends it to the appropriate node

import NodeSerial # LASG library for reading serial ports
import PiUDP # LASG library for UDP communication
from serial import SerialException
import queue

# instruction codes
REQUEST_TEENSY_IDS = b'\x01' # send back ids of all connected teensies

# code handlers
def handle_REQUEST_TEENSY_IDS():
    SOM = b'\xff\xff'
    tid = b'\x00\x00\x00' # if teensy ID is \x00\x00\x00 then raspberry pi knows this message is for itself
    length = bytes([serial_manager.num_nodes*3])
    REQUEST_TEENSY_IDS = b'\x01'
    data_bytes = b''
    for teensy in range(serial_manager.num_nodes):
        data_bytes += serial_manager.teensy_ids_bytes[teensy]
    EOM = b'\xfe\xfe'
    raw_bytes = SOM + tid + length + REQUEST_TEENSY_IDS + data_bytes + EOM
    UDP_manager.send_bytes(raw_bytes)

IP_LAPTOP = '192.168.2.22' # CHANGE THIS TO IP OF MASTER LAPTOP
PORT_RECEIVE = 4001 # receive input on this port
PORT_SEND = 4000 # send output on this port

# object for managing serial communication to and from each node
serial_manager = NodeSerial.NodeSerial()

# object for managing UDP communication to and from master laptop
UDP_manager = PiUDP.PiUDP(IP_LAPTOP, PORT_RECEIVE, PORT_SEND)

# run forever
while True:

    try:

        # check for serial message from nodes
        for i in range(serial_manager.num_nodes):
            code, data, tid, raw_bytes = serial_manager.checkIncomingMessageFromNode(i)
            if code != 'error':
                # if we get a message, pass it on to the laptop
                UDP_manager.send_bytes(raw_bytes)

        # check for UDP message from laptop
        try:
            # get a UDP packet from the queue
            # if the queue is empty it raises queue.Empty exception
            data_bytes = UDP_manager.data_bytes_queue.get(block = False)
            code, data, tid = UDP_manager.decode_bytes(data_bytes)
            if tid == 0:
                # A teensy ID of 0 indicates that this message is for the Pi itself
                if code == REQUEST_TEENSY_IDS:
                    handle_REQUEST_TEENSY_IDS()
                
            else:
                # if the teensy ID is not zero this message is destined for a node
                # node_number = -1 indicates that the teensy ID in the UDP packet
                # is not recognized by this pi
                node_number = serial_manager.getNodeNumberFromId(tid)

                if node_number != -1:
                    # if the teensy is on this Pi, send the bytes to the
                    # appropriate node
                    serial_manager.sendMessage(code, data, node_number)
                    
        except queue.Empty:
            # there are no packets waiting in the queue
            pass

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

    
        

    
            
        



