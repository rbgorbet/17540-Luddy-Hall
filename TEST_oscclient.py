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

    client = udp_client.UDPClient("192.168.1.8", 3001)
    #msg = osc_message_builder.OscMessageBuilder(address = "/4d/test")
    msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/362338/13/0/50/2000/14/0/50/2000")
    msg = msg.build()
    client.send(msg)

    time.sleep(2)
    msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/362338/13/50/0/2000/14/0/50/2000")
    msg = msg.build()
    client.send(msg)
