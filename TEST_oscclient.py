"""
This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import random
import time

from pythonosc import osc_message_builder
from pythonosc import udp_client

IP_MASTER = "192.168.2.22"


if __name__ == "__main__":

    client = udp_client.UDPClient("192.168.2.22", 3001)
    msg = osc_message_builder.OscMessageBuilder(address = "/4d/test")
    msg = msg.build()
    client.send(msg)
