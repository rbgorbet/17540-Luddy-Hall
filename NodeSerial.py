# NodeSerial.py - LASG/PBAI
# Created by Kevin Lam
# Updated by Adam Francey March 16 2018
# Handles serial connection and communication between Raspberry Pi and Node

import serial
from serial import SerialException
import time

class NodeSerial():

    def __init__(self, num_nodes):

        # num_nodes: number of nodes expected to be attached
        self.num_nodes = num_nodes

        #Initialized Serial Comm Locations, To Be Rearranged Later
        self.node_addresses = ['']*num_nodes

        #Teensy ID's in Physical Locations
        self.teensy_ids = [0]*num_nodes
        self.teensy_ids_bytes = [b'\x00\x00\x00']*num_nodes

        # list of serial ports
        self.serial_list = [None]*num_nodes

        # SOM (Start Of Message)
        # EOM (End Of Message)
        # this means that bytes 0xfe and 0xff
        # are OFF LIMITS for any other purpose!
        self.SOM = b'\xff\xff' # beginning of every message
        self.EOM = b'\xfe\xfe' # ending of every message
        self.padding_byte = b'\xfd'

        # fixed message length
        self.message_length = 25

        # password sent by node
        self.password = b'\xff\xff\x04\x00\x00\x01\xfe\xfe'

        # NOTE on bytes objects
        # example
        # byte_sequence = b'\xff\xfe\xfc'
        # byte_sequence[i] = integer (ie byte_sequence[0] = 255)
        # byte_sequence[i:i+1] = bytes object (ie byte_sequence[0:1] = b'\xff')
        
        self.baud_rate = 57600

        # register all port before initializing
        self.registerSerialPorts()

    def registerSerialPorts(self):
        
        # searches serial ports to find attached nodes
        # constructs self.node_addresses and self.serial_list

        prefix = '/dev/ttyACM' # linux serial port prefix, append integer for address
        #prefix = 'COM' # windows serial port prefix, append integer for address
        port_max = 100 # maximum number of ports to check
        port_timeout_limit = 2 # wait time in seconds to receive password from Teensy
        
        print("Beginning serial port registration")

        # find all nodes
        port_number = 0
        last_address_found = ''
        last_port_found = None
        num_registered_nodes = 0
        for node in range(self.num_nodes):
            print("Looking for node " + str(node) + "/" + str(self.num_nodes))

            # try to open serial ports until a node is found
            teensy_found = False
            while teensy_found == False and port_number < port_max:

                try:
                    # try to open port
                    # the try block will exit after this line if a serial device is not found
                    ser = serial.Serial(prefix + str(port_number), self.baud_rate)

                    print("Serial device found on " + prefix + str(port_number) + ": ", end = '')
                    
                    # if this is a node, it will be continuously sending a password until it receives a password back
                    # so we check the serial port to see if we get the password sequence
                    password_received = False
                    timeout = False
                    password_index = 0
                    start_time = time.time()
                    while password_received == False and timeout == False:
                        if ser.inWaiting() > 0:
                            # check if it matches the current byte in password sequence
                            incoming_byte = ser.read()
                            if incoming_byte == self.password[password_index:password_index+1]:
                                # if so, we increase index to check for next byte on next loop
                                password_index += 1
                            else:
                                # else, start looking from beginning
                                password_index = 0

                        if password_index == len(self.password):
                            print("Teensy detected")
                            # we have received the password!! This is a node!
                            password_received = True
                            teensy_found = True
                            last_address_found = prefix + str(port_number)
                            last_port_found = ser

                        if time.time() - start_time > port_timeout_limit:
                            # we have waited long enough, it is (probably) not a node
                            print("Not a Teensy (timed out)")
                            timeout = True
                            ser.close()
                                   
                    
                except SerialException:
                    # there is no serial device on this port
                    # do nothing
                    pass

                port_number += 1

            if teensy_found == True:

                # if we found a device, register it with system
                self.node_addresses[node] = last_address_found
                self.serial_list[node] = last_port_found

                # send password back to Teensy
                self.serial_list[node].write(self.password)

                # ditch extra password bytes in buffer, we don't need them anymore
                self.serial_list[node].reset_input_buffer()

                # wait for Teensy to send back Teensy ID
                time.sleep(1)

                if (self.serial_list[node].inWaiting()>2):
                    tid1 = self.serial_list[node].read()
                    tid2 = self.serial_list[node].read()
                    tid3 = self.serial_list[node].read()
                    self.teensy_ids_bytes[node] = tid1+tid2+tid3
                    self.teensy_ids[node] = ((tid1[0] << 16) | (tid2[0] << 8)) | tid3[0]

                    

                num_registered_nodes =+ 1
            else:
                # otherwise, we have hit port max
                print("Port maximum (" + str(port_max) + ") reached: " + str(port_number>=port_max))

        # print out info for registered nodes
        print(str(num_registered_nodes) + " out of " + str(self.num_nodes) + " nodes found ")
        for node in range(num_registered_nodes):
            print("Node: " + str(node) + " - Address: " + self.node_addresses[node] + " - ID: " + str(self.teensy_ids[node]))
        

    def waitUntilSerialPortsOpen(self):
        # DEPRECATED ---------------------------------------------------------------
        # only continue once we are able to open all serial ports
        print("Attempting to open serial ports...")
        while True:
            try:
                for i in range(len(self.serial_list)):
                    self.serial_list[i] = serial.Serial(self.node_addresses[i],self.baud_rate)
                    self.serial_list[i].flush()
                    self.serial_list[i].flushInput()
                break # if we are able to open all, break out of loop

            # catch the exception, wait one second before trying again
            except SerialException:
                time.sleep(1)
        print("Serial Ports Opened Sucessfully")

    def rearrangeSerialPorts(self):
        # NEEDS TO BE UPDATED -------------------------------------------------------------
        for i in range(len(self.serial_list)):
            sendMessage(INSTRUCT_CODE_GET_TEENSY_ID)
            code, tid = checkIncomingMessageFromNode(i)

    def checkIncomingMessageFromNode(self, node_number):

        # the raw bytes coming from serial port
        raw_bytes = b''

        #Serial port for Target Node
        ser = self.serial_list[node_number]

        #Check if port has minimum message length in buffer
        if ser.inWaiting() > 6: # at lseat enough bytes for SOM, ID, length, code

            #Check for Start of Message
            for i in range(len(self.SOM)):
                current_SOM = ser.read()
                raw_bytes += current_SOM
                if current_SOM != self.SOM[i:i+1]:
                    # Fail: SOM byte missing
                    # CheckIncomingMessageFromNode fails, stop reading serial port
                    print("SOM Not Found")
                    print(current_SOM)
                    return "error", "SOM missing", None, None

            #Teensy IDs, TODO: Use these for validation
            t1 = ser.read()
            t2 = ser.read()
            t3 = ser.read()
            raw_bytes = raw_bytes + t1 + t2 + t3
            received_tid = ((t1[0] << 16) | (t2[0] << 8)) | t3[0]
            
            # Read in Length and Code
            #data_length = int.from_bytes(ser.read(), byteorder = 'big')
            data_length = ser.read()
            raw_bytes += data_length
            data_length = data_length[0] # taking first element of one-element bytes object changes the byte to int
            message_code = ser.read()
            raw_bytes += message_code

            # read data
            incoming_data = []

            if ser.inWaiting() > data_length + 1: # at least enough bytes for data and EOM

                # read in data bytes (could be no bytes)
                for i in range(data_length):
                    data_byte = ser.read()
                    incoming_data.append(data_byte)
                    raw_bytes += data_byte

                #Check for End of Message
                for i in range(len(self.EOM)):
                    current_EOM = ser.read()
                    raw_bytes += current_EOM
                    if current_EOM != self.EOM[i:i+1]:
                        # Fail: EOM byte missing
                        # stop reading serial port, all read bytes are unused (aka discarded)
                        return "error", "EOM missing", None, None
                # if we get here, we have found EOM and therefore whole message
                

                # Success: return message
                # Returns identifier byte for message code and relevant data list
                print("Received message from node " + str(node_number) + " - Code: " + str(message_code) + ", Data: " + str(incoming_data))
                return message_code, incoming_data, received_tid, raw_bytes
            else:
                return "error", "not enough data bytes", None, None


        else:

            return "error", "not enough bytes before data", None, None

    def sendMessage(self, outgoing_message_code, outgoing_data, node_number):
        # input:
        # outgoing_message_code: bytes object of length 1
        # outgoing_data: list of ints (can be empty), ASSUMES EACH ITEM CAN BE TRANSFORMED INTO ONE SINGLE BYTE EACH
        # node_number: int

        data_length = len(outgoing_data) # outgoing data bytes

        # select serial port
        ser = self.serial_list[node_number]

        # the bytes object the we will construct and send to the serial port
        message = (self.SOM # 2 bytes
                   + self.teensy_ids_bytes[node_number] # 3 bytes
                   + bytes([data_length]) # 1 byte
                   + outgoing_message_code # 1 byte
                   + bytes(outgoing_data) # len(outgoing_data) bytes
                   + self.EOM) # 2 bytes

        ser.write(message)

        print("Sending message to node " + str(node_number) + " - Code: " + str(outgoing_message_code) + ", Data: " + str(outgoing_data))

    def getNodeNumberFromId(self, teensy_id):
        for i in range(len(self.teensy_ids)):
            if teensy_id == self.teensy_ids[i]:
                return i

    def close(self):
        for i in range(self.num_nodes):
            print ("Stopping port: " + str(self.node_addresses[i]))
            self.serial_list[i].close()
        

if __name__ == '__main__':

    num_nodes = 1

    # test message
    TEST_LED_PIN_AND_RESPOND = b'\x00'
    num_blinks = 10

    S = NodeSerial(num_nodes)

    S.sendMessage(TEST_LED_PIN_AND_RESPOND, [num_blinks], 0)

    time.sleep(1) # wait a second for response
                  # this is not needed on windows
                  # is needed on Pi

    code, data, tid, raw_bytes = S.checkIncomingMessageFromNode(0)
    print("Message received from node 0 - Code: " + str(code) + ", Data: " + str(data))
    print("Raw bytes of message: " + str(raw_bytes))
    

    while True:
        try:

            # just some code to fill in this gap (this will be where main program code goes
            # for some reason if it is empty the KeyboardInterrupt doesn't get caught below
            for i in range(100):
                filler = 0
        except KeyboardInterrupt:
            print("Closing Main Program and Serial Ports")
            S.close()

            print("Completed, Goodbye!")
            break
