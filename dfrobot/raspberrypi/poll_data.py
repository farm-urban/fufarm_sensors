#!/usr/bin/env python3
"""
sudo apt-get install python3-serial

Can also use:
screen -S arduino  /dev/ttyACM0 9600

Kill session: ctrl-A K 

"""
from datetime import datetime, timedelta
import logging
import json
import requests
import serial
import time
import paho.mqtt.client as mqtt

# Local imports
import bluelab_logs


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


def on_mqtt_message(client, userdata, message):
    """
    Process message of format:

    Received message on topic [tele/tasmota_5014E2/SENSOR]: {"Time":"1970-01-01T00:33:28","ENERGY":{"TotalStartTime":"2021-07-10T11:54:41","Total":0.003,"Yesterday":0.000,"Today":0.003,"Period":0,"Power":22,"ApparentPower":24,"ReactivePower":11,"Factor":0.90,"Voltage":246,"Current":0.098}}

    """
    decoded_message = str(message.payload.decode("utf-8"))
    logger.debug(f"Received message on topic [{message.topic}]: {decoded_message}")
    try:
        data = json.loads(decoded_message)
    except json.decoder.JSONDecodeError as e:
        logger.warning(f"Error decoding MQTT data to JSON: {e.msg}\nMessage was: {e.doc}")

    # Process individual message
    influx_schema = userdata["influx_schema"]
    measurement = userdata["measurement"]

    station_id = message.topic.split("/")[1]
    if station_id in MQTT_TO_STATIONID.keys():
        station_id = MQTT_TO_STATIONID[station_id]
    tags = {'station_id' : station_id}

    fields = data['ENERGY']
    fields['TotalStartTime'] = datetime.strptime(fields['TotalStartTime'],"%Y-%m-%dT%H:%M:%S").timestamp() 
    send_data_to_influx(influx_schema, measurement, tags, fields, include_timestamp=INCLUDE_TIMESTAMP)


MOCK = True
POLL_INTERVAL =  60 * 2
LOG_LEVEL = logging.DEBUG

MEASUREMENT_SENSOR = "sensors"
MEASUREMENT_MQTT = "energy"
MEASUREMENT_BLUELAB = "bluelab"
SENSOR_STATION_ID = "rpi"
MQTT_TO_STATIONID = { 'FU_Fans': 'Propagation'}
BLUELAB_TAG_TO_STATIONID = { '52rf': 'sys1',
                             '4q3f': 'sys2'}
INCLUDE_TIMESTAMP = True
ARDUINO_TERMINAL = "/dev/ttyACM0"

BUCKET = "Heath"
TOKEN = "BvQj3U3Ldwvz5bP6FPa58Rv9tzIDxVC4eY5C8UVlKfyZxKGWh8vjuxe7sMFvTjSLHmKfkh3nXQooGXBbJWjgow=="
ORG = "accounts@farmurban.co.uk"
INFLUX_URL = "https://westeurope-1.azure.cloud2.influxdata.com"
influx_schema = {
    "endpoint": INFLUX_URL,
    "org": ORG, "token": TOKEN,
    "bucket": BUCKET,
}
sensor_influx_tags = {'station_id': SENSOR_STATION_ID}

# Logging
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s [loz_experiment]: %(message)s"
)
logger = logging.getLogger()

## Setup MQTT
client = mqtt.Client()
#client.username_pw_set(username, password=None)
userdata = { 'influx_schema': influx_schema,
             'measurement': MEASUREMENT_MQTT}
client.user_data_set(userdata)
#client.connect("192.168.4.1", port=1883)
client.connect("localhost", port=1883)

# Add different plugs
client.subscribe("tele/FU_Fans/SENSOR")
#client.subscribe("tele/FU_System_1/SENSOR")
#client.subscribe("tele/FU_System_2/SENSOR")
#client.subscribe("tele/tasmota_5014E2/SENSOR")
client.on_message = on_mqtt_message

ser = serial.Serial(ARDUINO_TERMINAL, 9600, timeout=1)
ser.flush()
client.loop_start()
last_timestamp = datetime.now() - timedelta(seconds=POLL_INTERVAL)
while True:
    send = True
    if ser.in_waiting > 0:
        line = ser.readline().decode("utf-8").rstrip()
        send = True
        try:
            data = json.loads(line)
            # logger.info("Got data:%s",data)
        except json.decoder.JSONDecodeError as e:
            logger.warning("Error reading Arduino data: %s\nDoc was: %s", e.msg, e.doc)
            send = False
        if send: 
            send_data_to_influx(influx_schema, MEASUREMENT_SENSOR, sensor_influx_tags, data, include_timestamp=INCLUDE_TIMESTAMP)
    send = True
    
    bluelab_data = bluelab_logs.sample_bluelab_data(last_timestamp, POLL_INTERVAL)
    if bluelab_data is not None and len(bluelab_data) > 0:
        for d in bluelab_data:
            #  ['tag', 'timestamp', 'ec', 'ph', 'temp']
            tags = {'station_id': BLUELAB_TAG_TO_STATIONID[d.tag]}
            fields = {'cond': d.ec,
                      'ph': d.ph,
                      'temp': d.temp}
            send_data_to_influx(influx_schema, MEASUREMENT_BLUELAB, tags, fields, include_timestamp=INCLUDE_TIMESTAMP)

    last_timestamp = datetime.now()
    time.sleep(POLL_INTERVAL)

