"""
    This program tests the feasibility of a sensor monitoring system

    Copyright (C) 2018  Darren Faulke (VEC), Jens Thomas (Farm Urban)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

# Board initialisation:
# Connects to wi-fi.
# Opens UDP socket.

# Sets up database and macros.

import binascii
import logging
import machine
import pycom
import socket
import struct
import sys
import time
# These require separate imports
from machine import Timer
from network import WLAN

LOG_LEVEL = logging.DEBUG
DATA_OVER_USB = True # jmht - send data over the USB cable rather then wifi
ERROR = False # Global error flag - required as main executed regardless of boot.py
# =============================================================================
# Networking.
# =============================================================================
NETWORK_SSID    = 'vec-lab'         # Router broadcast name.
NETWORK_KEY     = 'vec-lab123'      # Access key.
NETWORK_TIMEOUT = 20                # Connection timeout (s)

STATIC_IP = False
# These are only needed for static IP address.
NETWORK_IP       = '192.168.0.103'   # IP address.
NETWORK_MASK     = '255.255.255.0'   # Network mask.
NETWORK_GATEWAY  = '192.168.0.1'     # Gateway.
NETWORK_DNS      = '192.168.0.1'     # DNS server (N/A).
NETWORK_CONFIG   = (NETWORK_IP, NETWORK_MASK, NETWORK_GATEWAY, NETWORK_DNS)

#HOST_NAME       = '138.253.118.249' # MySQL server address.
HOST_NAME       = '192.168.0.101'   # MySQL server address.
HOST_PORT       =  9000             # UDP port.
HOST_ADDRESS    = (HOST_NAME, HOST_PORT)

NTP_AVAILABLE   = False             # NTP server available?
NTP_ADDRESS     = 'pool.ntp.org'    # Address of open NTP server.

SENSOR_INTERVAL = 0.1 # Minutes.

# =============================================================================
# Data structures.
# =============================================================================
#
#   The database structure is defined as:
#
#       ,---------------------------------------------------,
#       | ID | Variable         | DB format     | Type      |
#       |----+------------------+---------------+-----------|
#       | -- | time             | datetime      | datetime  |
#       | -- | station          | char(12)      | bytes     |
#       | 01 | water_temp       | decimal(3,1)  | real      |
#       | 02 | air_temp         | decimal(3,1)  | real      |
#       | 03 | soil_humidity    | decimal(3,1)  | real      |
#       | 04 | air_humidity     | decimal(3,1)  | real      |
#       | 05 | ambient_light0   | smallint      | int       |
#       | 06 | ambient_light1   | smallint      | int       |
#       | 07 | ph_level         | decimal(2,2)  | real      |
#       | 08 | orp_level        | decimal(2,2)  | real      |
#       '---------------------------------------------------'

# =============================================================================
# Colour definitions for LED.
# =============================================================================
GREEN = 0x00ff00
AMBER = 0xff8000
RED = 0xff0000
BLUE = 0x0000ff
BLACK = 0x000000

UART = None
SOCKET = None
def connect_to_network(wlan):
    """Connect to access point"""
    if STATIC_IP:
        info_str = """
Using static IP address with:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}""".format(NETWORK_IP, NETWORK_MASK, NETWORK_GATEWAY, NETWORK_DNS)
        logger.info(info_str)
        wlan.ifconfig(config=NETWORK_CONFIG)
    else:
        logger.info("IP address will be assigned via DHCP.")
    logger.info("Looking for access point: {}".format(NETWORK_SSID))
    nets = wlan.scan()
    found = False
    for net in nets:
        #logger.info(".")
        if net.ssid == NETWORK_SSID:
            logger.info("Found %s access point!".format(NETWORK_SSID))
            found = True
            break
    if not found:
        logger.critical("Could not find access point {}".format(NETWORK_SSID))
        return False

#   ,-----------------------------------------------------------,
#   | The WLAN.connect timeout doesn't actually do anything so  |
#   | an alternative timeout method has been implemented.       |
#   | See Pycom forum topic 2201.                               |
#   '-----------------------------------------------------------'
    logger.info("Connecting to {}".format(NETWORK_SSID))
    wlan.connect(net.ssid, auth=(net.sec, NETWORK_KEY))
    CHRONO.start()
    start_loop = CHRONO.read()
    start_scan = start_loop
    while not wlan.isconnected():
        if CHRONO.read() - start_scan >= NETWORK_TIMEOUT:
            logger.critical("Timout on network connect.")
            break
        if CHRONO.read() - start_loop >= NETWORK_TIMEOUT / 50:
            start_loop = CHRONO.read()
            logger.info(".")
    CHRONO.stop()

    if wlan.isconnected():
        info_str = """
Successfully connected to network.
Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}""".format(wlan.ifconfig())
        logger.info(info_str)

    return wlan.isconnected()

def reset_wlan(wlan):
    """Reset the WLAN to the default settings"""
    #wlan.deinit()
    wlan.init(mode=WLAN.AP,
              ssid='wipy-wlan-1734',
              auth=(WLAN.WPA2,'www.pycom.io'),
              channel=6,
              antenna=WLAN.INT_ANT)

def setup_serial():
    #os.dupterm(None) # Kill the REPL?
    logger.debug("Setting up serial")
    global UART
    BUS = 0
    BAUDRATE = 9600
    UART = machine.UART(BUS, BAUDRATE)
    UART.init(BAUDRATE, bits=8, parity=None, stop=1)
    logger.debug("Serial done")


def setup_socket():
    logger.debug("Setting up socket")
    # Connection keeps dropping.
    # if not P_WLAN.isconnected():
    #     logger.critical("Couldn't connect to access point.")
    #     pycom.rgbled(RED)
    #     sys.exit(1)
    logger.info("Trying to create a network socket.")
    try:
        sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info("Socket created.")
    except Exception as e:
        logger.critical("Failed to create socket - quitting: {}: {}".format(type(e),e))
        pycom.rgbled(RED)
        sys.exit()
    sockt.setblocking(False)
    return soctk

def setup_communication():
    global SOCKET, DATA_OVER_USB
    if DATA_OVER_USB:
        setup_serial()
    else:
        wlan = WLAN(mode=WLAN.STA)
        if connect_to_network(wlan):
            SOCKET = setup_socket()
        else:
            reset_wlan(wlan)
            raise RuntimeError("Could not connect to network")

# Initialisation.
logging.basicConfig(level=LOG_LEVEL, filename=True)
logger = logging.getLogger(__name__)
pycom.heartbeat(False)  # Turn off pulsing LED heartbeat.
time.sleep(0.1) # sleep required to get rgbled to change color?!?
pycom.rgbled(AMBER)
CHRONO = Timer.Chrono()
STATION_MAC = binascii.hexlify(machine.unique_id())
logger.info("Station MAC = %s.", STATION_MAC.decode())
try:
    setup_communication()
except Exception as e:
    logger.critical("Error setting up communication: {}: {}".format(type(e),e))
    ERROR = True
    pycom.rgbled(RED)
    time.sleep(3)

logger.debug('completed boot.py')
