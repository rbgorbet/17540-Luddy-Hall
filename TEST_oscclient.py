"""
This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import random
import time

from pythonosc import osc_message_builder
from pythonosc import udp_client

IP_MASTER = "192.168.2.24"


if __name__ == "__main__":

    client = udp_client.UDPClient(IP_MASTER, 3001)
    #msg = osc_message_builder.OscMessageBuilder(address = "/4d/test")
    #msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/245689/13/0/50/2000/14/0/50/2000")
    #msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/245689/13/0/50/2000")
    
##    msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/SSS1")
##    msg.add_arg("RS1")
##    msg.add_arg(50)
##    msg.add_arg(0)
##    msg.add_arg(2000)
##    msg.add_arg("RS2")
##    msg.add_arg(50)
##    msg.add_arg(0)
##    msg.add_arg(2000)
    msg = osc_message_builder.OscMessageBuilder(address = "/4D/RIPPLE/SPHERE9")
    msg.add_arg(2)
    msg.add_arg(20000)
    msg = msg.build()
    client.send(msg)

    #time.sleep(2)
    #msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/245689/13/50/0/2000/14/0/50/2000")
    #msg = osc_message_builder.OscMessageBuilder(address = "/4D/FADE_ACTUATOR_GROUP/245689/13/50/0/2000")
    #msg = msg.build()
    #client.send(msg)
