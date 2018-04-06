# 17540-Luddy-Hall
Code for Luddy Hall project 

# Folders

* LuddyNode contains the main Teensy code (LuddyNode.ino) and related C++ libraries.
* LuddyPiSlave contains the main Raspberry Pi code (LuddyPiSlave.py) and related Python libraries.
* LuddyLaptopMaster contains the main PC code (LuddyLaptopMaster.py) and related Python libraries.

# Files

* LuddyNode32.hex is the LuddyNode program compiled for Teensy3.2 (for node controllers)
* LuddyNode36.hex is the LuddyNode program compiled for Teensy3.6 (for audio boards)

# Usage

1. Using TyCommander on the Raspberry Pi, upload the appropriate .hex file.
2. In LuddyPiSlave.py modify `IP_LAPTOP` so that it matches the IP address of the master laptop. Copy the whole LuddyPiSlave folder to the Pi, and run `python3 LuddyPiSlave.py`.
3. In LuddyLaptopMaster.py modify  `pi_ip_addresses = []` so that it contains a list of all Raspberry Pi IP addreses, modify `IP_4D_LAPTOP` so that it matches the IP address of the 4D Mac. Copy the whole LuddyLaptopMaster to the master laptop and run `LuddyLaptopMaster.py` with python3.
