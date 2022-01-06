"""
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


Example use:
import direct_sensors_rpi
SAMPLE_WINDOW = 5

direct_sensors_rpi.reset_flow_counter()
direct_sensors_rpi.setup_devices()
readings = {}
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    pulse_count = 0
    while time.time() < sample_end:
        # Loop to accumulate flow pulses
        pass
    readings["flow_rate"] = direct_sensors_rpi.flow_rate(SAMPLE_WINDOW)
    time.sleep(2)  # Need to add in pause or the distance sensor or else it measures 0.0
    readings["distance"] = direct_sensors_rpi.distance_sensor.distance

"""
import logging

from gpiozero import DistanceSensor
from gpiozero import DigitalInputDevice
from gpiozero.pins.native import NativeFactory
from gpiozero.pins.pigpio import PiGPIOFactory


TRIGGER_PIN = 17
ECHO_PIN = 27
FLOW_PIN = 22
USE_PIGPIOD = False

pulse_count = 0
btn = None
distance_sensor = None

logger = logging.getLogger()


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


def reset_flow_counter():
    global pulse_count
    pulse_count = 0


def setup_devices():
    global btn, distance_sensor
    btn = DigitalInputDevice(FLOW_PIN)
    btn.when_activated = count_paddle

    factory = NativeFactory()
    if USE_PIGPIOD:
        factory = PiGPIOFactory()
    else:
        factory = NativeFactory()

    distance_sensor = DistanceSensor(
        trigger=TRIGGER_PIN, echo=ECHO_PIN, pin_factory=factory, queue_len=20, partial=True
    )
