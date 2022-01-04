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

import binascii
import socket
import struct
import sys
import time

# These require separate imports
import machine
import pycom
from machine import Timer
from network import WLAN

# Libraries for the PySense board sensors from the PyCom github repository.               |
from pysense import Pysense  # Main pysense module.
from LTR329ALS01 import LTR329ALS01  # Ambient Light
from MPL3115A2 import MPL3115A2  # Barometer and temperature

# from MPL3115A2   import ALTITUDE # Barometric pressure.
from MPL3115A2 import PRESSURE  # Barometric altitude.
from SI7006A20 import SI7006A20  # Humidity & temperature.

#   ,-----------------------------------------------------------,
#   | These are the libraries for the DS18B20 sensor.           |
#   | The onewire library is from the PyCom github repository.  |
#   | The machine library is built-in.                          |
#   '-----------------------------------------------------------'
from machine import Pin
from onewire import OneWire
from onewire import DS18X20  # Liquid temperature.

# Local imports
import logging
import config as CONFIG


def init():
    logger.info("Starting Init")
    pycom.heartbeat(False)  # Turn off pulsing LED heartbeat.
    time.sleep(0.1)  # sleep required to get rgbled to change color?!?
    pycom.rgbled(AMBER)
    setup_communication()
    pycom.rgbled(BLUE)
    logger.info("Finished Init")
    return


def get_time():
    """
#   | The RTC module can set time directly from an NTP server   |
#   | using e.g.                                                |
#   |       rtc.ntp_sync("pool.ntp.org")                        |
#   | but testing is on a local network without access to an    |
#   | NTP server. Instead this function sends a command to get  |
#   | a datatime packet from the database injector.             |
    """
    old_time = RTC.now()
    if CONFIG.NTP_AVAILABLE:
        RTC.ntp_sync(CONFIG.NTP_ADDRESS)
        new_time = RTC.now()
        out_str = """Getting time from NTP server {0}
Current time is {1}
Revised time is {2}""".format(
            CONFIG.NTP_ADDRESS, old_time, new_time
        )
        logger.info(out_str)
    else:
        packet = "ntp"
        SOCKET.sendto(packet, CONFIG.HOST_ADDRESS)
        ntp_time, ip_from = SOCKET.recvfrom(512)
        dec_time = ntp_time.decode("utf-8")
        set_time = tuple(map(int, dec_time.split(",")))
        RTC.init(set_time)
        new_time = RTC.now()
        out_str = """Getting time from database injector.
Current time is {0}
Revised time is {1}""".format(
            old_time, new_time
        )
        logger.info(out_str)
    return


def send_data(sensor, value):
    """Takes readings and sends data to database injector."""
    # Pack the data into a C type structure.
    packet = struct.pack("@12sHf", CONFIG.STATION_MAC, sensor, value)
    logger.info("Sending {} bytes.\nData packet = {}".format(len(packet), packet))
    if CONFIG.DATA_OVER_USB:
        nbytes = UART.write(packet)
        logger.info("UART wrote %s bytes", nbytes)
    else:
        logger.info("Sending packet to: {}".format(CONFIG.HOST_ADDRESS))
        try:
            SOCKET.sendto(packet, CONFIG.HOST_ADDRESS)
        except OSError as e:
            logger.critical("Error sending packet: {}".format(e))
    time.sleep(1)
    logger.info("End send_data")
    return


def take_readings():
    logger.debug("Take readings")
    pycom.rgbled(BLUE)  # Change the LED to indicate that it is taking readings.
    if lts_ready:  # DS18B20 liquid temperature sensor.
        logger.info("Water temperature readings:")
        liquid_temp_sensor.start_conversion()
        reading = False
        while not reading:
            water_temperature = liquid_temp_sensor.read_temp_async()
            if water_temperature is not None:
                reading = True
        logger.info(u"Water temperature = {} \u00b0C.".format(water_temperature))
        send_data(CONFIG.SENSORS["water_temperature"], water_temperature)

    if barometer_ready:  # MPL3115A2 barometer sensor.
        logger.info("Barometer readings:")
        barometer_temperature = barometric_pressure.temperature()
        logger.info(u"Temperature = {} \u00b0C".format(barometer_temperature))
        send_data(CONFIG.SENSORS["barometer_temperature"], barometer_temperature)

    if humidity_sensor_ready:  # SI7006A20 humidity sensor.
        logger.info("Humidity sensor readings:")
        humidity_humidity = humidity_sensor.humidity()
        humidity_temperature = humidity_sensor.temperature()
        logger.info("Humidity  = {}".format(humidity_humidity))
        send_data(CONFIG.SENSORS["humidity_humidity"], humidity_humidity)
        logger.info(u"Temperature = {} \u00b0C.".format(humidity_temperature))
        send_data(CONFIG.SENSORS["humidity_temperature"], humidity_temperature)

    if light_sensor_ready:  # LTR329ALS01 light sensor.
        logger.info("Ambient light sensor readings:")
        ambient_light_0 = light_sensor.light()[0]
        ambient_light_1 = light_sensor.light()[1]
        logger.info("Light level (sensor 0) = {} lx.".format(ambient_light_0))
        send_data(CONFIG.SENSORS["ambient_light_0"], ambient_light_0)
        logger.info("Light level (sensor 1) = {} lx.".format(ambient_light_1))
        send_data(CONFIG.SENSORS["ambient_light_1"], ambient_light_1)

    pycom.rgbled(GREEN)
    return


def log_level():
    d = {"debug": logging.DEBUG, "info": logging.INFO, "critical": logging.CRITICAL}
    if (
        CONFIG.LOG_LEVEL
        and isinstance(CONFIG.LOG_LEVEL, str)
        and CONFIG.LOG_LEVEL.lower() in d
    ):
        return d[CONFIG.LOG_LEVEL.lower()]
    else:
        return logging.CRITICAL


def connect_to_network(wlan):
    """Connect to access point"""
    if CONFIG.STATIC_IP:
        info_str = """
Using static IP address with:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}""".format(
            CONFIG.NETWORK_IP,
            CONFIG.NETWORK_MASK,
            CONFIG.NETWORK_GATEWAY,
            CONFIG.NETWORK_DNS,
        )
        logger.info(info_str)
        wlan.ifconfig(config=CONFIG.NETWORK_CONFIG)
    else:
        logger.info("IP address will be assigned via DHCP.")
    logger.info("Looking for access point: {}".format(CONFIG.NETWORK_SSID))
    found = False
    for net in wlan.scan():
        if net.ssid == CONFIG.NETWORK_SSID:
            logger.info("Found {} access point!".format(CONFIG.NETWORK_SSID))
            found = True
            break
    if not found:
        logger.critical("Could not find access point {}".format(CONFIG.NETWORK_SSID))
        return False

    #   ,-----------------------------------------------------------,
    #   | The WLAN.connect timeout doesn't actually do anything so  |
    #   | an alternative timeout method has been implemented.       |
    #   | See Pycom forum topic 2201.                               |
    #   '-----------------------------------------------------------'
    logger.info("Connecting to {}".format(CONFIG.NETWORK_SSID))
    wlan.connect(net.ssid, auth=(net.sec, CONFIG.NETWORK_KEY))
    CHRONO.start()
    start_loop = CHRONO.read()
    start_scan = start_loop
    while not wlan.isconnected():
        if CHRONO.read() - start_scan >= CONFIG.NETWORK_TIMEOUT:
            logger.critical("Timout on network connect.")
            break
        if CHRONO.read() - start_loop >= CONFIG.NETWORK_TIMEOUT / 50:
            start_loop = CHRONO.read()
            # logger.info(".")
    CHRONO.stop()

    if wlan.isconnected():
        info_str = """
Successfully connected to network.
Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}""".format(
            *wlan.ifconfig()
        )
        logger.info(info_str)

    return wlan.isconnected()


def reset_wlan(wlan):
    """Reset the WLAN to the default settings"""
    # wlan.deinit()
    wlan.init(
        mode=WLAN.AP,
        ssid="wipy-wlan-1734",
        auth=(WLAN.WPA2, "www.pycom.io"),
        channel=6,
        antenna=WLAN.INT_ANT,
    )
    return


def setup_serial(bus=0, baudrate=9600, bits=8):
    # os.dupterm(None) # Kill the REPL?
    logger.debug("Setting up serial")
    uart = machine.UART(bus, baudrate)
    uart.init(baudrate, bits=bits, parity=None, stop=1)
    logger.debug("Serial done")
    return uart


def setup_socket():
    logger.debug("Setting up socket")
    # Connection keeps dropping.
    # if not P_WLAN.isconnected():
    #     logger.critical("Couldn't connect to access point.")
    #     pycom.rgbled(RED)
    #     sys.exit(1)
    logger.info("Trying to create a network socket.")
    sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.info("Socket created.")
    sockt.setblocking(False)
    return sockt


def setup_communication():
    global UART, SOCKET
    if CONFIG.STATION_MAC is None:
        CONFIG.STATION_MAC = binascii.hexlify(machine.unique_id())
    logger.info("Station MAC = %s.", CONFIG.STATION_MAC.decode())
    if CONFIG.DATA_OVER_USB:
        UART = setup_serial()
    else:
        wlan = WLAN(mode=WLAN.STA)
        if connect_to_network(wlan):
            SOCKET = setup_socket()
        else:
            reset_wlan(wlan)
            raise RuntimeError("Could not connect to network")
    return


def exit_error(message, traceback=None):
    logger.critical(message)
    if traceback:
        logger.logTraceback(traceback)
    pycom.rgbled(RED)
    time.sleep(3)
    sys.exit(1)


def main():
    logger.info("Starting Main Loop")
    CHRONO.start()
    start_time = time.time()
    while True:
        check_time = time.time()
        elapsed_time = check_time - start_time
        if elapsed_time >= CONFIG.SENSOR_INTERVAL:
            take_readings()
            start_time = time.time()
    return


# =============================================================================
# Colour definitions for LED.
# =============================================================================

GREEN = 0x00FF00
AMBER = 0xFF8000
RED = 0xFF0000
BLUE = 0x0000FF
BLACK = 0x000000

SOCKET = None
UART = None
CHRONO = Timer.Chrono()
RTC = machine.RTC()  # Get date and time from server.

# Initialisation.
print("RUNING MAIN")
logging.basicConfig(level=log_level(), filename=None)
logger = logging.getLogger(__name__)
print("SETUP LOGGER")
try:
    init()
except Exception as e:
    msg = "Error initialising network: {}: {}".format(type(e), e)
    exit_error(msg, traceback=e)

#   ,-----------------------------------------------------------,
#   | These are the PySense specific sensors.                   |
#   '-----------------------------------------------------------'
board = Pysense()
light_sensor = LTR329ALS01(board)
barometric_pressure = MPL3115A2(board, mode=PRESSURE)
# barometric_altitude = MPL3115A2(board, mode=ALTITUDE)
humidity_sensor = SI7006A20(board)
#   ,-----------------------------------------------------------,
#   | This is the DS18B20 liquid temperature sensor.            |
#   '-----------------------------------------------------------'
lts_pin = OneWire(Pin("P10"))  # Set up input GPIO.
liquid_temp_sensor = DS18X20(lts_pin)

#   ,-----------------------------------------------------------,
#   | Now let's see which sensors are attached and working.     |
#   '-----------------------------------------------------------'
# DS18B20
lts_ready = lts_pin.reset()
logger.info("Liquid temperature sensor present = %s.", lts_ready)

# MPL3115A2
barometer_ready = barometric_pressure._read_status()
logger.info("Barometer sensor present = %s.", barometer_ready)

#   ,-----------------------------------------------------------,
#   | There are no available functions to test the presence of  |
#   | the light or humidity sensors so these are just assumed   |
#   | to be available for now. It should be possible to simply  |
#   | scan the I2C bus at the addresses for each sensor to      |
#   | detect them.                                              |
#   '-----------------------------------------------------------'

# LTR329ALS01
light_sensor_ready = True  # There is no available function to test.
logger.info("Light sensor present = %s.", light_sensor_ready)
# SI7006A20
humidity_sensor_ready = True  # There is no available function to test.
logger.info("Humidity sensor present = %s.", humidity_sensor_ready)

# =============================================================================
# Main loop.
# =============================================================================
try:
    main()
except Exception as e:
    msg = "Error running main program: {}: {}".format(type(e), e)
    exit_error(msg, traceback=e)
