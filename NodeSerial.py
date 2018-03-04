#Serial Communication to Node Libraryr
#Handles messages being sent between Raspberry Pi and Node
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

        # list of serial ports
        self.serial_list = [None]*num_nodes

        # SOM and EOM
        # this means that bytes 0xfe and 0xff
        # are OFF LIMITS for any other purpose!
        self.SOM_list = [b'\xff',b'\xff'] # beginning of every message
        self.EOM_list = [b'\xfe',b'\xfe'] # ending of every message

        # password sent by node
        self.password = self.SOM_list + [b'\x04',b'\x00', b'\x00', b'\x01'] + self.EOM_list
        
        self.baud_rate = 57600

        self.registerSerialPorts()

    def registerSerialPorts(self):
        
        # searches serial ports to find attached nodes
        # constructs self.node_addresses and self.serial_list

        prefix = '/dev/ttyACM' # linux serial port prefix, append integer for address
        port_max = 100 # maximum number of ports to check
        port_timeout_limit = 10 # wait time in seconds to receive password from Teensy
        
        print("Beginning serial port registration")

        # find all nodes
        port_number = 0
        last_address_found = ''
        last_port_found = None
        num_registered_nodes = 0
        for node in range(self.num_nodes):
            print("Looking for node " + str(node) + "/" + str(self.num_nodes))

            # try to open serial ports until a node is found
            device_found = False
            while device_found == False and port_number < port_max:

                try:
                    # try to open port
                    # the try block will exit after this line if a serial device is not found
                    ser = serial.Serial(prefix + str(port_number), self.baud_rate)

                    print("Serial device found on " + prefix + str(port_number))
                    
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
                            if incoming_byte == self.password[password_index]:
                                # if so, we increase index to check for next byte on next loop
                                password_index += 1
                            else:
                                # else, start looking from beginning
                                password_index = 0
                                print("here")

                        if password_index == len(self.password):
                            print("got password")
                            # we have received the password!! This is a node!
                            password_received = True
                            device_found = True
                            last_address_found = prefix + str(port_number)
                            last_port_found = ser

                        if time.time() - start_time > port_timeout_limit:
                            # we have waited long enough, it is (probably) not a node
                            timeout = True
                    print(password_index)
                                   
                    
                except SerialException:
                    # there is no serial device on this port
                    # do nothing
                    pass

                port_number += 1

            if device_found == True:

                # if we found a device, register it with system
                self.node_addresses[node] = last_address_found
                self.serial_list[node] = last_port_found

                # send password back to Teensy
                for b in self.password:
                    self.serial_list[node].write(b)

                # ditch extra password bytes in buffer, we don't need them anymore
                self.serial_list[node].reset_input_buffer()

                num_registered_nodes =+ 1
            else:
                # otherwise, we have hit port max
                print("Port maximum (" + str(port_max) + ") reached: " + str(port_number<port_max))

        # print out info for registered nodes
        print(str(num_registered_nodes) + " out of " + str(self.num_nodes) + " nodes found ")
        for node in range(num_registered_nodes):
            print("Node " + str(node) + "- Address: " + self.node_addresses[node])
        

    def waitUntilSerialPortsOpen(self):
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

        for i in range(len(self.serial_list)):
            sendMessage(INSTRUCT_CODE_GET_TEENSY_ID)
            code, tid = checkIncomingMessageFromNode(i)

    def checkIncomingMessageFromNode(self, node_number):

        #Check if port has minimum message length in buffer
        if self.serial_list[node_number].inWaiting() >= 11:

            #Serial port for Target Node
            ser = self.serial_list[node_number]

            #Check for Start of Message
            for i in range(len(self.SOM_list)):
                current_SOM = ser.read()
                if current_SOM != self.SOM_list[i]:
                    print("SOM Not Found")
                    print(current_SOM)
                    return "error", "none"

            #Teensy IDs, TODO: Use these for validation
            t1 = ser.read()
            t2 = ser.read()
            t3 = ser.read()

            # received_tid = ((t1 << 16) | (t2 << 8)) | t3
            #Read in Length and Code
            message_length = ser.read()
            message_code = ser.read()

            #Find amount of bytes to read and store into data list
            num_bytes_to_receive = int.from_bytes(message_length, byteorder='big') - 8 - len(self.EOM_list);
            incoming_data = []

            if num_bytes_to_receive == 0:
                for i in range(len(self.EOM_list)):
                    current_EOM = ser.read()
                    if current_EOM != self.EOM_list[i]:
                        print("EOM Not Found")
                        ser.flushInput()
                        return "error", "none"

                return message_code, []

            else:

                if ser.inWaiting() >= num_bytes_to_receive:
                    for i in range(num_bytes_to_receive):
                        incoming_data.append(ser.read())

            #Check for End of Message
                for i in range(len(self.EOM_list)):
                    current_EOM = ser.read()
                    if current_EOM != self.EOM_list[i]:
                        print("EOM Not Found")
                        ser.flushInput()
                        return "error", "none"

            #Returns identifier byte for message code and relevant data list
                return message_code, incoming_data


        else:

            return "none", "none"

    def sendMessage(self, outgoing_message_code, outgoing_data, node_number):
            # input:
            # outgoing_message_code: bytes object of length 1
            # outgoing_data: list of ints (can be empty), ASSUMES EACH ITEM CAN BE TRANSFORMED INTO ONE SINGLE BYTE EACH
            # node_number: int

            # first determine number of bytes to send
        messageLength = (len(self.SOM_list) # SOM
                      + 3 # teensy id
                      + 1 # length byte
                      + len(outgoing_message_code) # code
                      + len(outgoing_data) # outgoing data bytes
                      + len(self.EOM_list)) # EOM

            # select serial port
        ser = self.serial_list[node_number]

        # send SOM (3 bytes)
        for SOM in self.SOM_list:
            ser.write(SOM)

        # send teensy id (3 bytes)
        TID_list = list(self.teensy_ids[node_number].to_bytes(3, byteorder='big'))
        for TID in TID_list:
            ser.write(bytes([TID]))

        # send length (1 byte)
        ser.write(bytes([messageLength]))

        # send code (1 bytes)
        ser.write(outgoing_message_code)

        # send data
        for OUT in outgoing_data:
            ser.write(bytes([OUT]))

        # send EOM (3 bytes)
        for EOM in self.EOM_list:
            ser.write(EOM)

        #Print All Bytes

        # print(self.SOM_list, end=" [")
        # for tid in TID_list:
        #     print(bytes([tid]), end=", ")
        # print("] [", end="")
        # print(bytes([messageLength]), end="")
        # print("] [", end="")
        # print(outgoing_message_code, end="")
        # print("] [", end="")
        # for out in outgoing_data:
        #     print(bytes([out]), end=", ")
        # print("]", end="")
        # print(self.EOM_list)
        # print(int.from_bytes(TID_list, byteorder='big'))
        # print("\n")

        print("Sending to " + str(self.node_addresses[node_number]) + " " + str(outgoing_message_code) + " " + str(outgoing_data))

if __name__ == '__main__':

    num_nodes = 1

    S = NodeSerial(num_nodes)

    while True:
        try:
            pass
        except KeyboardInterrupt:
            print("Closing Main Program and Serial Ports")

            for i in range(len(S.serial_list)):
                print ("Stopping" + str(S.node_addresses[i]))
                S.serial_list[i].close()

            print("Completed")
            break
