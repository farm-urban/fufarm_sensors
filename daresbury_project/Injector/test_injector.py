#!/usr/bin/env python3
import logging
import struct
import threading
import time

# local imports
import fu_database
import fu_connector
import injector

logging.basicConfig(level=logging.CRITICAL)

def test_injector():
    NREADINGS = 10
    # Set up the connector and database and clear old test data
    usb_config = fu_connector.USB_CONFIG
    usb_config['port'] = 'loop://'
    connector = fu_connector.connectorFactory(serial_config=usb_config)
    database = fu_database.Database(db_config=fu_database.db_config())
    database.ignore_close = True
    database.reset_mock_table()

    def send_test_data():
        time.sleep(1)
        sensor_id = fu_database.Database.sensor_id_map[fu_database.MOCK_TABLE]
        for i in range(NREADINGS):
            packet = struct.pack("@12sHf", "###########0".encode('ascii'), sensor_id, float(i))
            # REFACTOR TO USE A WRITE METHOD - AND CHECK WITH CODE ON WIPY
            connector.send(packet)
            time.sleep(2)

    sensor_thread = threading.Thread(target=send_test_data)
    kwargs = {'max_readings' : NREADINGS * 2,
              'connector' : connector,
              'database' : database}
    injector_thread = threading.Thread(target=injector.main, kwargs=kwargs)

    sensor_thread.start()
    injector_thread.start()
    injector_thread.join() # wait for test to complete

    # Check results
    # Database connection will have been closed
    database.init_database(db_config=fu_database.db_config())
    results = database.get_mock_data()
    assert len(results) == 10
    last = results[9]
    assert len(last) == 3
    assert last[2] == 9.0

if __name__ == '__main__':
    import pytest
    pytest.main()
