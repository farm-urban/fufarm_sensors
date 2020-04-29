import os
import glob

os.system('modprobe w1-gpio')  #1-wire mode
os.system('modprobe w1-therm') #1-wire temperature probe
temp_sensor = '/sys/bus/w1/devices/28-01143840e3aa/w1_slave' #device address

def temp_read():
       t = open(temp_sensor, 'r')   #read output
       lines = t.readlines()
       t.close()

       temp_output = lines[1].find('t=')     #find temperature values in the output
       if temp_output != -1:
               temp_string = lines[1].strip()[temp_output+2:]
               temp_c = float(temp_string)/1000.0
               temp_c = round(temp_c,1)
               return temp_c

