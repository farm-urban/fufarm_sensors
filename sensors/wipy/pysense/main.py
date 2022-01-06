import binascii
import pycom
import machine
import uos
import utime
from machine import Pin
from machine import SD
from network import WLAN

import hcsr04
import urequests
from pysense import Pysense  # Main pysense module.
from LTR329ALS01 import LTR329ALS01  # Ambient Light
from MPL3115A2 import MPL3115A2, PRESSURE  # Barometer and temperature
from SI7006A20 import SI7006A20  # Humidity & temperature.


STATION_MAC = 'lfarm_2'
NETWORK_SSID = "FUsensors"
NETWORK_KEY = "12345678"
INFLUX_URL = 'http://192.168.4.1:8086/write?db=farmdb'
NTP_SERVER = 'pool.ntp.org'
SAMPLE_WINDOW = 60 * 10
HAVE_EXTERNAL_SENSORS = False
MOUNTPOINT = '/sd'
PATHSEP = "/"
HAVE_SD = False

LED = {
    'amber': 0xFF8000,
    'black': 0x000000,
    'blue': 0x0000FF,
    'green': 0x00FF00,
    'orange': 0xFFA500,
    'red': 0xFF0000
}

NETWORK_CONFIG_STR = """Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}"""


def reset_wlan(wlan=None):
    """Reset the WLAN to the default settings"""
    args = {
        'mode': WLAN.AP,
        'ssid': "wipy-wlan-1767 ",
        'auth': (WLAN.WPA2, "www.pycom.io"),
        'channel': 6,
        'antenna': WLAN.INT_ANT
    }
    if wlan:
        # wlan.deinit()
        wlan.init(**args)
    else:
        WLAN(**args)
    return


def connect_wireless(wlan):
    nets = wlan.scan()
    for net in nets:
        if net.ssid == NETWORK_SSID:
            print('Found network: {}'.format(NETWORK_SSID))
            wlan.connect(net.ssid, auth=(net.sec, NETWORK_KEY), timeout=5000)
            while not wlan.isconnected():
                machine.idle()  # save power while waiting
            print(NETWORK_CONFIG_STR.format(*wlan.ifconfig()))
    return wlan.isconnected()


def internal_sensor_readings():
    # pycom.rgbled(LED['green'])
    # print("Take readings")
    l0, l1 = light_sensor.light()
    return {
        'barometer_pressure': barometer.pressure(),
        'barometer_temperature': barometer.temperature(),
        'humidity_humidity': humidity_sensor.humidity(),
        'humidity_temperature': humidity_sensor.temperature(),
        'ambient_light_0': l0,
        'ambient_light_1': l1
    }


def take_readings(sample_window, have_external_sensors=False, distance_sample_interval=1):
    global rate_count, us_trigger_pin, us_echo_pin, LED
    sample_start = utime.time()
    sample_end = sample_start + sample_window
    rate_count = 0
    distance_samples = []
    sample_time = sample_start
    while utime.time() < sample_end:
        # The flow rate is calculated using the callback within this loop
        if utime.time() - sample_time >= distance_sample_interval:
            if have_external_sensors:
                distance_samples.append(
                    hcsr04.distance_measure(us_trigger_pin, us_echo_pin))
            sample_time = utime.time()
    readings = internal_sensor_readings()
    if have_external_sensors:
        readings['distance'] = hcsr04.distance_median(distance_samples)
        readings['flow_rate'] = flow_rate(sample_window)
    return readings


def send_data(iline):
    print('sending data\n{}'.format(iline))
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            # pycom.rgbled(LED['blue'])
            urequests.post(INFLUX_URL, data=iline)
            success = True
        except OSError as e:
            print('network error: {}'.format(e))
            number_of_retries -= 1
            pass
    return success


def readings_to_influxdb_line(readings, station_id, include_timestamp=False):
    data = ""
    for k, v in readings.items():
        data += 'fu_sensor,stationid={},sensor={} measurement={}' \
               .format(station_id, k, v)
        if include_timestamp is True:
            timestamp = utime.mktime(rtc.now())
            data += ' {}000000000'.format(timestamp)
        data += "\n"
    return data


def next_logfile(name_stem='logfile'):
    MAX_FILENAMES = 100
    count = 0
    while True:
        name = "{}_{}.csv".format(name_stem, count)
        logfile_path = MOUNTPOINT + PATHSEP + name
        file_exists = True
        try:
            uos.stat(logfile_path)
        except OSError:
            file_exists = False
        if not file_exists:
            break
        count += 1
        if count > MAX_FILENAMES:
            raise RuntimeError("Too many logfiles! {0}".format(logfile_path))
    return logfile_path


def init_logfile(readings, station_id):
    " Open the csv logfile and initialise it with the headings"
    logfile_path = next_logfile()
    logfile = open(logfile_path, 'w')
    headings = ['timestamp', 'stationid'] + sorted(readings.keys())
    logfile.write(",".join(headings) + "\n")
    logfile.flush()
    return logfile


def write_readings_to_logfile(logfile, readings, station_id):
    timestamp = str(utime.mktime(rtc.now()))
    values = [timestamp, station_id] + [str(readings[k]) for k in sorted(readings.keys())]
    logfile.write(",".join(values) + "\n")
    logfile.flush()
    return


def flow_rate(sample_window):
    """Calculate and return flow rate based on rate_count variable"""
    global rate_count
    return rate_count


def rate_pin_cb(arg):
    """Increment rate_count"""
    # print("got an interrupt in pin %s value %s" % (arg.id(), arg()))
    global rate_count, rate_pin_id
    if arg.id() == rate_pin_id:
        rate_count += 1

################################################################################
# Start Script
################################################################################
if STATION_MAC is None:
    STATION_MAC = binascii.hexlify(machine.unique_id()).decode("utf-8")

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
connect_wireless(wlan)
if wlan.isconnected():
    rtc.ntp_sync(NTP_SERVER)
    if rtc.synced():
        ntp_synced = True

if HAVE_EXTERNAL_SENSORS:
    # initialise Ultrasonic Sensor pins
    us_trigger_pin = Pin('P4', mode=Pin.OUT)
    us_echo_pin = Pin('P10', mode=Pin.IN, pull=Pin.PULL_DOWN)
    # Initialise flow sensors
    rate_pin = Pin('P11', mode=Pin.IN,
                   pull=Pin.PULL_UP)  # Lopy4 specific: Pin('P20', mode=Pin.IN)
    rate_pin_id = rate_pin.id()
    # Pin seems to occasionally get 'stuck' on low so we just measure a
    # transition and log that, as it doens't matter if it's going 1->0 or 0->1
    rate_pin.callback(Pin.IRQ_FALLING, rate_pin_cb)

# Setup SD card
try:
    sd = SD()
    HAVE_SD = True
except OSError:
    print("No disk available")

if HAVE_SD:
    uos.mount(sd, MOUNTPOINT)
    readings = take_readings(3, have_external_sensors=HAVE_EXTERNAL_SENSORS)
    print("Setting up logfile")
    logfile = init_logfile(readings, STATION_MAC)

rate_count = 0
include_timestamp = ntp_synced
notification_sleep = 5
loop_count = 0
while True:
    pycom.heartbeat(True)
    loop_count += 1
    print("Running loop ", loop_count)
    if not wlan.isconnected():
        print("Lost network connection")
        connect_wireless(wlan)
        if not wlan.isconnected():
            print("Could not reconnect to network")
    readings = take_readings(SAMPLE_WINDOW,
                             have_external_sensors=HAVE_EXTERNAL_SENSORS)
    if HAVE_SD:
        write_readings_to_logfile(logfile, readings, STATION_MAC)
    success = False
    if wlan.isconnected():
        iline = readings_to_influxdb_line(readings,
                                          STATION_MAC,
                                          include_timestamp=include_timestamp)
        success = send_data(iline)
    pycom.heartbeat(False)
    if success:
        pycom.rgbled(LED['green'])
    else:
        pycom.rgbled(LED['orange'])
    utime.sleep(notification_sleep)
