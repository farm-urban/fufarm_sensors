"""
# NAT forwarding
https://gist.github.com/kimus/9315140

# Map for GPIO on pi zero
https://cdn.sparkfun.com/assets/learn_tutorials/6/7/6/PiZerov2.pdf

https://gpiozero.readthedocs.io/en/stable/api_input.html#distancesensor-hc-sr04
https://gpiozero.readthedocs.io/en/stable/api_pins.html#gpiozero.pins.pigpio.PiGPIOFactory

http://abyz.me.uk/rpi/pigpio/python.html
sudo apt-get install  python3-gpiozero python3-pigpio

# Need to start as a service
sudo pigpiod

# Wiring diagram HC-SR04
https://thepihut.com/blogs/raspberry-pi-tutorials/hc-sr04-ultrasonic-range-sensor-on-the-raspberry-pi

# YF-S201
https://www.hobbytronics.co.uk/yf-s201-water-flow-meter
Requires +5V so need to use voltage divider

Red ---------------- 5V

             +------ GPIO 22
             |
             |
             |
Yellow --1K--+--2K-- GND

Black -------------- GND

# waterproof JSN-SR04T
https://www.amazon.co.uk/Youmile-Measuring-Transducer-Ultrasonic-Waterproof/dp/B07YDG53MC/

"""
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import DigitalInputDevice
import requests
import time


INFLUX_URL = 'http://10.8.0.1:8086/write?db=farmdb'
STATION_MAC = 'rpi2utc'
SAMPLE_WINDOW = 60 * 5
#SAMPLE_WINDOW = 5
MOCK = False
USE_PIGPIOD = False
INFLUX_SCHEMA = { 'measurement': 'fu_sensors',
                  'tags': {'station_id' : STATION_MAC}}


def send_data(iline):
    print('sending data\n{}'.format(iline))
    if MOCK:
        return
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            requests.post(INFLUX_URL, data=iline)
            success = True
        except Exception as e:
            print('network error: {}'.format(e))
            number_of_retries -= 1
            pass
    return success


def readings_to_influxdb_line(schema, readings, include_timestamp=False):
    measurement = schema['measurement']
    tags = ",".join(["{}={}".format(k,v) for k,v in schema['tags'].items()])
    fields = ",".join(["{}={}".format(k,v) for k,v in readings.items()])
    iline = "{},{} {}".format(measurement, tags, fields)
    if include_timestamp is True:
        timestamp = utime.mktime(rtc.now())
        iline += ' {}000000000'.format(timestamp)
    iline += "\n"
    return iline


def count_paddle():
    global pulse_count
    pulse_count += 1
    # print("button was pressed")


def flow_rate(sample_window):
    """From YF-S201 manual:
    Pluse Characteristic:F=7Q(L/MIN).
    2L/MIN=16HZ 4L/MIN=32.5HZ 6L/MIN=49.3HZ 8L/MIN=65.5HZ 10L/MIN=82HZ

    sample_window is in seconds, so hz is pulse_count / sample_window
    """
    hertz = pulse_count / sample_window
    return hertz / 7.0


btn = DigitalInputDevice(22)
btn.when_activated = count_paddle

factory = None
if USE_PIGPIOD:
    factory = PiGPIOFactory()
sensor = DistanceSensor(trigger=17, echo=27, pin_factory=factory, queue_len=20)

pulse_count = 0
readings = {}
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    pulse_count = 0
    while time.time() < sample_end:
        pass
    readings['flow_rate'] = flow_rate(SAMPLE_WINDOW)
    time.sleep(2)  # Need to add in pause or the distance sensor or else it measures 0.0
    readings['distance'] = sensor.distance
    iline = readings_to_influxdb_line(INFLUX_SCHEMA, readings)
    success = send_data(iline)
