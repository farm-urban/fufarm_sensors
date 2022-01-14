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


MAC_ADDRESS = binascii.hexlify(machine.unique_id()).decode("utf-8")
mac_address_to_station_id = {
    "30aea44e7b60": "farmwipy1",
    "3c71bf86f644": "farmwipy2",
    "3c71bf881410": "farmwipy3",
    "30aea42d1734": "farmwipy4",
}
SENSOR_STATION_ID = mac_address_to_station_id[MAC_ADDRESS]

NETWORK_SSID = "LLS_BYOD"
NETWORK_KEY = ""
# NETWORK_SSID = "Farm Urban"
# NETWORK_KEY = "v8fD53Rs"
# NETWORK_SSID = "PLUSNET-K9PM"
# NETWORK_KEY = "925c9c64a5"

MOCK = False
SAMPLE_WINDOW = 60 * 10

if SENSOR_STATION_ID == "farmwipy1":
    BAROMETER_TEMPERATURE_CORRECTION = -5.9
    HUMIDITY_TEMPERATURE_CORRECTION = -7.75
elif SENSOR_STATION_ID == "farmwipy2":
    BAROMETER_TEMPERATURE_CORRECTION = 0.0
    HUMIDITY_TEMPERATURE_CORRECTION = 0.0
elif SENSOR_STATION_ID == "farmwipy3":
    BAROMETER_TEMPERATURE_CORRECTION = -5.3
    HUMIDITY_TEMPERATURE_CORRECTION = -7.15
elif SENSOR_STATION_ID == "farmwipy3":
    BAROMETER_TEMPERATURE_CORRECTION = 0.0
    HUMIDITY_TEMPERATURE_CORRECTION = 0.0
else:
    BAROMETER_TEMPERATURE_CORRECTION = 0.0
    HUMIDITY_TEMPERATURE_CORRECTION = 0.0

MEASUREMENT = "sensors"
BUCKET = "cryptfarm"
TOKEN = "scW9V68kenPTzEkGUAtky-7awOMuo71pPGnCJ3gEdJWNNFBrlvp5atHTSFttVY4rRj0796xBgkuaF_YkSQExBg=="
# TOKEN = open("TOKEN").readline().strip()
ORG = "Farm Urban"
INFLUX_URL = "http://farmuaa1.farmurban.co.uk:8086"
influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG,
    "token": TOKEN,
    "bucket": BUCKET,
}
sensor_influx_tags = {"station_id": SENSOR_STATION_ID}


HAVE_SD = False
HAVE_EXTERNAL_SENSORS = False
NTP_SERVER = "pool.ntp.org"

# SD variables
MOUNTPOINT = "/sd"
PATHSEP = "/"

LED = {
    "amber": 0xFF8000,
    "black": 0x000000,
    "blue": 0x0000FF,
    "green": 0x00FF00,
    "orange": 0xFFA500,
    "red": 0xFF0000,
}

NETWORK_CONFIG_STR = """Network config:
IP          : {0}
Subnet mask : {1}
Gateway     : {2}
DNS server  : {3}"""


def reset_wlan(wlan=None):
    """Reset the WLAN to the default settings"""
    args = {
        "mode": WLAN.AP,
        "ssid": "wipy-wlan-1767 ",
        "auth": (WLAN.WPA2, "www.pycom.io"),
        "channel": 6,
        "antenna": WLAN.INT_ANT,
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
            print("Found network: {}".format(NETWORK_SSID))
            wlan.connect(net.ssid, auth=(net.sec, NETWORK_KEY), timeout=5000)
            while not wlan.isconnected():
                machine.idle()  # save power while waiting
            print(NETWORK_CONFIG_STR.format(*wlan.ifconfig()))
    return wlan.isconnected()


def internal_sensor_readings():
    """
    Recalibration against the farm sensors:

    barometer_temperature - 31.5
    humidity_temperature - 33.35
    temp pi - 25.6

    """
    # pycom.rgbled(LED['green'])
    # print("Take readings")
    l0, l1 = light_sensor.light()
    return {
        "barometer_pressure": barometer.pressure(),
        "barometer_temperature": barometer.temperature()
        + BAROMETER_TEMPERATURE_CORRECTION,
        "humidity_humidity": humidity_sensor.humidity(),
        "humidity_temperature": humidity_sensor.temperature()
        + HUMIDITY_TEMPERATURE_CORRECTION,
        "ambient_light_0": l0,
        "ambient_light_1": l1,
    }


def take_readings(
    sample_window, have_external_sensors=False, distance_sample_interval=1
):
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
                    hcsr04.distance_measure(us_trigger_pin, us_echo_pin)
                )
            sample_time = utime.time()
    readings = internal_sensor_readings()
    if have_external_sensors:
        readings["distance"] = hcsr04.distance_median(distance_samples)
        readings["flow_rate"] = flow_rate(sample_window)
    return readings


def send_data_to_influx(
    schema, measurement, tags, fields, timestamp=None, local_timestamp=False
):
    iline = readings_to_influxdb_line(
        measurement, tags, fields, timestamp=timestamp, local_timestamp=local_timestamp
    )
    return send_data(schema, iline)


def readings_to_influxdb_line(
    measurement, tags, fields, timestamp=None, local_timestamp=False
):
    if timestamp and local_timestamp:
        raise RuntimeError("Cannot include a timestamp with local_timestamp")

    tags = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fields = ",".join(
        ["{}={:e}".format(k, v) for k, v in fields.items() if v is not None]
    )
    iline = "{},{} {}".format(measurement, tags, fields)

    if timestamp or local_timestamp:
        # if timestamp and isinstance(timestamp, datetime.datetime):
        if timestamp:
            timestamp = int(float(timestamp.strftime("%s.%f")) * 1000000000)
        if local_timestamp:
            timestamp = int(utime.mktime(rtc.now()) * 100000000)
            # timestamp = "{}000000000".format(timestamp)
        iline += " {}".format(timestamp)

    iline += "\n"
    return iline


def send_data(schema, iline):
    """
    https://docs.influxdata.com/influxdb/v2.0/api/#tag/Write
    https://docs.influxdata.com/influxdb/v2.0/write-data/developer-tools/api/
    """
    url = "{}/api/v2/write".format(schema["endpoint"])
    params = {"org": schema["org"], "bucket": schema["bucket"]}
    headers = {"Authorization": "Token {}".format(schema["token"])}
    url = url_encode(url, params)
    print("Sending url: {} headers: {} data: {}".format(url, headers, iline))
    if MOCK:
        return
    success = False
    retry = True
    number_of_retries = 3
    tries = 0
    while retry:
        try:
            response = urequests.post(url, headers=headers, data=iline)
            print("Sent data - status_code: {}".format(response.status_code))
            success = True
            retry = False
            break
        except Exception as e:
            print("Network error: {}".format(e))
            tries += 1
            if number_of_retries > 0:
                retry = tries < number_of_retries
    return success


def url_encode(url, params):
    url_encode_table = {
        " ": "%20",
        "!": "%21",
        '"': "%22",
        "#": "%23",
        "$": "%24",
        "%": "%25",
        "&": "%26",
        "'": "%27",
        "(": "%28",
        ")": "%29",
        "*": "%2A",
        "+": "%2B",
        ",": "%2C",
        "-": "%2D",
        ".": "%2E",
        "/": "%2F",
        ":": "%3A",
        ";": "%3B",
        "<": "%3C",
        "=": "%3D",
        ">": "%3E",
        "?": "%3F",
        "@": "%40",
        "[": "%5B",
        "]": "%5D",
        "^": "%5E",
        "_": "%5F",
    }

    # Encode all characters in the keys and values of the params dict
    params = {
        "".join([url_encode_table.get(s, s) for s in k]): "".join(
            [url_encode_table.get(s, s) for s in v]
        )
        for k, v in params.items()
    }
    url += "?" + "&".join(["{}={}".format(k, v) for k, v in params.items()])
    return url


def next_logfile(name_stem="logfile"):
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
    "Open the csv logfile and initialise it with the headings"
    logfile_path = next_logfile()
    logfile = open(logfile_path, "w")
    headings = ["timestamp", "stationid"] + sorted(readings.keys())
    logfile.write(",".join(headings) + "\n")
    logfile.flush()
    return logfile


def write_readings_to_logfile(logfile, readings, station_id):
    timestamp = str(utime.mktime(rtc.now()))
    values = [timestamp, station_id] + [
        str(readings[k]) for k in sorted(readings.keys())
    ]
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
if not HAVE_EXTERNAL_SENSORS:
    hcsr04.MOCK = True

pycom.heartbeat(False)
pycom.rgbled(LED["amber"])
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
    us_trigger_pin = Pin("P4", mode=Pin.OUT)
    us_echo_pin = Pin("P10", mode=Pin.IN, pull=Pin.PULL_DOWN)
    # Initialise flow sensors
    rate_pin = Pin(
        "P11", mode=Pin.IN, pull=Pin.PULL_UP
    )  # Lopy4 specific: Pin('P20', mode=Pin.IN)
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
    logfile = init_logfile(readings, SENSOR_STATION_ID)

rate_count = 0
LOCAL_TIMESTAMP = ntp_synced
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
    readings = take_readings(SAMPLE_WINDOW, have_external_sensors=HAVE_EXTERNAL_SENSORS)
    if HAVE_SD:
        write_readings_to_logfile(logfile, readings, SENSOR_STATION_ID)
    success = False
    if wlan.isconnected():
        success = send_data_to_influx(
            influx_schema,
            MEASUREMENT,
            sensor_influx_tags,
            readings,
            local_timestamp=LOCAL_TIMESTAMP,
        )
    pycom.heartbeat(False)
    if success:
        pycom.rgbled(LED["green"])
    else:
        pycom.rgbled(LED["orange"])
    utime.sleep(notification_sleep)
