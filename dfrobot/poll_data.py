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
from influxdb_client.client.write_api import SYNCHRONOUS, PointSettings

def data2influx(write_api, data):
    # tags set as default
    d = {'time': datetime.utcnow(),
         'measurement': INFLUX_MEASUREMENT,
         'fields': data,
         'tags': dict()}
    #p = Point.from_dict(d, write_precision=WritePrecision.NS)
    write_api.write(BUCKET, ORG, d)


STATION_ID="rpiard1"
INFLUX_MEASUREMENT="LozExpt"

# You can generate a Token from the "Tokens Tab" in the UI
BUCKET = "LaurenceExperiments"
TOKEN = "HKlpgdVMvW_pyDemAnSkW1ZQHny14G5wFCAMQdrYR-20Nc_QlbVRJmEowXMxVGSus2O73TUm24hkwVQgWkkI2Q=="
ORG = "accounts@farmurban.co.uk"
client = InfluxDBClient(url="https://westeurope-1.azure.cloud2.influxdata.com", token=TOKEN)

point_settings = PointSettings()
point_settings.add_default_tag("station_id", STATION_ID)
write_api = client.write_api(write_options=SYNCHRONOUS, point_settings=point_settings)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [laurence_experiment]: %(message)s')
logger = logging.getLogger()
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.flush()
while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        try:
            data = json.loads(line)
            #logger.info("Got data:%s",data)
        except json.decoder.JSONDecodeError as e:
            logger.warning("Error reading data:%s",e)
            continue
        data2influx(write_api,data)
