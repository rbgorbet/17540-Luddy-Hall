# INCOMPLETE
# LuddyLaptopMaster.py - LASG/PBAI
# Created by Adam Francey, March 16 2018
# This code resides on the master laptop at Amatria in Luddy Hall
# Reads and writes UDP data to each connected Raspberry Pi
# Reads and writes OSC messages to the 4DSOUND laptop
# Coordinates global behaviour

import socket
import threading
import time
import queue

# instruction codes
TEST_LED_PIN_AND_RESPOND = b'\x00'
REQUEST_TEENSY_IDS = b'\x01'

connected_teensies = {} # connected_teensies[pi_addr] = [list of bytes objects, each element is byte sobjects for one teensy]
received_connected_teensies = {} #received_connected_teensies[pi_addr] = True or False is we received connected Teensies

pi_ip_addresses = ['192.168.2.54', '192.168.2.24']

pi_incoming_bytes_queue = {}
for pi_addr in pi_ip_addresses:
    pi_incoming_bytes_queue[pi_addr] = queue.Queue()
    received_connected_teensies[pi_addr] = False

tested_teensies = False
    
PORT_RECEIVE = 4000
PORT_TRANSMIT = 4001
MY_IP ='0.0.0.0'

sock_transmit = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

sock_receive = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock_receive.bind((MY_IP, PORT_RECEIVE))


##def send_string(MESSAGE):
##    sock_transmit.sendto(bytes(MESSAGE, 'utf-8'), (IP_PI1, PORT_TRANSMIT))
##
##
##def receive_string():
##    while True:
##        data, addr = sock_receive.recvfrom(1024) # buffer size is 1024 bytes
##        print("Received string: " + str(data, 'utf-8'))


def send_bytes(raw_bytes, ip_addr):
    sock_transmit.sendto(raw_bytes, (ip_addr, PORT_TRANSMIT))


def receive_bytes():
    while True:
        data, addr = sock_receive.recvfrom(1024) # buffer size is 1024 bytes
        pi_incoming_bytes_queue[addr[0]].put(data)
        #print("Received UDP - Address: " + addr[0] + ", Data: " + str(data))

def decode_bytes(raw_bytes):

        # teensy id
    tid_bytes = raw_bytes[2:5]
    tid =((tid_bytes[0] << 16) | (tid_bytes[1] << 8)) | tid_bytes[2]

    # number of data bytes
    length = raw_bytes[5:6][0]

    # instruction code
    code = raw_bytes[6:7]

    # data in bytes
    data_bytes = raw_bytes[7:7+length]

    #convert data to list of ints
    data = []
    for d in range(length):
        data.append(data_bytes[d])

    return code, data, tid


def request_connected_teensies():
    

    # ask for connected Teensies
    SOM = b'\xff\xff'
    tid = b'\x00\x00\x00' # if teensy ID is \x00\x00\x00 then raspberry pi knows this message is for itself
    length = b'\x00' # no data
    EOM = b'\xfe\xfe'
    raw_bytes = SOM + tid + length + REQUEST_TEENSY_IDS + EOM
    for pi in pi_ip_addresses:
        send_bytes(raw_bytes, pi)

def get_connected_teensies(data):
    # data is list of ints, change back to bytes
    data_bytes = bytes(data)
    teensy_ids_bytes = []
    int_ids = []
    for i in range(0, len(data), 3):
        id_bytes = data_bytes[i:i+1] + data_bytes[i+1:i+2] + data_bytes[i+2:i+3]
        teensy_ids_bytes.append(id_bytes)
        int_id = ((data_bytes[i] << 16) | (data_bytes[i+1] << 8)) | data_bytes[i+2]
        int_ids.append(int_id)
        print(str(int_id) + " (" + str(id_bytes) + ")")
    return teensy_ids_bytes

def test_connected_teensies():
    # checks to see if we have collected Teensy IDs from connected Pis
    # if so, send a TEST command to each teensy and returns True
    # if not, exits and returns False
    for pi in pi_ip_addresses:
        if received_connected_teensies[pi] == False:
            return False

    # test connected Teensies
    SOM = b'\xff\xff'
    length = b'\x01' # no data
    data = b'\x05' # blink 5 times
    EOM = b'\xfe\xfe'
    print("Sending TEST_LED_PIN_AND_RESPOND to all connected Teensies")
    for pi in pi_ip_addresses:
        for teensy in connected_teensies[pi]:
            tid = teensy
            raw_bytes = SOM + tid + length + TEST_LED_PIN_AND_RESPOND + data + EOM
            send_bytes(raw_bytes, pi) 
    

#main
listening_thread = threading.Thread(target = receive_bytes)
listening_thread.start()

time.sleep(1)
# note: int.to_bytes(362262, byteorder = 'big', length = 3) = b'\x05\x87\x16'      

request_connected_teensies()



while True:

    for pi in pi_ip_addresses:
        # check for waiting message
        try:
            # try to get a packet from the queue
            # raises queue.Empty exception if no packets waiting in queue
            incoming_bytes = pi_incoming_bytes_queue[pi].get(block = False)
            code, data, tid = decode_bytes(incoming_bytes)
            if code == REQUEST_TEENSY_IDS:
                # response from asking for Teensy IDs
                print("Received UDP - Address: " + pi + ", Packet: " + str(incoming_bytes))
                print("Decoded Message:")
                print("Teensies connected to pi at address " + pi + ": ")
                connected_teensies[pi] = get_connected_teensies(data)
                received_connected_teensies[pi] = True

            elif code == TEST_LED_PIN_AND_RESPOND:
                print("Teensy response from " + str(tid) + " on " + pi + ": " + str(data))
        
        except queue.Empty:
            pass

        if tested_teensies == False:
            tested_teensies = test_connected_teensies()




