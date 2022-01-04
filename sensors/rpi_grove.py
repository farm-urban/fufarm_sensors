#!/usr/bin/env python3

import grove_sensors
from collections import namedtuple
import logging
import requests
import sys
import time


INFLUX_URL = "http://10.8.0.1:8086/write?db=bruntwood"
STATION_MAC = "bruntwood"
SAMPLE_WINDOW = 60 * 5
SAMPLE_WINDOW = 5
MOCK = True
grove_sensors.MOCK = MOCK

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [bruntwood_sensors]: %(message)s"
)
logger = logging.getLogger()


def readings_to_influxdb_line(readings, station_id, include_timestamp=False):
    data = ""
    for k, v in readings.items():
        data += "fu_sensor,stationid={},sensor={} measurement={}".format(
            station_id, k, v
        )
        if include_timestamp is True:
            timestamp = utime.mktime(rtc.now())
            data += " {}000000000".format(timestamp)
        data += "\n"
    return data


def send_data(iline):
    if MOCK:
        logger.info("sending data{}".format(iline))
        return
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            requests.post(INFLUX_URL, data=iline)
            success = True
        except Exception as e:
            logger.warn("network error: {}".format(e))
            number_of_retries -= 1
            pass
    return success


grove_sensors.setup_sensors()
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    rate_cnt = 0
    while time.time() < sample_end:
        pass
    time.sleep(2)  # Need to add in pause or the distance sensor or else it measures 0.0
    readings = grove_sensors.take_readings()
    iline = readings_to_influxdb_line(readings, STATION_MAC)
    success = send_data(iline)
