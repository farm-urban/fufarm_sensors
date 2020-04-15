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
from MPL3115A2 import MPL3115A2, PRESSURE  # Barometer and temperature
from SI7006A20 import SI7006A20  # Humidity & temperature.

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

def take_readings():
    print("Take readings")
    l0, l1 = light_sensor.light()
    return { 'barometer_pressure' : barometer.pressure(),
             'barometer_temperature' : barometer.temperature(),
             'humidity_humidity' : humidity_sensor.humidity(),
             'humidity_temperature' : humidity_sensor.temperature(),
             'ambient_light_0' : l0,
             'ambient_light_1' : l1 }


NETWORK_CONFIG_STR = """Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}"""
NTP_SERVER = 'pool.ntp.org'

LED = {'amber' : 0xFF8000,
       'black' : 0x000000,
       'blue'  : 0x0000FF,
       'green' : 0x00FF00,
       'red'   : 0xFF0000 }
#chrono = Timer.Chrono()


rtc = machine.RTC()  # Get date and time from server.
board = Pysense()
light_sensor = LTR329ALS01(board)
barometer = MPL3115A2(board, mode=PRESSURE)
humidity_sensor = SI7006A20(board)

# Initialisation.
if CONFIG.STATION_MAC is None:
    CONFIG.STATION_MAC = ubinascii.hexlify(machine.unique_id())

wlan = WLAN(mode=WLAN.STA)
nets = wlan.scan()
for net in nets:
    if net.ssid == CONFIG.NETWORK_SSID:
        print('Network found!')
        wlan.connect(net.ssid, auth=(net.sec, CONFIG.NETWORK_KEY), timeout=5000)
        while not wlan.isconnected():
            machine.idle() # save power while waiting
        print(NETWORK_CONFIG_STR.format(*wlan.ifconfig()))

rtc.ntp_sync(NTP_SERVER)
ntp_synced = False
if rtc.synced():
    ntp_synced = True

include_timestamp = ntp_synced
sensor_interval = 10
while True:
    d = take_readings()
    data = ""
    for k, v in d.items():
        # k = CONFIG.SENSORS[k]
        data += 'fu_sensor,stationid={},sensor={} value={}' \
               .format(CONFIG.STATION_MAC,k,v)
        if include_timestamp is True:
            data += ' {}000000000'.format(self.timestamp)
        data += "\n"
    print('sending data\n{}'.format(data))
    influx_url = 'http://192.168.0.7:8086/write?db=fudata'
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
    time.sleep(sensor_interval)
