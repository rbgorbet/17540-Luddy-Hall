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

IP_PI1 = '192.168.2.47'
PORT_RECEIVE = 4000
PORT_TRANSMIT = 4001
MY_IP ='0.0.0.0'

sock_transmit = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

sock_receive = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock_receive.bind((MY_IP, PORT_RECEIVE))



def send_message(MESSAGE):
    sock_transmit.sendto(bytes(MESSAGE, 'utf-8'), (IP_PI1, PORT_TRANSMIT))


def receive_message():
    while True:
        data, addr = sock_receive.recvfrom(1024) # buffer size is 1024 bytes
        print("Received message: " + str(data, 'utf-8'))


def send_bytes(raw_bytes):
    sock_transmit.sendto(raw_bytes, (IP_PI1, PORT_TRANSMIT))


def receive_bytes():
    while True:
        data, addr = sock_receive.recvfrom(1024) # buffer size is 1024 bytes
        print("Received UDP - Address: " + addr[0] + ", Data: " + str(data))

#main
listening_thread = threading.Thread(target = receive_bytes)
listening_thread.start()

time.sleep(1)

TEST_LED_PIN_AND_RESPOND = b'\xff\xff\x05\x87\x16\x04\x00\x04\x00\x00\x01\xfe\xfe'
print("Sending TEST_LED_PIN_AND_RESPOND")
send_bytes(TEST_LED_PIN_AND_RESPOND)
