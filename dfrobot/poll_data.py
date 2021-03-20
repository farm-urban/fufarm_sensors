#!/usr/bin/env python3
"""
sudo apt-get install python3-serial

Can also use:
screen -S arduino  /dev/ttyACM0 9600

Kill session: ctrl-A K 

"""
import logging
import json
import requests
import serial
import time

from datetime import datetime

def send_data(auth_data, iline):
    # https://docs.influxdata.com/influxdb/v2.0/api/#tag/Write
    # https://docs.influxdata.com/influxdb/v2.0/write-data/developer-tools/api/
    url = "{}/api/v2/write".format(auth_data['endpoint'])
    params = {'org': auth_data['org'],
              'bucket': auth_data['bucket']}
    headers = {'Authorization': 'Token {}'.format(auth_data['token'])}
    logger.info("Sending url: {} params: {} headers: {} data: {}".format(url, params, headers, data))
    if MOCK:
        return
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            response = requests.post(url, headers=headers, params=params, data=iline)
            success = True
        except Exception as e:
            print('network error: {}'.format(e))
            number_of_retries -= 1
            pass
    return success


def readings_to_influxdb_line(schema, readings, include_timestamp=False):
    measurement = schema['measurement']
    tags = ",".join(["{}={}".format(k,v) for k,v in schema['tags'].items()])
    fields = ",".join(["{}={}".format(k,v) for k,v in readings.items()])
    iline = "{},{} {}".format(measurement, tags, fields)
    if include_timestamp is True:
        timestamp = datetime.utcnow()
        iline += ' {}000000000'.format(timestamp)
    iline += "\n"
    return iline


MOCK = False
POLL_INTERVAL = 5
MEASUREMENT = 'LozExpt'
STATION_ID = "rpiard1"
BUCKET = "LaurenceExperiments"
TOKEN = "HKlpgdVMvW_pyDemAnSkW1ZQHny14G5wFCAMQdrYR-20Nc_QlbVRJmEowXMxVGSus2O73TUm24hkwVQgWkkI2Q=="
ORG = "accounts@farmurban.co.uk"
INFLUX_ENDPOINT = "https://westeurope-1.azure.cloud2.influxdata.com"


INFLUX_SCHEMA = { 'bucket': BUCKET,
                  'measurement': MEASUREMENT,
                  'tags': {'station_id' : STATION_ID}}

AUTHORISATION_DATA = {'endpoint': INFLUX_ENDPOINT,
                      'org': ORG,
                      'token': TOKEN,
                      'bucket': BUCKET
}

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
        iline = readings_to_influxdb_line(INFLUX_SCHEMA, data, include_timestamp=False)
        send_data(AUTHORISATION_DATA, iline)
        time.sleep(POLL_INTERVAL)
