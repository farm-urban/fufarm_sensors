import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
PIN_TRIG = 23 #Trigger GPIO pin = 23
PIN_ECHO = 24 #Echo GPIO pin = 24

GPIO.setup(PIN_TRIG, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)

GPIO.output(PIN_TRIG, False)

time.sleep(2) #time to set

def distance():
    GPIO.output(PIN_TRIG, True)  #sending an impulse
    time.sleep(0.00001)
    GPIO.output(PIN_TRIG, False)

    while GPIO.input(PIN_ECHO)==0:
         pulse_start_time = time.time()  #calculating time
    while GPIO.input(PIN_ECHO)==1:
         pulse_end_time = time.time()    #impulse received

    pulse_duration = pulse_end_time - pulse_start_time
    dist = round(pulse_duration * 17150, 1) #distance = time * speed of sound
    return dist

    GPIO.cleanup()

