#!/usr/bin/env python3
"""
Can also use:
screen -S arduino  /dev/ttyACM0 9600

Kill session: ctrl-A K 

"""
import logging
import json
import serial

from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

def data2influx(write_api, data):
    data = "mem,host=host1 used_percent=23.43234543"
    #write_api.write(bucket, org, data)

sequence = ["mem,host=host1 used_percent=23.43234543",
            "mem,host=host1 available_percent=15.856523"]
write_api.write(bucket, org, sequence)
   data = ""
    for k, v in readings.items():
        data += 'fu_sensor,stationid={},sensor={} measurement={}' \
               .format(station_id, k, v)
        if include_timestamp is True:
            timestamp = utime.mktime(rtc.now())
            data += ' {}000000000'.format(timestamp)
        data += "\n"



# You can generate a Token from the "Tokens Tab" in the UI
token = "HKlpgdVMvW_pyDemAnSkW1ZQHny14G5wFCAMQdrYR-20Nc_QlbVRJmEowXMxVGSus2O73TUm24hkwVQgWkkI2Q=="
org = "accounts@farmurban.co.uk"
bucket = "LaurenceExperiments"
client = InfluxDBClient(url="https://westeurope-1.azure.cloud2.influxdata.com", token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)


logging.basicConfig(level=logging.INFO, format='%(asctime)s [laurence_experiment]: %(message)s')
logger = logging.getLogger()
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.flush()
while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        try:
            data = json.loads(line)
            logger.info("Got data:%s",data)
        except json.decoder.JSONDecodeError as e:
            logger.warning("Error reading data:%s",e)
            continue
       data2influx(write_api,data)
