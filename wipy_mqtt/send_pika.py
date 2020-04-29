#!/usr/bin/env python
import json
import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()

queue_name = "fusensors"
channel.queue_declare(queue=queue_name)

i = 0
while True:
    i += 1
    if i % 5 == 0:
        i = 0
    msg = {
        "timestamp": time.time(),
        "stationid": "12345678",
        "sensor": "temperature",
        "value": 30.0 + i,
    }
    payload = json.dumps(msg)
    channel.basic_publish(exchange="", routing_key=queue_name, body=payload)
    print("Sent {}".format(msg))
    time.sleep(5)

connection.close()
