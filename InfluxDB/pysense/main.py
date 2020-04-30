import binascii
import pycom
import machine
import utime
from machine import Pin
from network import WLAN
import sys

import hcsr04
import urequests
from pysense import Pysense  # Main pysense module.
from LTR329ALS01 import LTR329ALS01  # Ambient Light
from MPL3115A2 import MPL3115A2, PRESSURE  # Barometer and temperature
from SI7006A20 import SI7006A20  # Humidity & temperature.


LED = { 'amber' : 0xFF8000,
        'black' : 0x000000,
        'blue'  : 0x0000FF,
        'green' : 0x00FF00,
        'red'   : 0xFF0000 }

NETWORK_CONFIG_STR = """Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}"""


def reset_wlan(wlan=None):
    """Reset the WLAN to the default settings"""
    args = { 'mode' : WLAN.AP,
             'ssid' : "wipy-wlan-1734",
             'auth' : (WLAN.WPA2, "www.pycom.io"),
             'channel' : 6,
             'antenna' : WLAN.INT_ANT }
    if wlan:
        # wlan.deinit()
        wlan.init(**args)
    else:
        WLAN(**args)   
    return


def internal_sensor_readings():
    # pycom.rgbled(LED['green'])
    # print("Take readings")
    l0, l1 = light_sensor.light()
    return { 'barometer_pressure' : barometer.pressure(),
             'barometer_temperature' : barometer.temperature(),
             'humidity_humidity' : humidity_sensor.humidity(),
             'humidity_temperature' : humidity_sensor.temperature(),
             'ambient_light_0' : l0,
             'ambient_light_1' : l1 }
    # pycom.rgbled(LED['black'])


def readings_to_influxdb_line(readings, station_id, include_timestamp=False):
    data = ""
    for k, v in readings.items():
        data += 'fu_sensor,stationid={},sensor={} measurement={}' \
               .format(station_id,k,v)
        if include_timestamp is True:
            timestamp = utime.mktime(rtc.now())
            data += ' {}000000000'.format(timestamp)
        data += "\n"
    return data


def flow_rate(sample_window):
    """Calculate and return flow rate based on rate_cnt variable"""
    global rate_cnt
    return rate_cnt


def rate_pin_cb(arg):
    """Increment rate_cnt"""
    #print("got an interrupt in pin %s value %s" % (arg.id(), arg()))
    global rate_cnt, rate_pin_id
    if arg.id() == rate_pin_id:
        rate_cnt += 1


STATION_MAC = binascii.hexlify(machine.unique_id()).decode("utf-8")

# NETWORK_SSID = "virginmedia7305656"
# NETWORK_KEY = "vbvnqjxn"
# INFLUX_URL = 'http://192.168.0.7:8086/write?db=farmdb'
NETWORK_SSID = "FUsensors"
NETWORK_KEY = "12345678"
INFLUX_URL = 'http://192.168.4.1:8086/write?db=farmdb'
NTP_SERVER = 'pool.ntp.org'
SAMPLE_WINDOW = 60 * 10
HAVE_EXTERNAL_SENSORS = False

if not HAVE_EXTERNAL_SENSORS:
    hcsr04.MOCK = True

pycom.heartbeat(False)
pycom.rgbled(LED['amber'])
rtc = machine.RTC()  # Get date and time from server.
board = Pysense()
light_sensor = LTR329ALS01(board)
barometer = MPL3115A2(board, mode=PRESSURE)
humidity_sensor = SI7006A20(board)

ntp_synced = False
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

if not wlan.isconnected():
    pycom.rgbled(LED['red'])
    raise RuntimeError("Cannot find network!")

rtc.ntp_sync(NTP_SERVER)
if rtc.synced():
    ntp_synced = True

# initialise Ultrasonic Sensor pins
us_trigger_pin = Pin('P4', mode=Pin.OUT)
us_echo_pin = Pin('P10', mode=Pin.IN, pull=Pin.PULL_DOWN)
# Initialise flow sensors
rate_pin = Pin('P11', mode=Pin.IN, pull=Pin.PULL_UP) # Lopy4 specific: Pin('P20', mode=Pin.IN)
rate_pin_id = rate_pin.id()
# Pin seems to occasionally get 'stuck' on low so we just measure a
# transition and log that, as it doens't matter if it's going 1->0 or 0->1
rate_pin.callback(Pin.IRQ_FALLING, rate_pin_cb)

rate_cnt = 0
sample_end = 0
distance_sample_interval = 1
include_timestamp = ntp_synced
while True:
    sample_start = utime.time()
    sample_end = sample_start + SAMPLE_WINDOW
    rate_cnt = 0
    distance_samples = []
    loop_time = sample_start
    while utime.time() < sample_end:
        # The flow rate is calculated using the callback within this loop
        #print(echo(), end='')
        if utime.time() - loop_time >= distance_sample_interval:
            distance_samples.append(hcsr04.distance_measure(us_trigger_pin, us_echo_pin))
            loop_time = utime.time()
    pycom.rgbled(LED['blue'])
    readings = internal_sensor_readings()
    readings['distance'] = hcsr04.distance_median(distance_samples)
    readings['flow_rate'] = flow_rate(SAMPLE_WINDOW)
    iline = readings_to_influxdb_line(readings, STATION_MAC, include_timestamp=include_timestamp)
    print('sending data\n{}'.format(iline))
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            # pycom.rgbled(LED['blue'])
            urequests.post(INFLUX_URL, data=iline)
            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass
    if success:
        pycom.rgbled(LED['green'])
    else:
        pycom.rgbled(LED['red'])
    utime.sleep(5)
    pycom.rgbled(LED['black'])