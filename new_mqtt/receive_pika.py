#!/usr/bin/env python
from influxdb import InfluxDBClient
import json
import pika
import time


def data_to_idb(data):
    return [
        {
            "measurement": "fu_sensor",
            "tags": {"sensor": data["sensor"], "stationid": data["stationid"]},
            "time": data["timestamp"],
            "fields": {"value": data["value"]},
        }
    ]


# queue_name = "jens_queue"
# connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
# channel = connection.channel()
# # ADD CODE TO SET UP QUEUE AND RETENTION POLICY ETC
# # channel.queue_declare(queue=queue_name)

idb_host = "localhost"
idb_port = 8086
idb_dbname = "fudata"
idb_client = InfluxDBClient(host=idb_host, port=idb_port, database=idb_dbname)

temp = 30.0
sensor_data = {
    "timestamp": int(time.time()),
    "stationid": "12345678",
    "sensor": "temperature",
    "value": temp,
}


data = data_to_idb(sensor_data)
# payload = json.reads(msg)
idb_client.write_points(data)


# def callback(ch, method, properties, body):
#     print(" [x] Received %r" % body)
#
#
# channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
#
# print(" [*] Waiting for messages. To exit press CTRL+C")
# channel.start_consuming()
