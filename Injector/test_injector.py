#!/usr/bin/env python3
import logging
import struct
import threading
import time

# local imports
import fu_database
import injector

logging.basicConfig(level=logging.DEBUG)
def send_data():
    time.sleep(1)
    sensor_id = fu_database.Database.sensor_id_map['mock']
    for i in range(10):
        packet = struct.pack("@12sHf", "###########0".encode('ascii'), sensor_id, float(i))
        injector.TEST_CONNECTOR.serial.write(packet)
        time.sleep(2)

# Set up the data pipe
usb_config = injector.USB_CONFIG
usb_config['port'] = 'loop://'
injector.TEST_CONNECTOR = injector.Connector(usb_config=usb_config)

sensor_thread = threading.Thread(target=send_data)
injector_thread = threading.Thread(target=injector.main)

sensor_thread.start()
injector_thread.start()
