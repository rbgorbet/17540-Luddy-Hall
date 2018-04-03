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

#Server
from pythonosc import dispatcher
from pythonosc import osc_server

#Client
from pythonosc import osc_message_builder
from pythonosc import udp_client

# instruction codes
TEST_LED_PIN_AND_RESPOND = b'\x00'
REQUEST_TEENSY_IDS = b'\x01'
FADE_ACTUATOR_GROUP = b'\x06'

connected_teensies = {} # connected_teensies[pi_addr] = [list of bytes objects, each element is byte sobjects for one teensy]
received_connected_teensies = {} #received_connected_teensies[pi_addr] = True or False is we received connected Teensies

#pi_ip_addresses = ['192.168.2.54', '192.168.2.24']
pi_ip_addresses = ['192.168.1.177']

pi_incoming_bytes_queue = {}
for pi_addr in pi_ip_addresses:
    pi_incoming_bytes_queue[pi_addr] = queue.Queue()
    received_connected_teensies[pi_addr] = False

tested_teensies = False


# UDP Initialization    
UDP_PORT_RECEIVE = 4000
UDP_PORT_TRANSMIT = 4001
MY_IP ='0.0.0.0'

sock_transmit = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

sock_receive = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock_receive.bind((MY_IP, UDP_PORT_RECEIVE))


def send_bytes(raw_bytes, ip_addr):
    sock_transmit.sendto(raw_bytes, (ip_addr, UDP_PORT_TRANSMIT))


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

# OSC Initialization
IP_4D_LAPTOP = '0.0.0.0'
OSC_packet_queue = queue.Queue()

# Server
OSC_PORT_RECEIVE = 3001
def receive_all_OSC(addr):
    # expect addresses like
    # /4D/code/data
    OSC_packet_queue.put(addr)
    print(addr)

def parse_and_process_OSC(addr):
    # expect messages to look like
    # /4D/code/nodeidentifier/data1/data2/data3/.../dataN/

    addr_list = addr.split('/')

    # addr[0] will always be ''
    source = addr_list[1]
    code = addr_list[2]
    node_ident = int(addr_list[3])

    data = addr_list[4:]

    print(source)
    print(code)
    print(node_ident)

    if code == 'FADE_ACTUATOR_GROUP':

        # data should look like
        # [pin1,start1,end1,time1,pin2,start2,end2,time2,...,pinN,startN,endN,timeN]
        num_actuators = len(data)/4
        pin_list = []
        start_list = []
        end_list = []
        time_list = []
        for d in range(0, len(data),4):
            pin_list.append(int(data[d]))
            start_list.append(int(data[d+1]))
            end_list.append(int(data[d+2]))
            time_list.append(int(data[d+3]))


        pi,teensy_bytes = find_pi_from_teensy_int_id(node_ident)

        print("OSC: FADE_ACTUATOR_GROUP")

        send_fade_command(pi,teensy_bytes, pin_list,start_list,end_list,time_list)


def find_pi_from_teensy_int_id(int_id):
    for pi in pi_ip_addresses:
        for teensy in connected_teensies[pi]:
            print("teensy: " + str(teensy))
            print("int id: " + str(int_id))
            
            int_from_bytes = ((teensy[0] << 16) | (teensy[1] << 8)) | teensy[2]
            print("bytes: " + str(int_from_bytes))
            if int_from_bytes == int_id:
                return pi,teensy
            
            
            
        
    

    

dispatcher = dispatcher.Dispatcher()
dispatcher.set_default_handler(receive_all_OSC)
OSC_listener = osc_server.BlockingOSCUDPServer(('0.0.0.0', OSC_PORT_RECEIVE), dispatcher)
OSC_listener_thread = threading.Thread(target=OSC_listener.serve_forever)
OSC_listener_thread.start()

# Client
OSC_PORT_TRANSMIT = 3000
OSC_client = udp_client.UDPClient(IP_4D_LAPTOP, OSC_PORT_TRANSMIT)
def send_OSC_to_4D(addr):
    msg = osc_message_builder.OscMessageBuilder(address = addr)
    msg = msg.build()
    OSC_client.send(msg)



# UDP message handlers
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
    length = b'\x01' # data is only number of blinks
    data = b'\x05' # blink 20 times
    EOM = b'\xfe\xfe'
    print("Sending TEST_LED_PIN_AND_RESPOND to all connected Teensies")
    for pi in pi_ip_addresses:
        for teensy in connected_teensies[pi]:
            tid = teensy
            raw_bytes = SOM + tid + length + TEST_LED_PIN_AND_RESPOND + data + EOM
            send_bytes(raw_bytes, pi)


def send_fade_command_to_all(pin_list, start_list, end_list, time_list):

    fade_time = 2000
    fade_hi = (fade_time >> 8) & 255 # high byte
    fade_lo = fade_time & 255 # low byte

    # to recover: fade_time == (fade_hi << 8) + fade_lo

    SOM = b'\xff\xff'
    length = bytes([len(pin_list)*5])
    data = b''
    for a in range(len(pin_list)):
        fade_hi =(time_list[a] >> 8) & 255 # high byte
        fade_lo = time_list[a] & 255 # low byte
        data = data + bytes([pin_list[a], start_list[a], end_list[a],fade_hi, fade_lo])
    EOM = b'\xfe\xfe'
    print("Sending FADE_ACTUATOR_GROUP to all connected Teensies")
    for pi in pi_ip_addresses:
        for teensy in connected_teensies[pi]:
            tid = teensy
            raw_bytes = SOM + tid + length + FADE_ACTUATOR_GROUP + data + EOM
            send_bytes(raw_bytes, pi)

def send_fade_command(pi, tid, pin_list, start_list, end_list, time_list):


    # to recover: fade_time == (fade_hi << 8) + fade_lo
    print("here")

    SOM = b'\xff\xff'
    length = bytes([len(pin_list)*5])
    data = b''
    for a in range(len(pin_list)):
        fade_hi =(time_list[a] >> 8) & 255 # high byte
        fade_lo = time_list[a] & 255 # low byte
        data = data + bytes([pin_list[a], start_list[a], end_list[a],fade_hi, fade_lo])
    EOM = b'\xfe\xfe'
    print("Sending FADE_ACTUATOR_GROUP to " + str(tid))
    raw_bytes = SOM + tid + length + FADE_ACTUATOR_GROUP + data + EOM
    send_bytes(raw_bytes, pi)
    
    

#main
debug = True
send_fade = False
listening_thread = threading.Thread(target = receive_bytes)
listening_thread.start()

time.sleep(1)
# note: int.to_bytes(362262, byteorder = 'big', length = 3) = b'\x05\x87\x16'      

request_connected_teensies()

start_time = time.time()



while True:

    # check for OSC message from 4d laptop
    try:
        incoming_OSC = OSC_packet_queue.get(block = False)
        print("Incoming OSC: " + incoming_OSC)
        if (incoming_OSC == "/4d/test"):
            test_connected_teensies()
        else:
            parse_and_process_OSC(incoming_OSC)
            
    except queue.Empty:
        pass

    for pi in pi_ip_addresses:
        # check for waiting UDP message from a Pi
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

        if debug and tested_teensies == False:
            tested_teensies = test_connected_teensies()

        if time.time() - start_time > 5 and send_fade == True:
            send_fade_command_to_all([13],[0],[50],[2000])
            time.sleep(2)
            send_fade_command_to_all([13],[50],[0],[2000])
            send_fade = False
            
            




