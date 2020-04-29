import sys

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/ABElectronics_Python_Libraries/ADCPi')
from ADCPi import ADCPi

import time

ch = 1

#values from calibration process
x1 = 0.126  #voltage from value n1
x2 = 1.085  #voltage from value n2
y2 = 12.88
y1 = 1.413

#linear approximation
m = (y2 - y1)/(x2 - x1)
q = y1 - m*x1

def EC_read():

        adc = ADCPi (0x68, 0x69, 18)  #I2C ACDPi address, sample rate
        voltage = (adc.read_voltage(ch))
        EC = m*voltage + q
        EC = round(EC, 2)
        return EC

