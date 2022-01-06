import utime

MOCK = False

def distance_measure(trigger_pin, echo_pin, timeout = 100000):
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
    if MOCK:
        return 0.0

    # trigger pulse LOW for 2us (just in case)
    trigger_pin(0)
    utime.sleep_us(2)
    # trigger HIGH for a 10us pulse
    trigger_pin(1)
    utime.sleep_us(10)
    trigger_pin(0)

    # wait for the rising edge of the echo then start timer
    i = 0
    while echo_pin() == 0 and i < timeout:
        i += 1
    start = utime.ticks_us()

    # wait for end of echo pulse then stop timer
    j = 0
    while echo_pin() == 1 and j < timeout:
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
    if MOCK:
        return 0
    #print("DISTANCE_MEDIAN measuring ",distance_samples)
    distance_samples = sorted(distance_samples)
    distance_median = distance_samples[int(len(distance_samples)/2)]
    return int(distance_median)