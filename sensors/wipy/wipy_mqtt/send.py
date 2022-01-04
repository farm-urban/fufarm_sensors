#!/usr/bin/env python3
import json
import time
import paho.mqtt.client as mqtt

err_dict = {v: k for k, v in mqtt.__dict__.items() if k.startswith("MQTT_ERR")}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + err_dict[rc])


def on_message(client, userdata, msg):
    print("on_message ", msg.topic + " " + str(msg.payload))


queue_name = "jens_route"
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
# client.loop_forever()

client.loop_start()  # happens in separate thread so we get control back
i = 0
j = 0
while True:
    # temperature = sensor.blocking_read()
    i += 1
    j += 1
    if j % 5 == 0:
        j = 0
    temp = 30.0 + j
    temp = i

    msg = {
        "timestamp": time.time(),
        "stationid": "12345678",
        "sensor": "temperature",
        "value": temp,
    }
    payload = json.dumps(msg)
    # returns MQTTMessageInfo - on_publish callback is generated once message sent
    print("Sending {}".format(payload))
    result = client.publish(queue_name, payload=payload, qos=1, retain=True)
    # result.rc: MQTT_ERR_SUCCESS, MQTT_ERR_NO_CONN, MQTT_ERR_QUEUE_SIZE
    # result.mid
    result.wait_for_publish()
    if not result.is_published():
        print("Message not published: {}".format(err_dict[result.rc]))
    else:
        print(
            "Published message with mid {} and rc {}".format(
                result.mid, err_dict[result.rc]
            )
        )
    time.sleep(5)

loop_stop()
