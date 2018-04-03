#!/usr/bin/env python3
"""
    This program tests connecting to a MySQL database from Python.

    Copyright (C) 2018  Darren Faulke (VEC), Jens Thomas (Farm Urban)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import datetime
from datetime import datetime
import logging
import socket
import struct
import sys
import time
# 3rd-party imports
import serial
import mysql.connector
from mysql.connector import errorcode

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Networking.
# -----------------------------------------------------------------------------
#UDP_IP = "127.0.0.1"
UDP_IP = "192.168.0.101"
UDP_PORT = 9000

# jmht - send data over the USB cable rather then wifi
DATA_OVER_USB = True
SERIAL_PORT = '/dev/cu.usbmodemPy5a3af1'
SERIAL = None
SOCKET = None
PACKET_SIZE = 20
BAUDRATE = 9600
IN_WAITING = None

MOCK_SENSOR_ID = 9999

# -----------------------------------------------------------------------------
# Database access.
# -----------------------------------------------------------------------------
DB_CONFIG = {
    'user': 'foo',
    'password': 'password',
    'host': 'localhost'
    }

DB_NAME = 'farmurban'
DB = None
CURSOR = None

"""
# -----------------------------------------------------------------------------
# Database table structures.
# -----------------------------------------------------------------------------

    ,-------------------------------------------------------------------------,
    | Each of these tables will be created if they don't exist. The contents  |
    | will need to be adapted for specific use.                               |
    | The following are the SQL commands to create the different tables.      |
    '-------------------------------------------------------------------------'

 The station ID is determined from a database of MAC addresses:

        ,------------------,
        | ID | MAC address |
        |----+-------------|
        | 01 | Station 01  |
        | 02 | Station 02  |
        | .. | ..          |
        | nn | Station nn  |
        '------------------'

 The ID can be returned using an SQL query.

The sensor ID is determined from a database of sensor IDs:
        ,----------------------------,
        | ID | Sensor                |
        |----+-----------------------|
        | 00 | water_temperature     |
        | 05 | barometer_pressure    |
        | 06 | barometer_temperature |
        | 10 | humidity_humidity     |
        | 11 | humidity_temperature  |
        | 15 | ambient_light_0       |
        | 16 | ambient_light_1       |
        | 20 | ph_level              |
        '----------------------------'

    Sensor data:

        ,--------------------------------------,
        | Variable | DB format     | Type      |
        |----------+---------------+-----------|
        | time     | datetime      | datetime  |
        | station  | char(12)      | bytes     |
        | reading  | decimal(3,1)  | real      |
        '--------------------------------------'

"""

CREATE_TABLE_STATIONS = ('CREATE TABLE ''stations''('
                         'mac CHAR(12) UNIQUE NOT NULL,'
                         'id INT NOT NULL PRIMARY KEY AUTO_INCREMENT)')

CREATE_TABLE_SENSORS = ('CREATE TABLE ''sensors''('
                        'sensor CHAR(32) UNIQUE NOT NULL,'
                        'id SMALLINT NOT NULL)')

CREATE_TABLE_WATER_TEMPERATURE = ('CREATE TABLE ''water_temperature''('
                                  'time DATETIME NOT NULL PRIMARY KEY,'
                                  'station SMALLINT,'
                                  'reading DECIMAL(3,1))')

CREATE_TABLE_BAROMETER_TEMPERATURE = ('CREATE TABLE ''barometer_temperature''('
                                      'time DATETIME NOT NULL PRIMARY KEY,'
                                      'station SMALLINT,'
                                      'reading DECIMAL(3,1))')

CREATE_TABLE_HUMIDITY_HUMIDITY = ('CREATE TABLE ''humidity_humidity''('
                                  'time DATETIME NOT NULL PRIMARY KEY,'
                                  'station SMALLINT,'
                                  'reading DECIMAL(3,1))')

CREATE_TABLE_HUMIDITY_TEMPERATURE = ('CREATE TABLE ''humidity_temperature''('
                                     'time DATETIME NOT NULL PRIMARY KEY,'
                                     'station SMALLINT,'
                                     'reading DECIMAL(3,1))')

CREATE_TABLE_AMBIENT_LIGHT_0 = ('CREATE TABLE ''ambient_light_0''('
                                'time DATETIME NOT NULL PRIMARY KEY,'
                                'station SMALLINT,'
                                'reading SMALLINT)')

CREATE_TABLE_AMBIENT_LIGHT_1 = ('CREATE TABLE ''ambient_light_1''('
                                'time DATETIME NOT NULL PRIMARY KEY,'
                                'station SMALLINT,'
                                'reading SMALLINT)')

CREATE_TABLE_PH_LEVEL = ('CREATE TABLE ''ph_level''('
                         'time DATETIME NOT NULL PRIMARY KEY,'
                         'station SMALLINT,'
                         'reading DECIMAL(2,1))')

CREATE_TABLE_MOCK = ('CREATE TABLE ''mock''('
                     'time DATETIME NOT NULL PRIMARY KEY,'
                     'station SMALLINT,'
                     'reading DECIMAL(2,1))')

TABLES = {}
TABLES['stations']              = (CREATE_TABLE_STATIONS)
TABLES['sensors']               = (CREATE_TABLE_SENSORS)
TABLES['water_temperature']     = (CREATE_TABLE_WATER_TEMPERATURE)
TABLES['barometer_temperature'] = (CREATE_TABLE_BAROMETER_TEMPERATURE)
TABLES['humidity_humidity']     = (CREATE_TABLE_HUMIDITY_HUMIDITY)
TABLES['humidity_temperature']  = (CREATE_TABLE_HUMIDITY_TEMPERATURE)
TABLES['ambient_light_0']       = (CREATE_TABLE_AMBIENT_LIGHT_0)
TABLES['ambient_light_1']       = (CREATE_TABLE_AMBIENT_LIGHT_1)
TABLES['ph_level']              = (CREATE_TABLE_PH_LEVEL)
TABLES['mock']                  = (CREATE_TABLE_MOCK)


# Functions for inserting data into tables.         |
INSERT_STATION = ("INSERT IGNORE INTO stations (mac, id) VALUES (%s, %s)")
INSERT_SENSOR = ("INSERT IGNORE INTO sensors (sensor, id) VALUES (%s, %s)")
QUERY_STATION = ("SELECT id FROM stations WHERE mac = %s")
QUERY_SENSOR = ("SELECT sensor FROM sensors WHERE id = %s")

# ,-------------------------,
# | Sensor ID definitions.  |
# '-------------------------'
SENSOR_ID_MAP = {'water_temperature'     :  0,
                 'barometer_pressure'    :  5,
                 'barometer_temperature' :  6,
                 'humidity_humidity'     : 10,
                 'humidity_temperature'  : 11,
                 'ambient_light_0'       : 15,
                 'ambient_light_1'       : 16,
                 'ph_level'              : 20,
                 'mock'                  : MOCK_SENSOR_ID}

def insert_value_station(cursor, mac):
    global CURSOR
    logger.info("Storing station ID for {}.".format(mac.decode()))
    station_data = (mac, "NULL")
    CURSOR.execute(INSERT_STATION, station_data)
    DB.commit()

def insert_value_sensor(cursor, name, id):
    global CURSOR
    logger.info("ID {:2} = {}.".format(id, name))
    CURSOR.execute(INSERT_SENSOR, (name, id))
    DB.commit()

def insert_value_data(cursor, data):
    global CURSOR
    time = data[0]
    station = data[1]
    sensor = data[2].decode()
    value = data[3]
    logger.info("Inserting data into table.")
    logger.info("\tTime = {}.".format(time))
    logger.info("\tStation = {}.".format(station))
    logger.info("\tSensor = {}.".format(sensor))
    logger.info("\tValue = {}.".format(value))
    INSERT_DATA = ("INSERT IGNORE INTO {} (time, station, reading) "
                   "VALUES (%s, %s, %s)".format(sensor))
    CURSOR.execute(INSERT_DATA, (time, station, value))
    res = DB.commit()
    logger.info("Got result: %s" % res)

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} CHARACTER SET utf8 COLLATE utf8_bin".format(DB_NAME))
    except mysql.connector.Error as err:
        logger.citical("\tFailed to create database: {}".format(err))
        exit(1)

def get_station_id(mac):
    global CURSOR
    logger.info("Station {} is ".format(mac.decode()))
    CURSOR.execute(QUERY_STATION, (mac,))
    id = CURSOR.fetchone()
    if id:
        logger.info("{}.".format(id[0]))
        return id[0]
    else:
        logger.info("unknown.")
        return None

def get_sensor_name(id):
    global CURSOR
    name_str = "unknown"
    CURSOR.execute(QUERY_SENSOR, (id,))
    name = CURSOR.fetchone()
    if name:
        name = name[0]
        name_str = name.decode()
    else:
        name = None
    logger.info("Sensor %s is %s", id, name_str)
    return name

def set_time():
    """
    Waits for initial connection and sends current date and time.

    The intent for this function is to provide a fallback
    method for the station sensor board to set it's clock
    after being off without a battery back up.
    It needs to be triggered by a request, which is
    difficult because the data packet structure is fixed.
    At the moment this function is not called as the time
    is created by this program rather than the station
    sensor board.
    """
    logger.info("Waiting for NTP request.\n")
    waiting_ntp = True
    while waiting_ntp:
        data, addr = SOCKET.recvfrom(512)
        stringdata = data.decode('utf-8')
        if stringdata == "ntp":
            logger.info("Received request for NTP.")
            ntp_string = "{}".format(datetime.now())
            ntp_bytes = ntp_string.encode('utf-8')
            ntp_tuple = time.strptime(ntp_string, "%Y-%m-%d %H:%M:%S.%f")
            packet = "{},{},{},{},{},{},{},{}".format(ntp_tuple.tm_year,\
                                                    ntp_tuple.tm_mon,\
                                                    ntp_tuple.tm_mday,\
                                                    ntp_tuple.tm_hour,\
                                                    ntp_tuple.tm_min,\
                                                    ntp_tuple.tm_sec,\
                                                    ntp_tuple.tm_wday,\
                                                    ntp_tuple.tm_yday)
            logger.info("Packet = {}.".format(packet))
            SOCKET.sendto(packet.encode('utf-8'), addr)
            waiting_ntp = False

def setup_data_transfer():
    global PACKET_SIZE, BAUDRATE, IN_WAITING, SERIAL, SOCKET, DATA_OVER_USB
    if DATA_OVER_USB:
        if SERIAL_PORT.startswith('loop://'):
            SERIAL = serial.serial_for_url(SERIAL_PORT, baudrate=BAUDRATE,
                                           bytesize=serial.EIGHTBITS, timeout=2)
        else:
            SERIAL = serial.Serial(port=SERIAL_PORT, baudrate=BAUDRATE,
                                   bytesize=serial.EIGHTBITS, timeout=2)
        logger.debug("SETUP SERIAL %s", SERIAL)
        IN_WAITING = 'in_waiting'
        if not hasattr(SERIAL, IN_WAITING):
            IN_WAITING = 'inWaiting'
            if not hasattr(SERIAL, IN_WAITING):
                raise AttributeError("Ser object doesn't have in_waiting or inWaiting atrributes!")
        IN_WAITING = getattr(SERIAL, IN_WAITING)
        # poller.register(ser)
    else:
        logger.info("Networking:")
        SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # poller.register(socket)
        logger.info("\tBinding socket to {}, port {}".format(UDP_IP, UDP_PORT))
        SOCKET.bind((UDP_IP, UDP_PORT))

def setup_database():
    global CURSOR, DB, SERIAL, DB_CONFIG
    logger.info("Initialising...\n")
    logger.info("Database:")
    try:
        DB = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.info("Something is wrong with your user name or password")
            sys.exit(1)
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.info("Database does not exist")
            sys.exit(1)
        else:
            logger.info(err)
            sys.exit(1)
    CURSOR = DB.cursor()

    # ,---------------------------------------------,
    # | Create the database if it doesn't exist.    |
    # '---------------------------------------------'
    try:
        DB.database = DB_NAME
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.info("\tCreating new database \"{}\": ".format(DB_NAME))
            create_database(CURSOR)
            DB.database = DB_NAME
        else:
            logger.info(err)
            exit(1)
    else:
        logger.info("\tDatabase \"{}\" already exists.".format(DB.database))

    # ,-----------------------------------------,
    # | Create the tables if they don't exist.  |
    # '-----------------------------------------'
    for name, ddl in TABLES.items():
        try:
            CURSOR.execute(ddl)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                logger.info("\tTable \"{}\" already exists.".format(name))
            else:
                logger.info(err.msg)
        else:
            logger.info("\tCreated new table \"{}\"".format(name))

    # ,-----------------------------,
    # | Populate the sensors table. |
    # '-----------------------------'
    logger.info("Entering sensor ID.")
    for sensor, id in SENSOR_ID_MAP.items():
        insert_value_sensor(CURSOR, sensor, id)
    print("GOT DB ",DB)
    print("GOT CURSOR ",CURSOR)

def main():
    global DB, CURSOR, SOCKET, SERIAL, IN_WAITING, PACKET_SIZE
    if not DB:
        setup_database()
    if not (SOCKET or SERIAL):
        setup_data_transfer()

    error = False # Error trapping variable.
    #set_time()
    logger.info("Waiting for sensor data.\n")
    while not error:
        time.sleep(1)
        if DATA_OVER_USB:
            global PACKET_SIZE
            to_read = IN_WAITING() # call the relevant function
            logger.info("GOT to_read %s ", to_read)
            if to_read == PACKET_SIZE:
                data = SERIAL.read(PACKET_SIZE)
                station_mac,\
                sensor_id,\
                sensor_data = struct.unpack("@12sHf", data)
                logger.info("GOT DATA: %s %s %s" % (station_mac, sensor_id, sensor_data))
            else:
                # Just clear the output buffer
                data = SERIAL.read(to_read)
        else:
            data, addr = SOCKET.recvfrom(512)

        if not data:
            continue
        logger.info("Received %s bytes of sensor data.", len(data))

        # Unpack the UDP data into it's components.
        station_mac,\
        sensor_id,\
        sensor_data = struct.unpack("@12sHf", data)

        # Store station MAC address and get ID.
        station = get_station_id(station_mac)
        if not station:
            insert_value_station(CURSOR, station_mac)
            station = get_station_id(station_mac)

        sensor_name = get_sensor_name(sensor_id)
        if sensor_name:
            logger.info("Sensor {} reading = {}.".format(sensor_name.decode(), sensor_data))

        # ,-------------------------------------------------------,
        # | Currently the time stamp is made here for convenience |
        # | in case the station board cannot set it's clock.      |
        # '-------------------------------------------------------'
        read_time = datetime.now()

        logging.debug("SENSOR DATA: %s %s %s %s", read_time, station, sensor_name, sensor_data)
        sensor_data = (read_time, station, sensor_name, sensor_data)
        insert_value_data(CURSOR, sensor_data)

    # -----------------------------------------------------------------------------
    # Tidy up.
    # -----------------------------------------------------------------------------
    if DATA_OVER_USB:
        SERIAL.close()
    else:
        SOCKET.close()
    CURSOR.close()
    DB.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
