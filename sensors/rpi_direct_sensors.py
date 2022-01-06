import logging
import time

# local imports
import influxdb
import direct_sensors_rpi


direct_sensors_rpi.USE_PIGPIOD = True

SAMPLE_WINDOW = 60 * 5
SAMPLE_WINDOW = 5
LOGLEVEL = logging.DEBUG
MOCK = True
influxdb.MOCK = MOCK

LOCAL_TIMESTAMP = True
SENSOR_STATION_ID = "farm"
MEASUREMENT = "sensors_direct"
BUCKET = "cryptfarm"
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


readings = {}
direct_sensors_rpi.setup_devices()
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    direct_sensors_rpi.reset_flow_counter()
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
