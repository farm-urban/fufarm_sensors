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
import time
import paho.mqtt.client as mqtt

from datetime import datetime


def send_data_to_influx(schema, data, include_timestamp=False):
    iline = readings_to_influxdb_line(schema, data, include_timestamp=include_timestamp)
    return send_data(schema, iline)


def readings_to_influxdb_line(schema, readings, include_timestamp=False):
    measurement = schema["measurement"]
    tags = ",".join(["{}={}".format(k, v) for k, v in schema["tags"].items()])
    fields = ",".join(["{}={:e}".format(k, v) for k, v in readings.items()])
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


MOCK = False
LOG_LEVEL = logging.DEBUG

STATION_ID = "rpie"
MEASUREMENT = "EnergyTest"
BUCKET = "HeathPower"
TOKEN = "BvQj3U3Ldwvz5bP6FPa58Rv9tzIDxVC4eY5C8UVlKfyZxKGWh8vjuxe7sMFvTjSLHmKfkh3nXQooGXBbJWjgow=="
ORG = "accounts@farmurban.co.uk"
INFLUX_URL = "https://westeurope-1.azure.cloud2.influxdata.com"
INCLUDE_TIMESTAMP = True

influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG,
    "token": TOKEN,
    "bucket": BUCKET,
    "measurement": MEASUREMENT,
    "tags": {"station_id": STATION_ID},
}


logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s [loz_experiment]: %(message)s"
)
logger = logging.getLogger()

client = mqtt.Client()
#client.username_pw_set(username, password=None)
client.connect("192.168.4.1", port=1883)
client.subscribe("tele/tasmota_5014E2/SENSOR")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, message):
    """
    {'Time': '1970-01-01T00:27:09', 'ENERGY': {'TotalStartTime': '2021-07-10T11:54:41', 'Total': 0.002, 'Yesterday': 0.0, 'Today': 0.002, 'Period': 0, 'Power': 0, 'ApparentPower': 0, 'ReactivePower': 0, 'Factor': 0.0, 'Voltage': 0, 'Current': 0.0}}
    """
    decoded_message = str(message.payload.decode("utf-8"))
    logger.log(logging.INFO, f"received message on topic [{message.topic}]: {decoded_message}")
    try:
        data = json.loads(decoded_message)
        #logger.info("Got data:%s",data)
    except json.decoder.JSONDecodeError as e:
        logger.warning("Error reading Arduino data: %s\nDoc was: %s", e.msg, e.doc)
    data = data['ENERGY']
    data.pop('TotalStartTime')
    send_data_to_influx(influx_schema, data, include_timestamp=INCLUDE_TIMESTAMP)

client.on_message = on_message
client.on_connect = on_connect
#client.loop_start()
client.loop_forever()



