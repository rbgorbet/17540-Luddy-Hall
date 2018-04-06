# INCOMPLETE
# LuddyLaptopMaster.py - LASG/PBAI
# Created by Adam Francey, March 16 2018
# This code resides on the master laptop at Amatria in Luddy Hall
# Reads and writes UDP data to each connected Raspberry Pi
# Reads and writes OSC messages to the 4DSOUND laptop
# Coordinates global behaviour



# CHANGE THESE IP ADDRESSES
IP_4D_LAPTOP = '0.0.0.0'
pi_ip_addresses = ['192.168.1.177']

import socket
import threading
import time
import queue
import DeviceLocator
import FutureActions

device_locator = DeviceLocator.DeviceLocator()
future_manager = FutureActions.FutureActions() 

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
IR_TRIGGER = b'\x07'

connected_teensies = {} # connected_teensies[pi_addr] = [list of bytes objects, each element is byte sobjects for one teensy]
received_connected_teensies = {} #received_connected_teensies[pi_addr] = True or False if we received connected Teensies

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
OSC_packet_queue = queue.Queue()

# Server
OSC_PORT_RECEIVE = 3001
def receive_all_OSC(addr, *values):
    # expect addresses like
    # /4D/code/data
    OSC_packet_queue.put([addr, values])
    print(addr)

def parse_and_process_OSC(incoming_OSC):

    addr = incoming_OSC[0]
    data = incoming_OSC[1]  

    addr_list = addr.split('/')

    # addr[0] will always be ''
    source = addr_list[1]
    code = addr_list[2]
    identifier = addr_list[3]

    print(source)
    print(code)
    print(identifier)

    if code == 'FADE_ACTUATOR_GROUP':
        if "SSS" in identifier:

            # message format
            # /4D/FADE_ACTUATOR_GROUP/SSS1 RS1 0 50 2000 RS2 50 25 2000 MOTH3 50 0 6000
            
            SSS_num = int(identifier[3])
            node_id = device_locator.SSS[SSS_num - 1][-1] #moths/RS on last node in SSS
            pin_list = []
            start_list = []
            end_list = []
            time_list = []
            for d in range(0, len(data),4):
                actuator_id = data[d]
                if "MOTH" in actuator_id:
                    index = int(actuator_id[4])
                    pin = device_locator.Moths[node_id][index - 1]
                elif "RS" in actuator_id:
                    index = int(actuator_id[2])
                    pin = device_locator.Rebel_Star[node_id][index - 1]
                
                pin_list.append(pin)
                start_list.append(data[d+1])
                end_list.append(data[d+2])
                time_list.append(data[d+3])
            print("FADE_ACTUATOR_GROUP SSS")
            pi,teensy_bytes = find_pi_from_teensy_int_id(node_id)
            send_fade_command(pi,teensy_bytes, pin_list,start_list,end_list,time_list)            
            
        elif "SPHERE" in identifier:

            # message format
            # /4D/FADE_ACTUATOR_GROUP/SPHERE1 RS1 0 50 2000 RS2 50 25 2000 MOTH3 50 0 6000
        
            sphere_num = int(identifier[6])
            node_ids = device_locator.SphereUnit[sphere_num - 1]
            
            # data should look like
            # (actuator_id1,start1,end1,time1,actuator_id2,start2,end2,time2,...,actuator_idN,startN,endN,timeN)
            num_actuators = len(data)/4

            # MOTHs on SPHEREUNITS can be on one of two nodes
            pin_list1 = []
            start_list1 = []
            end_list1 = []
            time_list1 = []
            pin_list2 = []
            start_list2 = []
            end_list2 = []
            time_list2 = []
            for d in range(0, len(data),4):

                # interpret actuator id, find out which of the two nodes it is on, and its pin
                actuator_id = data[d]
                if "MOTH" in actuator_id:
                    index = int(actuator_id[4])
                    
                    if index < 7:
                        # it is on first node
                        node = 1
                        node_id = node_ids[-2]
                        pin = device_locator.Moths[node_id][index - 1]
                        pin_list1.append(pin)
                        start_list1.append(data[d+1])
                        end_list1.append(data[d+2])
                        time_list1.append(data[d+3])
                        
                    else:
                        #it is on second node
                        node = 2
                        node_id = node_id[-1]
                        pin = device_locator.Moths[node_id][index - 7]
                        pin_list2.append(pin)
                        start_list2.append(data[d+1])
                        end_list2.append(data[d+2])
                        time_list2.append(data[d+3])

                elif "RS" in actuator_id:

                    # rebel stars are always on second node
                    node_id = node_ids[-1]
                    index = int(actuator_id[2])
                    pin = device_locator.Rebel_Star[node_id][index - 1]
                    pin_list2.append(pin)
                    start_list2.append(data[d+1])
                    end_list2.append(data[d+2])
                    time_list2.append(data[d+3])
                    
                
            print("FADE_ACTUATOR_GROUP SPHERE")
            if len(pin_list1) > 0:
                # send command to actuators on first node
                pi,teensy_bytes = find_pi_from_teensy_int_id(node_ids[-2])
                send_fade_command(pi,teensy_bytes, pin_list1,start_list1,end_list1,time_list1)
            if len(pin_list2)>0:
                # send command to actuators on second node
                pi,teensy_bytes = find_pi_from_teensy_int_id(node_ids[-1])
                send_fade_command(pi,teensy_bytes, pin_list2,start_list2,end_list2,time_list2)

    elif code == "ACTIVATE":
        if "SSS" in identifier:
            # message format
            # /4D/ACTIVATE/SSS3 1 10000
            
            SSS_num = int(identifier[3])
            strength = data[0]
            timespan = data[1]
            ACTIVATE_SSS(SSS_num, strength, timespan)
            
        elif "SPHERE" in identifier:
            # message format
            # /4D/ACTIVATE/SPHERE3 1 10000
            
            sphere_num = int(identifier[6])
            strength = data[0]
            timespan = data[1]
            ACTIVATE_SPHEREUNIT(sphere_num, strength, timespan)

    elif code == "RIPPLE":
        if "SSS" in identifier:
            # message format
            # /4D/RIPPLE/SSS3 1 10000
            
            SSS_num = int(identifier[3])
            strength = data[0]
            timespan = data[1]
            RIPPLE_SSS(SSS_num, strength, timespan)
            
        elif "SPHERE" in identifier:
            # message format
            # /4D/RIPPLE/SPHERE3 1 10000
            
            sphere_num = int(identifier[6])
            strength = data[0]
            timespan = data[1]
            RIPPLE_SPHEREUNIT(sphere_num, strength, timespan)

def ACTIVATE_SSS(SSS_num, strength, timespan):

    # fades up [strength] rebel stars to 75 over one second
    # then fades back down to zero

    node_id = device_locator.SSS[SSS_num - 1][-1] #moths/RS on last node in SSS
    moth_list = device_locator.Moths[node_id]
    RS_list = device_locator.Rebel_Star[node_id]
    
    pi,teensy_bytes = find_pi_from_teensy_int_id(node_id)
    pin_list = RS_list[:strength]
    start_list = [0]*strength
    end_list = [75]*strength
    
    half_time = int(timespan/2)
    time_list = [half_time]*strength

    # fade up right now
    send_fade_command(pi,teensy_bytes, pin_list,start_list,end_list,time_list)

    # fade down one second from now
    future_manager.add_function(half_time, send_fade_command, pi, teensy_bytes, pin_list, end_list, start_list, time_list)

def ACTIVATE_SPHEREUNIT(sphere_num, strength, timespan):

    # fades up [strength] rebel stars to 75 over one second
    # then fades back down to zero

    node_ids = device_locator.SphereUnit[sphere_num - 1]

    # for now: take moths on first node only
    moth_list = device_locator.Moths[node_ids[-2]]

    # rebel stars are on second node
    RS_list = device_locator.Rebel_Star[node_ids[-1]]

    # this node has rebel stars
    node_id = node_ids[-1]
    
    pi,teensy_bytes = find_pi_from_teensy_int_id(node_id)
    pin_list = RS_list[:strength]
    start_list = [0]*strength
    end_list = [75]*strength

    half_time = int(timespan/2)
    time_list = [half_time]*strength

    # fade up right now
    send_fade_command(pi,teensy_bytes, pin_list,start_list,end_list,time_list)

    # fade down after waiting to fade up
    future_manager.add_function(half_time, send_fade_command, pi, teensy_bytes, pin_list, end_list, start_list, time_list)

def RIPPLE_SSS(SSS_start, strength, timespan):

    max_distance = max(SSS_start - 1, 6 - SSS_start)

    jump_time = int(timespan/max_distance)

    # first activate the starting SSS
    ACTIVATE_SSS(SSS_start, strength, jump_time)

    # now propagate the actuation away
    for index in range(1, max_distance + 1):
        forward_SSS = index + SSS_start
        backward_SSS = SSS_start - index
        time_to_wait = jump_time*index

        if forward_SSS <= 6:
            # maximum index for SSS is 5
            future_manager.add_function(time_to_wait, ACTIVATE_SSS, forward_SSS, strength, jump_time)
        if backward_SSS >= 1:
            future_manager.add_function(time_to_wait, ACTIVATE_SSS, backward_SSS, strength, jump_time)
            
            
        
def RIPPLE_SPHEREUNIT(sphere_start, strength, timespan):

    max_distance = max(sphere_start - 1, 12 - sphere_start)

    jump_time = int(timespan/max_distance)

    # first activate the starting sphere
    ACTIVATE_SPHEREUNIT(sphere_start, strength, jump_time)

    # now propagate the actuation away
    for index in range(1, max_distance + 1):
        forward_sphere = index + sphere_start
        backward_sphere = sphere_start - index
        time_to_wait = jump_time*index

        if forward_sphere <= 12:
            # maximum index for sphere is 5
            future_manager.add_function(time_to_wait, ACTIVATE_SPHEREUNIT, forward_sphere, strength, jump_time)
        if backward_sphere >= 1:
            future_manager.add_function(time_to_wait, ACTIVATE_SPHEREUNIT, backward_sphere, strength, jump_time)
    

    
    
    


def find_pi_from_teensy_int_id(int_id):
    for pi in pi_ip_addresses:
        for teensy in connected_teensies[pi]:
            print("teensy: " + str(teensy))
            print("int id: " + str(int_id))
            
            int_from_bytes = ((teensy[0] << 16) | (teensy[1] << 8)) | teensy[2]
            print("bytes: " + str(int_from_bytes))
            if int_from_bytes == int_id:
                return pi,teensy
    print("ERROR: Cannot locate Pi for this Teensy ID - is DeviceLocator.py out of date?")
            
            

    

dispatcher = dispatcher.Dispatcher()
dispatcher.set_default_handler(receive_all_OSC)
OSC_listener = osc_server.BlockingOSCUDPServer(('0.0.0.0', OSC_PORT_RECEIVE), dispatcher)
OSC_listener_thread = threading.Thread(target=OSC_listener.serve_forever)
OSC_listener_thread.start()

# Client
OSC_PORT_TRANSMIT = 3000
OSC_client = udp_client.UDPClient(IP_4D_LAPTOP, OSC_PORT_TRANSMIT)

def send_OSC_to_4D(addr, data):
    msg = osc_message_builder.OscMessageBuilder(address = addr)
    for d in data:
        msg.add_arg(d)
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
debug = False
send_fade = False
listening_thread = threading.Thread(target = receive_bytes)
listening_thread.start()

time.sleep(1)
# note: int.to_bytes(362262, byteorder = 'big', length = 3) = b'\x05\x87\x16'      

request_connected_teensies()

start_time = time.time()



while True:

    # first see if we need to do any waiting functions
    future_manager.do_if_time_elapsed_and_remove()

    # check for OSC message from 4d laptop
    try:
        incoming_OSC = OSC_packet_queue.get(block = False)
        print("Incoming OSC: " + str(incoming_OSC))
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
                
            elif code == IR_TRIGGER:

                # first find which SSS this came from
                SSS = -1
                for i in range(len(device_locator.SSS)):
                    # IR sensors are only on second node
                    if tid == device_locator.SSS[i][1]:
                        SSS = i

                # enumerate IR sensor number
                sensor_num = data[0]
                IR_index = SSS*3 + sensor_num

                # send to 4D
                send_to_4D("/4D/TRIGGER/IR" + str(IR_index), [])
                
        
        except queue.Empty:
            pass

        # these if statements are just for testing

        if debug and tested_teensies == False:
            tested_teensies = test_connected_teensies()

        if time.time() - start_time > 5 and send_fade == True:
            send_fade_command_to_all([13],[0],[50],[2000])
            time.sleep(2)
            send_fade_command_to_all([13],[50],[0],[2000])
            send_fade = False
            
            




