"""
# NAT forwarding
https://gist.github.com/kimus/9315140

# Map for GPIO on pi zero
https://cdn.sparkfun.com/assets/learn_tutorials/6/7/6/PiZerov2.pdf

https://gpiozero.readthedocs.io/en/stable/api_input.html#distancesensor-hc-sr04
https://gpiozero.readthedocs.io/en/stable/api_pins.html#gpiozero.pins.pigpio.PiGPIOFactory
sudo apt-get install  python3-gpiozero python3-pigpio
# Need to start as a service
sudo pigpiod

# waterproof JSN-SR04T
https://www.amazon.co.uk/Youmile-Measuring-Transducer-Ultrasonic-Waterproof/dp/B07YDG53MC/

"""
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import DigitalInputDevice
import requests
import time


INFLUX_URL = 'http://10.8.0.1:8086/write?db=farmdb'
STATION_MAC = 'rpizero1utc'
SAMPLE_WINDOW = 60 * 5
MOCK = False
rate_cnt = 0

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


def count_paddle():
    global rate_cnt
    rate_cnt += 1
    #print("button was pressed")

def flow_rate(sample_window):
    return rate_cnt

btn = DigitalInputDevice(22)
btn.when_activated = count_paddle

factory = PiGPIOFactory()
sensor = DistanceSensor(trigger=17, echo=27, pin_factory=factory)

readings = {}
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    rate_cnt = 0
    while time.time() < sample_end:
        pass
    readings['flow_rate'] = flow_rate(SAMPLE_WINDOW)
    time.sleep(1) # Need to add in pause or the distance sensor or else it measures 0.0
    readings['distance'] = sensor.distance
    iline = readings_to_influxdb_line(readings, STATION_MAC)
    success = send_data(iline)
