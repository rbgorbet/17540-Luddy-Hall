# PiUDP.py - LASG/PBAI
# Created by Adam France, March 16 2018
# Handles UDP communication between Raspberry Pi and master laptop

import socket
import threading
import queue

class PiUDP():
    def __init__(self, ip_laptop, port_receive, port_send):

        # received data in bytes in queue
        self.data_bytes_queue = queue.Queue()

        # received data as a utf-8 string
        self.data_string = ''

        # address we receive from
        self.addr = ''

        self.ip_laptop = ip_laptop # master laptop
        self.port_receive = port_receive
        self.port_send = port_send

        self.sock_transmit = socket.socket(socket.AF_INET, # Internet
                              socket.SOCK_DGRAM) # UDP

        self.sock_receive = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
        self.sock_receive.bind(('0.0.0.0', port_receive))

        
        # set to False when we close the sockets
        self.running = True

        # we listen for incoming bytes continuously on a separate thread
        self.listening_thread = threading.Thread(target = self.receive_bytes)
        self.listening_thread.start()
        print("Starting UDP receiver - Port: " + str(port_receive))
        print("Starting UDP sender - Address: " + ip_laptop + " , Port: " + str(port_send))

    def send_bytes(self, raw_bytes):
        print("Sending UDP: " + str(raw_bytes))
        self.sock_transmit.sendto(raw_bytes, (self.ip_laptop, self.port_send))

    def receive_bytes(self):
        while self.running:
            # recvfrom blocks until it receives a UDP packet
            data_bytes, self.addr = self.sock_receive.recvfrom(1024) # buffer size is 1024 bytes

            # store the packet in the queue
            self.data_bytes_queue.put(data_bytes)
            print("Received UDP - Address: " + self.addr[0] + ", Data: " + str(data_bytes))
            

    def send_string(self, string):
        self.sock_transmit.sendto(bytes(string, 'utf-8'), (self.ip_laptop, self.port_send))

    def receive_string(self):
        while self.running:
            self.data_string, addr = self.sock_receive.recvfrom(1024) # buffer size is 1024 bytes
            print("Received string: " + str(self.data_string, 'utf-8'))

    def decode_bytes(self, raw_bytes):

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

    def close(self):
        # NEEDS WORK -------------------------------------
        print("Closing UDP sockets")
        self.running = False
        #self.sock_transmit.shutdown(socket.SHUT_RDWR)
        #self.sock_receive.shutdown(socket.SHUT_RDWR)
        self.sock_transmit.close()
        self.sock_receive.close()
        #self.listening_thread.join()
        
            
