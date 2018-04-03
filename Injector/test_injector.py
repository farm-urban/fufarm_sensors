#!/usr/bin/env python3
import logging
#import sqlite3
import struct
import threading
import time

# local imports
import injector

logging.basicConfig(level=logging.DEBUG)
#con = sqlite3.connect(":memory:")
injector.SERIAL_PORT = 'loop://'

def send_data():
    time.sleep(1)
    sensor_id = injector.Database.sensor_id_map['mock']
    for i in range(10):
        packet = struct.pack("@12sHf", "###########0".encode('ascii'), sensor_id, float(i))
        injector.SERIAL.write(packet)
        time.sleep(2)

# Set up the data pipe
#injector.setup_database()
injector.setup_data_transfer()

sensor_thread = threading.Thread(target=send_data)
injector_thread = threading.Thread(target=injector.main)

sensor_thread.start()
injector_thread.start()
