import binascii
import socket
import sys
import time

# These require separate imports
import machine
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
    pycom.rgbled(LED['green'])
    print("Take readings")
    l0, l1 = light_sensor.light()
    return { 'barometer_pressure' : barometer.pressure(),
             'barometer_temperature' : barometer.temperature(),
             'humidity_humidity' : humidity_sensor.humidity(),
             'humidity_temperature' : humidity_sensor.temperature(),
             'ambient_light_0' : l0,
             'ambient_light_1' : l1 }
    pycom.rgbled(LED['black'])


def readings_to_influxdb_line(readings, station_id):
    data = ""
    for k, v in readings.items():
        data += 'fu_sensor,stationid={},sensor={} measurement={}' \
               .format(station_id,k,v)
        if include_timestamp is True:
            data += ' {}000000000'.format(rtc.now())
        data += "\n"
    return data


NETWORK_CONFIG_STR = """Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}"""
NTP_SERVER = 'pool.ntp.org'



NETWORK_SSID = "virginmedia7305656"
NETWORK_KEY = "vbvnqjxn" 
NTP_ADDRESS = "pool.ntp.org"
SENSOR_INTERVAL = 20  # in seconds
STATION_MAC = binascii.hexlify(machine.unique_id()).decode("utf-8")

rtc = machine.RTC()  # Get date and time from server.
board = Pysense()
light_sensor = LTR329ALS01(board)
barometer = MPL3115A2(board, mode=PRESSURE)
humidity_sensor = SI7006A20(board)

wlan = WLAN(mode=WLAN.STA)
nets = wlan.scan()
for net in nets:
    if net.ssid == NETWORK_SSID:
        print('Found network: {}'.format(NETWORK_SSID))
        wlan.connect(net.ssid, auth=(net.sec, NETWORK_KEY), timeout=5000)
        while not wlan.isconnected():
            machine.idle() # save power while waiting
        print(NETWORK_CONFIG_STR.format(*wlan.ifconfig()))
        pycom.rgbled(LED['green'])

rtc.ntp_sync(NTP_ADDRESS)
ntp_synced = False
if rtc.synced():
    ntp_synced = True

include_timestamp = ntp_synced
while True:
    iline = readings_to_influxdb_line(take_readings(), STATION_MAC)
    print('sending data\n{}'.format(iline))
    influx_url = 'http://192.168.0.7:8086/write?db=farmdb'
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            pycom.rgbled(LED['blue'])
            urequests.post(influx_url, data=iline)
            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass
    pycom.rgbled(LED['black'])
    time.sleep(SENSOR_INTERVAL)
