import sys

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/ABElectronics_Python_Libraries/ADCPi')
from ADCPi import ADCPi

import time

ch = 2  #ACDPi channel 

#values from calibration process
x1 = 1.170   #voltage n1
x2 = 2.035   #voltage n2
y2 = 7
y1 = 4

#linear approximation
m = (y2 - y1)/(x2 - x1)
q = y1 - m*x1

def pH_read():

        adc = ADCPi (0x68, 0x69, 18)
        voltage = (adc.read_voltage(ch))
        pH = m*voltage + q
        pH = round(pH, 1)
        return pH
