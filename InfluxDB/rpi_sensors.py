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
import time
import sys


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

SAMPLE_WINDOW = 5
readings = {}
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    rate_cnt = 0
    while time.time() < sample_end:
        pass
    #readings = internal_sensor_readings()
    readings['distance'] = sensor.distance
    readings['flow_rate'] = flow_rate(SAMPLE_WINDOW)
    print("GOT DISTANCE {} FLOW RATE {}".format(readings['distance'], readings['flow_rate']))


