import utime
import pycom
import machine
from machine import Pin
from network import WLAN

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

# Ultrasonic distance measurment
def distance_measure(timeout = 100000):
    """Ultrasonic distance measurement using HR-SO4

    Returns:
    --------
    Distance in centimetres

    References:
    -----------
    https://core-electronics.com.au/tutorials/hc-sr04-ultrasonic-sensor-with-pycom-tutorial.html
    https://github.com/mithru/MicroPython-Examples/blob/master/08.Sensors/HC-SR04/ultrasonic.py
    https://github.com/gpiozero/gpiozero/blob/master/gpiozero/input_devices.py
    """
    # trigger pulse LOW for 2us (just in case)
    us_trigger_pin(0)
    utime.sleep_us(2)
    # trigger HIGH for a 10us pulse
    us_trigger_pin(1)
    utime.sleep_us(10)
    us_trigger_pin(0)

    # wait for the rising edge of the echo then start timer
    i = 0
    while us_echo_pin() == 0 and i < timeout:
        i += 1
    start = utime.ticks_us()

    # wait for end of echo pulse then stop timer
    j = 0
    while us_echo_pin() == 1 and j < timeout:
        j += 1
    finish = utime.ticks_us()

    if i >= timeout - 1:
        print("Distance timed out on loop 1")
    if j >= timeout - 1:
        print("Distance timed out on loop 2")

    # pause for 20ms to prevent overlapping echos
    utime.sleep_ms(20)

    # calculate distance by using time difference between start and stop
    # speed of sound 340m/s or .034cm/us. Time * .034cm/us = Distance sound travelled there and back
    # divide by two for distance to object detected.
    distance = ((utime.ticks_diff(start, finish)) * .034)/2

    return distance

def distance_median(distance_samples):
    print("DISTANCE_MEDIAN measuring ",distance_samples)
    distance_samples = sorted(distance_samples)
    distance_median = distance_samples[int(len(distance_samples)/2)]
    return int(distance_median)

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

reset_wlan()
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
sample_window = 5
distance_sample_interval = 1
while True:
    sample_start = utime.time()
    sample_end = sample_start + sample_window
    rate_cnt = 0
    distance_samples = []
    loop_time = sample_start
    while utime.time() < sample_end:
        #print(echo(), end='')
        if utime.time() - loop_time >= distance_sample_interval:
            distance_samples.append(distance_measure())
            loop_time = utime.time()
    print("flow_rate {}".format(flow_rate(sample_window)))
    print("Distance median: {}".format(distance_median(distance_samples)))

