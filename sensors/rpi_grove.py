#!/usr/bin/env python3
import logging
import time

# local imports
import grove_sensors
import influxdb


SAMPLE_WINDOW = 60 * 5
LOGLEVEL=logging.DEBUG
MOCK = False
grove_sensors.MOCK = MOCK
influxdb.MOCK = MOCK

LOCAL_TIMESTAMP = True
SENSOR_STATION_ID = "bruntwood"
MEASUREMENT = "sensors"
BUCKET = "ediblewalls"
TOKEN = open("TOKEN").readline().strip()
ORG = "farmurban"
INFLUX_URL = "http://farmuaa6.vpn.farmurban.co.uk:8086"
influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG,
    "token": TOKEN,
    "bucket": BUCKET,
}
sensor_influx_tags = {"station_id": SENSOR_STATION_ID}


logging.basicConfig(
    level=LOGLEVEL, format="%(asctime)s [bruntwood_sensors]: %(message)s"
)
logger = logging.getLogger()


grove_sensors.setup_sensors()
loopcount = 0
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    if loopcount > 0:
        # Always take intial readings - for check/debug purposes
        while time.time() < sample_end:
            pass
    readings = grove_sensors.take_readings()
    influxdb.send_data_to_influx(
        influx_schema,
        MEASUREMENT,
        sensor_influx_tags,
        readings,
        local_timestamp=LOCAL_TIMESTAMP,
    )
    loopcount += 1
