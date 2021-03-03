#!/usr/bin/env python3
"""
Can also use:
screen -S arduino  /dev/ttyACM0 9600

Kill session: ctrl-A K 

"""
import serial
import json
if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.flush()
    i = 0
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            i += 1
            print(i)
            try:
                x = json.loads(line)
                print(x)
                print(x["temperature"])
            except json.decoder.JSONDecodeError as e:
                print(line)
