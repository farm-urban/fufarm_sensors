"""Example Usage:

LOCAL_TIMESTAMP = True
SENSOR_STATION_ID = "bruntwood"
MEASUREMENT = "sensors"
BUCKET = "ediblewalls"
# TOKEN = pGHNPOqH8TmwJpU6vko7us8fmTAXltGP_X4yKONTI6l9N-c2tWsscFtCab43qUJo5EcQE3696U9de5gn9NN4Bw==
TOKEN = open("TOKEN").readline().strip()
ORG = "farmurban"
INFLUX_URL = "http:/10.8.0.1:8086"
influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG,
    "token": TOKEN,
    "bucket": BUCKET,
}
sensor_influx_tags = {"station_id": SENSOR_STATION_ID}


readings = {'temperature': 25, 'light': 10}
influxdb.send_data_to_influx(
    influx_schema,
    MEASUREMENT,
    sensor_influx_tags,
    readings,
    local_timestamp=LOCAL_TIMESTAMP,
)

"""

import datetime
import logging
import requests
import time

MOCK = False
logger = logging.getLogger()


def send_data_to_influx(
    schema, measurement, tags, fields, timestamp=None, local_timestamp=False
):
    iline = readings_to_influxdb_line(
        measurement, tags, fields, timestamp=timestamp, local_timestamp=local_timestamp
    )
    return send_data(schema, iline)


def readings_to_influxdb_line(
    measurement, tags, fields, timestamp=None, local_timestamp=False
):
    if timestamp and local_timestamp:
        raise RuntimeError("Cannot include a timestamp with local_timestamp")

    tags = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fields = ",".join(
        ["{}={:e}".format(k, v) for k, v in fields.items() if v is not None]
    )
    iline = "{},{} {}".format(measurement, tags, fields)

    if timestamp or local_timestamp:
        if timestamp and isinstance(timestamp, datetime.datetime):
            timestamp = int(float(timestamp.strftime("%s.%f")) * 1000000000)
        if local_timestamp:
            # timestamp = int(float(datetime.datetime.utcnow().strftime("%s.%f"))*1000000000)
            # timestamp = int(time.time()*1000000000)
            timestamp = time.time_ns()
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
    logger.info(
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
            logger.debug(
                "Sent data - status_code: {} - text: {}".format(
                    response.status_code, response.text
                )
            )
            success = True
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.error("Network error: {}".format(e))
            tries += 1
            if number_of_retries > 0:
                retry = tries < number_of_retries
    return success
