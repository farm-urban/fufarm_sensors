#!/usr/bin/env python3
"""
sudo apt-get install python3-serial

Can also use:
screen -S arduino  /dev/ttyACM0 9600

Kill session: ctrl-A K 

Example of config.yml:

```
APP:
  mock: False
  log_level: 'DEBUG'
  poll_interval: 60 * 5
  have_bluelab: False
  gpio_sensors: False
  local_timestamp: True
  control_lights: False
  light_schedule: ("06:00", 16)

INFLUX:
  station_id: "rpi"
  token: "PLACE TOKEN IN TOKEN FILE"
  measurement: "sensors"
  bucket: "cryptfarm"
  org: "Farm Urban"
  url: "https://influx.farmurban.co.uk"

MQTT:
  available: False
  measurement: "energy"
  tag_to_stationid: [
    ["FU_System_2", "Propagation"]
  ]
  subscribe_topics: [
      "tele/FU_Fans/SENSOR",
      "tele/FU_System_1/SENSOR",
      "tele/FU_System_2/SENSOR",
      "h2Pwr/STATUS",
  ]

BLUELAB:
  available: True
  measurement: "bluelab"
  tag_to_stationid: [
    ["52rf", "lgrow"],
    ["4q3f", "farm"]
  ]
  log_dir: "/home/pi/.local/share/Bluelab/Connect/logs"
```

"""
import datetime
import logging
import json
import requests
import serial
import time
import yaml
import paho.mqtt.client as mqtt


# Local imports
from bluelab_logs import bluelab_logs
from util import influxdb
from util import gpio_sensors
from util import dfrobot_sensors

class obj(object):
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [obj(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, obj(v) if isinstance(v, dict) else v)

    def __repr__(self):
        return '<%s>' % str('\n '.join('%s : %s' % (k, repr(v)) for (k, v) in self.__dict__.items())) 

def process_config(file_path):
    with open(file_path, "r") as f:
        yamls = yaml.safe_load(f)
    config = obj(yamls)

    # Handle individual configuration variables
    if not hasattr(logging, config.APP.log_level):
        raise AttributeError(f"Unknown log_level: {config.APP.log_level}")

    config.APP.poll_interval = eval(config.APP.poll_interval)
    config.INFLUX.token = open("TOKEN").readline().strip()
    config.BLUELAB.tag_to_stationid = { x[0] : x[1] for x in config.BLUELAB.tag_to_stationid }
    return config

def setup_mqtt(influx_schema, measurement, on_mqtt_message):
    ## Setup MQTT
    client = mqtt.Client()
    # client.username_pw_set(username, password=None)
    userdata = {"influx_schema": influx_schema, "measurement": measurement}
    client.user_data_set(userdata)
    # client.connect("192.168.4.1", port=1883)
    client.connect("localhost", port=1883)

    # Add different plugs
    for topic in CONFIG.MQTT.subscribe_topics:
        client.subscribe(topic)
    client.on_message = on_mqtt_message
    return client


def on_mqtt_message(client, userdata, message):
    """
    Process message of format:

    Received message on topic [tele/tasmota_5014E2/SENSOR]: {"Time":"1970-01-01T00:33:28","ENERGY":{"TotalStartTime":"2021-07-10T11:54:41","Total":0.003,"Yesterday":0.000,"Today":0.003,"Period":0,"Power":22,"ApparentPower":24,"ReactivePower":11,"Factor":0.90,"Voltage":246,"Current":0.098}}

    """
    global h2_data
    decoded_message = str(message.payload.decode("utf-8"))
    if True or message.topic != "h2Pwr/STATUS":
        logger.debug(f"Received message on topic [{message.topic}]: {decoded_message}")

    if message.topic == "h2Pwr/STATUS":
        try:
            data = json.loads(decoded_message)
        except json.decoder.JSONDecodeError as e:
            logger.warning(
                f"Error decoding MQTT data to JSON: {e.msg}\nMessage was: {e.doc}"
            )
            data = {"current": -1.0, "voltage": -1.0}
        h2_data.append(data)
        return

    try:
        data = json.loads(decoded_message)
    except json.decoder.JSONDecodeError as e:
        logger.warning(
            f"Error decoding MQTT data to JSON: {e.msg}\nMessage was: {e.doc}"
        )

    # Process individual message
    influx_schema = userdata["influx_schema"]
    measurement = userdata["measurement"]

    station_id = message.topic.split("/")[1]
    if station_id in CONFIG.MQTT.tag_to_stationid.keys():
        station_id = CONFIG.MQTT.tag_to_stationid[station_id]
    tags = {"station_id": station_id}

    fields = data["ENERGY"]
    fields["TotalStartTime"] = datetime.datetime.strptime(
        fields["TotalStartTime"], "%Y-%m-%dT%H:%M:%S"
    ).timestamp()
    influxdb.send_data_to_influx(
        influx_schema, measurement, tags, fields, local_timestamp=CONFIG.APP.local_timestamp
    )


def is_past(trigger):
    return bool((trigger - datetime.datetime.now()).days < 0)


def create_schedule_times(schedule):
    today = datetime.date.today()
    _on_time = datetime.time(
        hour=int(schedule[0].split(":")[0]), minute=int(schedule[0].split(":")[1])
    )
    on_time = datetime.datetime.combine(today, _on_time)
    _off_time = (on_time + datetime.timedelta(hours=schedule[1])).time()
    on_time = datetime.datetime.combine(today, _on_time)
    off_time = datetime.datetime.combine(today, _off_time)
    on_time, off_time = manage_lights(on_time, off_time)
    logger.info(
        f"create_schedule_time: lights next set to go on at {on_time} and off at {off_time}"
    )
    return on_time, off_time


def manage_lights(on_time, off_time, mqtt_client=None):
    if is_past(on_time) and is_past(off_time):
        # off_time always after on_time, so if both in past, lights should be off and on_time needs
        # to be pushed to tomorrow
        on_time = on_time + datetime.timedelta(hours=24)
        off_time = off_time + datetime.timedelta(hours=24)
        if mqtt_client:
            logger.info(
                f"Turning lights off at: {datetime.datetime.now()} - next on at: {on_time}"
            )
            mqtt_client.publish("cmnd/FU_System_2/Power", "0")
    elif is_past(on_time):
        # on_time past, off_time is in future - lights should be on and on_time pushed to tomorrow
        on_time = on_time + datetime.timedelta(hours=24)
        if mqtt_client:
            logger.info(
                f"Turning lights on at: {datetime.datetime.now()} - next off at: {off_time}"
            )
            mqtt_client.publish("cmnd/FU_System_2/Power", "1")
    elif is_past(off_time):
        # off_time past, on_time is in future - lights should be off and off_time pushed to tomorrow
        off_time = off_time + datetime.timedelta(hours=24)
        if mqtt_client:
            logger.info(
                f"Turning lights off at: {datetime.datetime.now()} - next on at: {on_time}"
            )
            mqtt_client.publish("cmnd/FU_System_2/Power", "0")
    else:
        # Both on_time and off_time in the future so nothing to do
        pass
    return on_time, off_time

CONFIG = process_config('config.yml')
influx_schema = {
    "endpoint": CONFIG.INFLUX.url,
    "org": CONFIG.INFLUX.org,
    "token": CONFIG.INFLUX.token,
    "bucket": CONFIG.INFLUX.bucket,
}
sensor_influx_tags = {"station_id": CONFIG.INFLUX.station_id}

# Logging
logging.basicConfig(level=CONFIG.APP.log_level, format="%(asctime)s [rpi2]: %(message)s")
logger = logging.getLogger()
if CONFIG.MQTT.available:
    mqtt_client = setup_mqtt(influx_schema, CONFIG.MQTT.measurement, on_mqtt_message)

h2_data = []
if CONFIG.APP.control_lights:
    on_time, off_time = create_schedule_times(CONFIG.APP.light_schedule)
if CONFIG.APP.gpio_sensors:
    gpio_sensors.setup_devices()
if CONFIG.MQTT.available:
    mqtt_client.loop_start()
last_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=CONFIG.APP.poll_interval)
logger.info(
    f"\n\n### Sensor service starting loop at: {datetime.datetime.strftime(datetime.datetime.now(),'%d-%m-%Y %H:%M:%S')} ###\n\n"
)
loopcount = 0
while True:
    # Below seems to raise an exception - not sure why
    # if not mqtt_client.is_connected():
    #    logger.info("mqtt_client reconnecting")
    #    mqtt_client.reconnect()
    if CONFIG.APP.control_lights:
        on_time, off_time = manage_lights(on_time, off_time, mqtt_client)

    if loopcount > 0:
        # We run the first set of readings immediately so we have data to send -
        # mainly for debugging and checking purposes.
        gpio_sensors.reset_flow_counter()
        # Need to pause so paddle can count rotations
        time.sleep(CONFIG.APP.poll_interval)

    data = dfrobot_sensors.sensor_readings()
    if data is None:
        # No data from dfrobot Arduino sensors
        data = {}
    if CONFIG.APP.gpio_sensors:
        data["flow"] = gpio_sensors.flow_rate(CONFIG.APP.poll_interval)
        data["distance"] = gpio_sensors.distance_sensor.distance
    if data:
        # Send sensor data from dfrobot Arduino and direct sensors
        influxdb.send_data_to_influx(
            influx_schema,
            CONFIG.INFLUX.measurement,
            sensor_influx_tags,
            data,
            local_timestamp=CONFIG.APP.local_timestamp,
        )

    if CONFIG.BLUELAB.available:
        bluelab_data = bluelab_logs.sample_bluelab_data(last_timestamp,
                                                        CONFIG.APP.poll_interval,
                                                        log_dir=CONFIG.BLUELAB.log_dir)
        if bluelab_data is not None and len(bluelab_data) > 0:
            for d in bluelab_data:
                #  ['tag', 'timestamp', 'ec', 'ph', 'temp']
                tags = {"station_id": CONFIG.BLUELAB.tag_to_stationid[d.tag]}
                fields = {"cond": d.ec, "ph": d.ph, "temp": d.temp}
                influxdb.send_data_to_influx(
                    influx_schema,
                    CONFIG.BLUELAB.measurement,
                    tags,
                    fields,
                    timestamp=d.timestamp,
                )

    if len(h2_data):
        current = sum([d["current"] for d in h2_data]) / len(h2_data)
        voltage = sum([d["voltage"] for d in h2_data]) / len(h2_data)
        h2_measurement = "h2pwr"
        h2_tags = {"station_id": "rpi"}
        h2_fields = {"current": current, "voltage": voltage}
        influxdb.send_data_to_influx(
            influx_schema, h2_measurement, h2_tags, h2_fields, local_timestamp=True
        )
        h2_data = []

    last_timestamp = datetime.datetime.now()
    loopcount += 1
