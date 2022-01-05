#!/usr/bin/env python3
"""
sudo apt-get install python3-serial

Can also use:
screen -S arduino  /dev/ttyACM0 9600

Kill session: ctrl-A K 

"""
import datetime
import logging
import json
import requests
import serial
import time
import paho.mqtt.client as mqtt

# For Local Pins
from gpiozero import DigitalInputDevice
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory

# Local imports
import bluelab_logs
import influxdb


def parse_serial_json(myserial):
    buffer = ""
    MAXLOOP = 20
    loop_count = 0
    data = None
    while True:
        if loop_count >= MAXLOOP:
            warnings.warn("parse_serial_json exceeded MAXLOOP")
            return None
        buffer += ser.read().decode("utf-8")
        try:
            data = json.loads(buffer)
            buffer = ""
        except json.JSONDecodeError:
            time.sleep(1)
        loop_count += 1
    return data


def setup_mqtt(influx_schema, measurement, on_mqtt_message):
    ## Setup MQTT
    client = mqtt.Client()
    # client.username_pw_set(username, password=None)
    userdata = {"influx_schema": influx_schema, "measurement": measurement}
    client.user_data_set(userdata)
    # client.connect("192.168.4.1", port=1883)
    client.connect("localhost", port=1883)

    # Add different plugs
    for topic in MQTT_SUBSCRIBE_TOPICS:
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
    if station_id in MQTT_TO_STATIONID.keys():
        station_id = MQTT_TO_STATIONID[station_id]
    tags = {"station_id": station_id}

    fields = data["ENERGY"]
    fields["TotalStartTime"] = datetime.datetime.strptime(
        fields["TotalStartTime"], "%Y-%m-%dT%H:%M:%S"
    ).timestamp()
    send_data_to_influx(
        influx_schema, measurement, tags, fields, local_timestamp=LOCAL_TIMESTAMP
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


def count_paddle():
    global pulse_count
    pulse_count += 1
    # print("button was pressed")


def flow_rate(sample_window):
    """From YF-S201 manual:
    Pluse Characteristic:F=7Q(L/MIN).
    2L/MIN=16HZ 4L/MIN=32.5HZ 6L/MIN=49.3HZ 8L/MIN=65.5HZ 10L/MIN=82HZ

    sample_window is in seconds, so hz is pulse_count / sample_window
    """
    hertz = pulse_count / sample_window
    return hertz / 7.0


MOCK = False
POLL_INTERVAL = 60 * 5
HAVE_BLUELAB = False
HAVE_MQTT = False
LOCAL_SENSORS = True
DIRECT_SENSORS = True
CONTROL_LIGHTS = False
LOCAL_TIMESTAMP = True
ARDUINO_TERMINAL = "/dev/ttyACM0"
LOG_LEVEL = logging.DEBUG


# Influxdb Configuration
SENSOR_STATION_ID = "rpi"
MEASUREMENT_SENSOR = "sensors"
BUCKET = "cryptfarm"
# TOKEN = pGHNPOqH8TmwJpU6vko7us8fmTAXltGP_X4yKONTI6l9N-c2tWsscFtCab43qUJo5EcQE3696U9de5gn9NN4Bw==
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

if DIRECT_SENSORS:
    pulse_count = 0
    # Local non-DFROBOT sensors
    btn = DigitalInputDevice(22)
    btn.when_activated = count_paddle

    factory = None
    USE_PIGPIOD = False
    if USE_PIGPIOD:
        factory = PiGPIOFactory()
    sensor = DistanceSensor(
        trigger=17, echo=27, pin_factory=factory, queue_len=20, partial=True
    )


# MQTT Data
MEASUREMENT_MQTT = "energy"
MEASUREMENT_BLUELAB = "bluelab"
# MQTT_TO_STATIONID = { 'FU_System_2': 'Propagation'}
MQTT_TO_STATIONID = {}
MQTT_SUBSCRIBE_TOPICS = [
    "tele/FU_Fans/SENSOR",
    "tele/FU_System_1/SENSOR",
    "tele/FU_System_2/SENSOR",
    "h2Pwr/STATUS",
]
BLUELAB_TAG_TO_STATIONID = {"52rf": "sys1", "4q3f": "sys2"}
LIGHT_SCHEDULE = ("06:00", 16)


# Logging
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [rpi2]: %(message)s")
logger = logging.getLogger()
if HAVE_MQTT:
    mqtt_client = setup_mqtt(influx_schema, MEASUREMENT_MQTT, on_mqtt_message)
if LOCAL_SENSORS:
    ser = serial.Serial(ARDUINO_TERMINAL, 9600, timeout=1)
    ser.flush()

h2_data = []
if CONTROL_LIGHTS:
    on_time, off_time = create_schedule_times(LIGHT_SCHEDULE)
if HAVE_MQTT:
    mqtt_client.loop_start()
last_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=POLL_INTERVAL)
logger.info(
    f"\n\n### Sensor service starting loop at: {datetime.datetime.strftime(datetime.datetime.now(),'%d-%m-%Y %H:%M:%S')} ###\n\n"
)
while True:
    # Below seems to raise an exception - not sure why
    # if not mqtt_client.is_connected():
    #    logger.info("mqtt_client reconnecting")
    #    mqtt_client.reconnect()

    if DIRECT_SENSORS:
        #  Need to loop so paddle can count rotations
        sample_start = time.time()
        sample_end = sample_start + POLL_INTERVAL
        pulse_count = 0
        while time.time() < sample_end:
            pass
        _flow_rate = flow_rate(POLL_INTERVAL)
        time.sleep(
            2
        )  # Need to add in pause or the distance sensor or else it measures 0.0
        _distance = sensor.distance

    if CONTROL_LIGHTS:
        on_time, off_time = manage_lights(on_time, off_time, mqtt_client)
    send = True
    if LOCAL_SENSORS and ser.in_waiting > 0:
        line = ser.readline().decode("utf-8").rstrip()
        send = True
        data = {}
        try:
            data = json.loads(line)
            # logger.info("Got data:%s",data)
        except json.decoder.JSONDecodeError as e:
            logger.warning("Error reading Arduino data: %s\nDoc was: %s", e.msg, e.doc)
            send = False
        #        data = parse_serial_json(ser)
        #        if data is None:
        #             warnings.warn("No data from parse_serial_json")
        #             data = {}
        #             send = False
        if DIRECT_SENSORS:
            data["flow"] = _flow_rate
            data["distance"] = _distance

        if send:
            influxdb.send_data_to_influx(
                influx_schema,
                MEASUREMENT_SENSOR,
                sensor_influx_tags,
                data,
                local_timestamp=LOCAL_TIMESTAMP,
            )

        # Clear anything remaining
        while ser.in_waiting > 0:
            c = ser.read()
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    send = True

    if HAVE_BLUELAB:
        bluelab_data = bluelab_logs.sample_bluelab_data(last_timestamp, POLL_INTERVAL)
        if bluelab_data is not None and len(bluelab_data) > 0:
            for d in bluelab_data:
                #  ['tag', 'timestamp', 'ec', 'ph', 'temp']
                tags = {"station_id": BLUELAB_TAG_TO_STATIONID[d.tag]}
                fields = {"cond": d.ec, "ph": d.ph, "temp": d.temp}
                influxdb.send_data_to_influx(
                    influx_schema,
                    MEASUREMENT_BLUELAB,
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
    if not DIRECT_SENSORS:
        time.sleep(POLL_INTERVAL)
