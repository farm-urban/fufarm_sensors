#!/usr/bin/env python3
"""


"""
import datetime
import logging
import json
import serial
import time
import yaml
import paho.mqtt.client as mqtt


# Local imports
from bluelab_logs import bluelab_logs
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
    if config.BLUELAB:
        config.BLUELAB.tag_to_stationid = { x[0] : x[1] for x in config.BLUELAB.tag_to_stationid }
    return config

def setup_mqtt():
    client = mqtt.Client()
    client.username_pw_set(CONFIG.MQTT.username, CONFIG.MQTT.password)
    client.connect("localhost", port=1883)
    return client


CONFIG = process_config('config.yml')
logging.basicConfig(level=CONFIG.APP.log_level, format=f"%(asctime)s {CONFIG.APP.station_id}: %(message)s")
logger = logging.getLogger()

if CONFIG.APP.gpio_sensors:
    gpio_sensors.setup_devices()

mqtt_client = setup_mqtt()
mqtt_client.loop_start()

last_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=CONFIG.APP.poll_interval)
logger.info(
    f"\n\n### Sensor service starting loop at: {datetime.datetime.strftime(datetime.datetime.now(),'%d-%m-%Y %H:%M:%S')} ###\n\n"
)
firstloop = True
while True:
    # Below seems to raise an exception - not sure why
    if not mqtt_client.is_connected():
       logger.error("mqtt_client not connected")
    #    mqtt_client.reconnect()

    if not firstloop:
        # Send first readings immediately - for debugging.
        if CONFIG.APP.gpio_sensors:
            gpio_sensors.reset_flow_counter()
        # Need to pause so paddle can count rotations
        time.sleep(CONFIG.APP.poll_interval)

    data = dfrobot_sensors.sensor_readings()
    if data is None: # No data from dfrobot Arduino sensors
        data = {}
    if CONFIG.APP.gpio_sensors:
        data["flow"] = gpio_sensors.flow_rate(CONFIG.APP.poll_interval)
        data["distance"] = gpio_sensors.distance_sensor.distance
    if data:
        # Send sensor data from dfrobot Arduino and direct sensors
        logger.debug(f"Publishing to {CONFIG.MQTT.sensor_topic}: {data}")
        mqtt_client.publish(CONFIG.MQTT.sensor_topic, data)

    if CONFIG.BLUELAB.available:
        bluelab_data = bluelab_logs.sample_bluelab_data(last_timestamp,
                                                        CONFIG.APP.poll_interval,
                                                        log_dir=CONFIG.BLUELAB.log_dir)
        if bluelab_data is not None and len(bluelab_data) > 0:
            for d in bluelab_data:
                #  ['tag', 'timestamp', 'ec', 'ph', 'temp']
                station_id = CONFIG.BLUELAB.tag_to_stationid[d.tag]
                data = {"ec": d.ec, "ph": d.ph, "temp": d.temp}
                topic = f"{CONFIG.MQTT.bluelab_topic}/{station_id}"
                # timestamp?
                logger.debug(f"Publishing to {topic}: {data}")
                mqtt_client.publish(topic, data)

    last_timestamp = datetime.datetime.now()
    firstloop = False
