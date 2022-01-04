#!/usr/bin/env python
from influxdb import InfluxDBClient
import json
import pika
import time

queue_name = "jens_queue"
idb_host = "localhost"
idb_port = 8086
idb_dbname = "fudata"


def data_to_idb(data):
    return [
        {
            "measurement": "fu_sensor",
            "tags": {"sensor": data["sensor"], "stationid": data["stationid"]},
            "time": int(data["timestamp"]),
            "fields": {"value": data["value"]},
        }
    ]


def message_callback(ch, method, properties, body):
    print("Received %r" % body)
    payload = json.loads(body)
    data = data_to_idb(payload)
    idb_client.write_points(data)


idb_client = InfluxDBClient(host=idb_host, port=idb_port, database=idb_dbname)

connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()
# # ADD CODE TO SET UP QUEUE AND RETENTION POLICY ETC
# # channel.queue_declare(queue=queue_name)


# temp = 30.0
# sensor_data = {
#     "timestamp": int(time.time()),
#     "stationid": "12345678",
#     "sensor": "temperature",
#     "value": temp,
# }


channel.basic_consume(
    queue=queue_name, on_message_callback=message_callback, auto_ack=True
)

print(" [*] Waiting for messages. To exit press CTRL+C")
channel.start_consuming()
