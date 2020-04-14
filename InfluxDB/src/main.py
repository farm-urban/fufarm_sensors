import binascii
import socket
import sys
import time

# These require separate imports
import machine
import pycom
from machine import Timer
from network import WLAN
import urequests

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

import config as CONFIG


# def reset_wlan(wlan):
#     """Reset the WLAN to the default settings"""
#     # wlan.deinit()
#     wlan.init(
#         mode=WLAN.AP,
#         ssid="wipy-wlan-1734",
#         auth=(WLAN.WPA2, "www.pycom.io"),
#         channel=6,
#         antenna=WLAN.INT_ANT,
#     )
#     return

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



def take_readings():
    print("Take readings")
    readings = { 'water_temperature' : None,
                 'barometer_pressure' : None,
                 'humidity_humidity' : None,
                 'humidity_temperature' : None,
                 'ambient_light_0' : None,
                 'ambient_light_1' : None }
    if lts_ready:  # DS18B20 liquid temperature sensor.
        print("READING TEMP")
        liquid_temp_sensor.start_conversion()
        while True:
            water_temperature = liquid_temp_sensor.read_temp_async()
            if water_temperature is not None:
                break
        print(u"Water temperature = {} \u00b0C.".format(water_temperature))
        readings['water_temperature'] = water_temperature

    if barometer_ready:  # MPL3115A2 barometer sensor.
        readings['barometer_temperature'] = barometric_pressure.temperature()

    if humidity_sensor_ready:  # SI7006A20 humidity sensor.
        readings['humidity_humidity'] = humidity_sensor.humidity()
        readings['humidity_temperature']= humidity_sensor.temperature()
        #print("Humidity  = {}".format(humidity_humidity))

    if light_sensor_ready:  # LTR329ALS01 light sensor.
        readings['ambient_light_0'] = light_sensor.light()[0]
        readings['ambient_light_1'] = light_sensor.light()[1]
    return readings



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

#   ,-----------------------------------------------------------,
#   | These are the PySense specific sensors.                   |
#   '-----------------------------------------------------------'
board = Pysense()
light_sensor = LTR329ALS01(board)
barometric_pressure = MPL3115A2(board, mode=PRESSURE)
# barometric_altitude = MPL3115A2(board, mode=ALTITUDE)
humidity_sensor = SI7006A20(board)
# DS18B20 liquid temperature sensor.
lts_pin = OneWire(Pin("P10"))  # Set up input GPIO.
liquid_temp_sensor = DS18X20(lts_pin)

# DS18B20 liquid temperature sensor.
lts_ready = lts_pin.reset()
print("Liquid temperature sensor present = {}".format(lts_ready))

# MPL3115A2
barometer_ready = barometric_pressure._read_status()
print("Barometer sensor present = {}".format(barometer_ready))

# LTR329ALS01
light_sensor_ready = True  # There is no available function to test.
print("Light sensor present = {}".format(light_sensor_ready))
# SI7006A20
humidity_sensor_ready = True  # There is no available function to test.
print("Humidity sensor present = {}".format(humidity_sensor_ready))


# Initialisation.
if CONFIG.STATION_MAC is None:
    CONFIG.STATION_MAC = binascii.hexlify(machine.unique_id())

wlan = WLAN(mode=WLAN.STA)
nets = wlan.scan()
for net in nets:
    if net.ssid == CONFIG.NETWORK_SSID:
        print('Network found!')
        wlan.connect(net.ssid, auth=(net.sec, CONFIG.NETWORK_KEY), timeout=5000)
        while not wlan.isconnected():
            machine.idle() # save power while waiting
        print("WLAN connection succeeded!")
        break


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
    print(info_str)

# 

include_timestamp = False
while True:
    d = take_readings()
    data = ""
    for k, v in d.items():
        data += 'fu_sensor,stationid={},sensor={} value={}' \
               .format(CONFIG.STATION_MAC,CONFIG.SENSORS[k],v)
        # if include_timestamp is True:
        #     data += ' {}000000000'.format(self.timestamp)
        data += "\n"

    print('sending data\n{}'.format(data))
    influx_url = 'http://rpi.local:8086/write?db=mydb'
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            urequests.post(influx_url, data=data)
            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass
    time.sleep(5)


