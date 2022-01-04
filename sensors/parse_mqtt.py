#!/usr/bin/python3
from datetime import datetime

with open("/var/log/mosquitto/mosquitto.log") as f:
    for line in f:
        x = line.strip().split(":")
        d = datetime.fromtimestamp(int(x[0])).strftime("%m/%d/%Y %H:%M:%S")
        print(f"{d}:{x[1]}")
        
    
