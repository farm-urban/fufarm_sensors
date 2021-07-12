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


def send_data_to_influx(schema, measurement, tags, fields, include_timestamp=False):
    iline = readings_to_influxdb_line(measurement, tags, fields, include_timestamp=include_timestamp)
    return send_data(schema, iline)


def readings_to_influxdb_line(measurement, tags, fields, include_timestamp=False):
    tags = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fields = ",".join(["{}={:e}".format(k, v) for k, v in fields.items() if v is not None])
    iline = "{},{} {}".format(measurement, tags, fields)
    if include_timestamp is True:
        timestamp = int(time.time()*1000000000)
        iline += " {}".format(timestamp)
    iline += "\n"
    return iline


def send_data(schema, iline):
    """
    https://docs.influxdata.com/influxdb/v2.0/api/#tag/Write
    https://docs.influxdata.com/influxdb/v2.0/write-data/developer-tools/api/
    """
    url = "{}/api/v2/write".format(schema["endpoint"])
    params = {"org": schema["org"], "bucket": schema["bucket"]}
    headers = {"Authorization": "Token {}".format(schema["token"])}
    logger.debug(
        "Sending url: {} params: {} headers: {} data: {}".format(
            url, params, headers, iline
        )
    )
    if MOCK:
        return
    success = False
    retry = True
    number_of_retries = 3
    tries = 0
    while retry:
         try:
            response = requests.post(url, headers=headers, params=params, data=iline)
            logger.debug("Sent data - status_code: {}\ntext: {}".format(response.status_code, response.text))
            success = True
            break
         except (requests.exceptions.ConnectionError,
                 requests.exceptions.Timeout) as e:
            logger.error("Network error: {}".format(e))
            tries += 1
            if number_of_retries > 0:
                retry = tries < number_of_retries
    return success


MOCK = True
POLL_INTERVAL = 5*60
POLL_INTERVAL = 5
LOG_LEVEL = logging.DEBUG

STATION_ID = "rpiard1"
MEASUREMENT = "LozExpt"
BUCKET = "Loz_test"
TOKEN = "SibMj38WbdjAWgrjZMRF2aBCeiE3vK44drLuG-Ioee9C-cTPJydc9KoBFu1-A9vEa4vAzwjX-WjKBulAOrkcXA=="
ORG = "accounts@farmurban.co.uk"
INFLUX_URL = "https://westeurope-1.azure.cloud2.influxdata.com"
ARDUINO_TERMINAL = "/dev/ttyACM0"
INCLUDE_TIMESTAMP = True

influx_tags = {"station_id": STATION_ID}
influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG,
    "token": TOKEN,
    "bucket": BUCKET,
}


logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s [loz_experiment]: %(message)s"
)
logger = logging.getLogger()

ser = serial.Serial(ARDUINO_TERMINAL, 9600, timeout=1)
ser.flush()
while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode("utf-8").rstrip()
        try:
            data = json.loads(line)
            # logger.info("Got data:%s",data)
        except json.decoder.JSONDecodeError as e:
            logger.warning("Error reading Arduino data: %s\nDoc was: %s", e.msg, e.doc)
            continue
        send_data_to_influx(influx_schema, MEASUREMENT, influx_tags, data, include_timestamp=INCLUDE_TIMESTAMP)
        time.sleep(POLL_INTERVAL)
