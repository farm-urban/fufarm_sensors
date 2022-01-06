#!/usr/bin/env python3
import json
import time
import paho.mqtt.client as mqtt

err_dict = {v: k for k, v in mqtt.__dict__.items() if k.startswith("MQTT_ERR")}

queue_name = "jens_route"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    global queue_name
    print("Connected with result code " + err_dict[rc])
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(queue_name)
    print("END CONNECT")


def on_message(client, userdata, message):
    print(
        "Received message '"
        + str(message.payload)
        + "' on topic '"
        + message.topic
        + "' with QoS "
        + str(message.qos)
    )
    # dir of message: 'dup', 'info', 'mid', 'payload', 'qos', 'retain', 'state', 'timestamp', 'topic'


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", port=1883, keepalive=60)
client.loop_forever()
