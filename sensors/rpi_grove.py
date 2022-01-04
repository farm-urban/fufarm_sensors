#!/usr/bin/env python3

import grove_sensors
import logging
import requests
import time

# local imports
import influxdb


SAMPLE_WINDOW = 60 * 5
SAMPLE_WINDOW = 5
MOCK = True
grove_sensors.MOCK = MOCK
influxdb.MOCK = MOCK

LOCAL_TIMESTAMP = True
SENSOR_STATION_ID = "bruntwood"
MEASUREMENT = "sensors"
BUCKET = "ediblewalls"
TOKEN = "pGHNPOqH8TmwJpU6vko7us8fmTAXltGP_X4yKONTI6l9N-c2tWsscFtCab43qUJo5EcQE3696U9de5gn9NN4Bw=="
# TOKEN = open("TOKEN").readline().strip()
ORG = "farmurban"
INFLUX_URL = "http:/10.8.0.1:8086"
influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG,
    "token": TOKEN,
    "bucket": BUCKET,
}
sensor_influx_tags = {"station_id": SENSOR_STATION_ID}


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [bruntwood_sensors]: %(message)s"
)
logger = logging.getLogger()


grove_sensors.setup_sensors()
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    rate_cnt = 0
    while time.time() < sample_end:
        pass
    time.sleep(2)  # Need to add in pause or the distance sensor or else it measures 0.0
    readings = grove_sensors.take_readings()
    influxdb.send_data_to_influx(
        influx_schema,
        MEASUREMENT,
        sensor_influx_tags,
        readings,
        local_timestamp=LOCAL_TIMESTAMP,
    )
