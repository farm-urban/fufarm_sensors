import logging
import time

# local imports
import influxdb
import direct_sensors_rpi


INFLUX_URL = "http://10.8.0.1:8086/write?db=farmdb"
STATION_MAC = "rpi2utc"
SAMPLE_WINDOW = 60 * 5
# SAMPLE_WINDOW = 5
MOCK = False
INFLUX_SCHEMA = {"measurement": "fu_sensors", "tags": {"station_id": STATION_MAC}}


SAMPLE_WINDOW = 60 * 5
SAMPLE_WINDOW = 5
LOGLEVEL = logging.DEBUG
MOCK = False
influxdb.MOCK = MOCK

LOCAL_TIMESTAMP = True
SENSOR_STATION_ID = "farm"
MEASUREMENT = "sensors"
BUCKET = "cryptfarm"
# TOKEN = "pGHNPOqH8TmwJpU6vko7us8fmTAXltGP_X4yKONTI6l9N-c2tWsscFtCab43qUJo5EcQE3696U9de5gn9NN4Bw=="
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


direct_sensors_rpi.reset_flow_counter()
readings = {}
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    pulse_count = 0
    while time.time() < sample_end:
        # Loop to accumulate flow pulses
        pass
    readings["flow_rate"] = direct_sensors_rpi.flow_rate(SAMPLE_WINDOW)
    time.sleep(2)  # Need to add in pause or the distance sensor or else it measures 0.0
    readings["distance"] = direct_sensors_rpi.distance_sensor.distance
    influxdb.send_data_to_influx(
        influx_schema,
        MEASUREMENT,
        sensor_influx_tags,
        readings,
        local_timestamp=LOCAL_TIMESTAMP,
    )
