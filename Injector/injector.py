#!/usr/bin/env ccp4-python
# =============================================================================
# This program tests connecting to a MySQL database from Python.
#
# Licensing ?
#
# Darren Faulke (VEC)
# =============================================================================

import mysql.connector
import socket
import time
import datetime
import struct
from datetime import datetime
from mysql.connector import errorcode
# jmht
import select
import serial

# -----------------------------------------------------------------------------
# Debugging and output.
# -----------------------------------------------------------------------------
PRINT_DEBUG = True  # Print debugging output.
PRINT_OUTPUT = True # Print informational output.

# -----------------------------------------------------------------------------
# Networking.
# -----------------------------------------------------------------------------
#UDP_IP = "127.0.0.1"
UDP_IP = "192.168.0.101"
UDP_PORT = 9000

# jmht - send data over the USB cable rather then wifi
DATA_OVER_USB = True

# -----------------------------------------------------------------------------
# Database access.
# -----------------------------------------------------------------------------
DB_CONFIG = {
    'user': 'foo',
    'password': 'password',
    'host': 'localhost'
    }

DB_NAME = 'farmurban'

# -----------------------------------------------------------------------------
# Database table structures.
# -----------------------------------------------------------------------------

#   ,-------------------------------------------------------------------------,
#   | Each of these tables will be created if they don't exist. The contents  |
#   | will need to be adapted for specific use.                               |
#   | The following are the SQL commands to create the different tables.      |
#   '-------------------------------------------------------------------------'

# The station ID is determined from a database of MAC addresses:
#
#       ,------------------,
#       | ID | MAC address |
#       |----+-------------|
#       | 01 | Station 01  |
#       | 02 | Station 02  |
#       | .. | ..          |
#       | nn | Station nn  |
#       '------------------'
#
# The ID can be returned using an SQL query.

CREATE_TABLE_STATIONS = ('CREATE TABLE ''stations''('
                         'mac CHAR(12) UNIQUE NOT NULL,'
                         'id INT NOT NULL PRIMARY KEY AUTO_INCREMENT)')

# The sensor ID is determined from a database of sensor IDs:
#
#       ,----------------------------,
#       | ID | Sensor                |
#       |----+-----------------------|
#       | 00 | water_temperature     |
#       | 05 | barometer_pressure    |
#       | 06 | barometer_temperature |
#       | 10 | humidity_humidity     |
#       | 11 | humidity_temperature  |
#       | 15 | ambient_light_0       |
#       | 16 | ambient_light_1       |
#       | 20 | ph_level              |
#       '----------------------------'

CREATE_TABLE_SENSORS = ('CREATE TABLE ''sensors''('
                        'sensor CHAR(32) UNIQUE NOT NULL,'
                        'id SMALLINT NOT NULL)')

#   Sensor data:
#
#       ,--------------------------------------,
#       | Variable | DB format     | Type      |
#       |----------+---------------+-----------|
#       | time     | datetime      | datetime  |
#       | station  | char(12)      | bytes     |
#       | reading  | decimal(3,1)  | real      |
#       '--------------------------------------'

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

#   ,---------------------------------------------------,
#   | Functions for inserting data into tables.         |
#   '---------------------------------------------------'

INSERT_STATION = ("INSERT IGNORE INTO stations (mac, id) VALUES (%s, %s)")

INSERT_SENSOR = ("INSERT IGNORE INTO sensors (sensor, id) VALUES (%s, %s)")

#INSERT_DATA = ("INSERT INTO data (time, station, %s) VALUES (%s, %s, %s)")

def insert_value_station(cursor, mac):

    if PRINT_OUTPUT:
        print("Storing station ID for {}.".format(mac.decode()))
    station_data = (mac, "NULL")
    cursor.execute(INSERT_STATION, station_data)
    db.commit()

def insert_value_sensor(cursor, name, id):

    if PRINT_OUTPUT:
        print("ID {:2} = {}.".format(id, name))
    cursor.execute(INSERT_SENSOR, (name, id))
    db.commit()

def insert_value_data(cursor, data):

    time = data[0]
    station = data[1]
    sensor = data[2].decode()
    value = data[3]
    if PRINT_OUTPUT:
        print("Inserting data into table.")
        print("\tTime = {}.".format(time))
        print("\tStation = {}.".format(station))
        print("\tSensor = {}.".format(sensor))
        print("\tValue = {}.".format(value))
        print("")

    INSERT_DATA = ("INSERT IGNORE INTO {} (time, station, reading) "
                   "VALUES (%s, %s, %s)".format(sensor))
    cursor.execute(INSERT_DATA, (time, station, value))
    db.commit()

# ,-------------------------,
# | Sensor ID definitions.  |
# '-------------------------'
sensor_id = {'water_temperature'     :  0,
             'barometer_pressure'    :  5,
             'barometer_temperature' :  6,
             'humidity_humidity'     : 10,
             'humidity_temperature'  : 11,
             'ambient_light_0'       : 15,
             'ambient_light_1'       : 16,
             'ph_level'              : 20}

# ,---------------------------------,
# | Function to create a database.  |
# '---------------------------------'
def create_database(cursor):

    try:
        cursor.execute(
            "CREATE DATABASE {} CHARACTER SET utf8 COLLATE utf8_bin".format(DB_NAME))
    except mysql.connector.Error as err:
        if PRINT_OUTPUT:
            print("\tFailed to create database: {}".format(err))
        exit(1)

# ,-----------------------------------------,
# | Functions to query the database tables. |
# '-----------------------------------------'

QUERY_STATION = ("SELECT id FROM stations WHERE mac = %s")

def get_station_id(mac):
    if PRINT_OUTPUT:
        print("Station {} is ".format(mac.decode()), end="")
    cursor.execute(QUERY_STATION, (mac,))
    id = cursor.fetchone()
    if id:
        if PRINT_OUTPUT:
            print("{}.".format(id[0]))
        return id[0]
    else:
        if PRINT_OUTPUT:
            print("unknown.")
        return None

QUERY_SENSOR = ("SELECT sensor FROM sensors WHERE id = %s")

def get_sensor_name(id):
    if PRINT_OUTPUT:
        print("Sensor {} is ".format(id), end="")
    cursor.execute(QUERY_SENSOR, (id,))
    name = cursor.fetchone()
    if name:
        if PRINT_OUTPUT:
            print("{}.".format(name[0].decode()))
        return name[0]
    else:
        if PRINT_OUTPUT:
            print("unknown.")
        return None

# =============================================================================
# Main program.
# =============================================================================

# ,-----------------------------,
# | Open database connection.   |
# '-----------------------------'
if PRINT_OUTPUT:
    print("Initialising.\n")
    print("Database:")

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor()

# ,---------------------------------------------,
# | Create the database if it doesn't exist.    |
# '---------------------------------------------'
try:
    db.database = DB_NAME
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        if PRINT_OUTPUT:
            print("\tCreating new database \"{}\": ".format(DB_NAME))
        create_database(cursor)
        db.database = DB_NAME
    else:
        if PRINT_OUTPUT:
            print(err)
        exit(1)
else:
    if PRINT_OUTPUT:
        print("\tDatabase \"{}\" already exists.".format(db.database))

# ,-----------------------------------------,
# | Create the tables if they don't exist.  |
# '-----------------------------------------'
for name, ddl in TABLES.items():
    try:
        cursor.execute(ddl)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            if PRINT_OUTPUT:
                print("\tTable \"{}\" already exists.".format(name))
        else:
            if  PRINT_OUTPUT:
                print(err.msg)
    else:
        if PRINT_OUTPUT:
            print("\tCreated new table \"{}\"".format(name))

if PRINT_OUTPUT:
    print("")

# ,-----------------------------,
# | Populate the sensors table. |
# '-----------------------------'
if PRINT_OUTPUT:
    print("Entering sensor ID.")
for sensor, id in sensor_id.items():
    insert_value_sensor(cursor, sensor, id)

#if PRINT_OUTPUT:
#    print("Sensors:")

#for sensor_id in range (0,20):
#    get_sensor_name(sensor_id)
#    if sensor_id:
#    print("Sensor ID {} = {}.".format(sensor_id, get_sensor_name(sensor_id)))


# -----------------------------------------------------------------------------
# Set up and bind UDP socket.
# -----------------------------------------------------------------------------
poller = select.poll()
if DATA_OVER_USB:
    PACKET_SIZE = 20
    SERIAL_PORT = '/dev/cu.usbmodemPy5a3af1'
    BAUDRATE = 9600
    ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUDRATE, bytesize=serial.EIGHTBITS, timeout=2)
    poller.register(ser)
else:
    if PRINT_OUTPUT:
        print("Networking:")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    poller.register(socket)

    if PRINT_OUTPUT:
        print("\tBinding socket to {}, port {}".format(UDP_IP, UDP_PORT))
    sock.bind((UDP_IP, UDP_PORT))

# -----------------------------------------------------------------------------
# Waits for initial connection and sends current date and time.
# -----------------------------------------------------------------------------

#       ,-------------------------------------------------------,
#       | The intent for this function is to provide a fallback |
#       | method for the station sensor board to set it's clock |
#       | after being off without a battery back up.            |
#       | It needs to be triggered by a request, which is       |
#       | difficult because the data packet structure is fixed. |
#       | At the moment this function is not called as the time |
#       | is created by this program rather than the station    |
#       | sensor board.                                         |
#       '-------------------------------------------------------'

def set_time():
    if PRINT_OUTPUT:
        print("Waiting for NTP request.\n")

    waiting_ntp = True
    while waiting_ntp:
        data, addr = sock.recvfrom(512)
        stringdata = data.decode('utf-8')
        if stringdata == "ntp":
            if PRINT_OUTPUT:
                print("Received request for NTP.")
            ntp_string = "{}".format(datetime.now())
            ntp_bytes = ntp_string.encode('utf-8')
            ntp_tuple = time.strptime(ntp_string, "%Y-%m-%d %H:%M:%S.%f")
            packet="{},{},{},{},{},{},{},{}".format(ntp_tuple.tm_year,\
                                                    ntp_tuple.tm_mon,\
                                                    ntp_tuple.tm_mday,\
                                                    ntp_tuple.tm_hour,\
                                                    ntp_tuple.tm_min,\
                                                    ntp_tuple.tm_sec,\
                                                    ntp_tuple.tm_wday,\
                                                    ntp_tuple.tm_yday)
            if PRINT_OUTPUT:
                print("Packet = {}.".format(packet))
            sock.sendto(packet.encode('utf-8'), addr)
            waiting_ntp = False

# -----------------------------------------------------------------------------
# Listen to socket.
# -----------------------------------------------------------------------------
error = False # Error trapping variable.
#set_time()

if PRINT_OUTPUT:
    print("Waiting for sensor data.\n")

while not error:
    avail = poller.poll()
    assert len(avail) == 1, "Poller returned more then one object"
    fd = avail[0][0]
    emask = avail[0][1]
    if (emask & select.POLLIN or emask & select.POLLPRI):
        if DATA_OVER_USB:
            iw = 'in_waiting'
            if not hasattr(ser, iw):
                iw = 'inWaiting'
                if not hasattr(ser, iw):
                    raise AttributeError("Ser object doesn't have in_waiting or inWaiting atrributes!")
            to_read = getattr(ser, iw)() # call the relevant function
            print("GOT to_read ",to_read)
            if to_read == PACKET_SIZE:
                data = ser.read(PACKET_SIZE)
                station_mac,\
                sensor_id,\
                sensor_data = struct.unpack("@12sHf", data)
                print("GOT DATA: %s %s %s" % (station_mac, sensor_id, sensor_data))
            else:
                # Just clear the output buffer
                ser.read(to_read)
        else:
            data, addr = sock.recvfrom(512)
    elif emask & select.POLLHUP or  emask & select.POLLERR:
        print("POLLHUP OR POLLERR")
        sys.exit(status=1)
    else:
        continue # connection could just be available for write for DATA_OVER_USB

    if PRINT_OUTPUT:
        print("Received {} bytes of sensor data.".format(len(data)))

    # Unpack the UDP data into it's components.
    station_mac,\
    sensor_id,\
    sensor_data = struct.unpack("@12sHf", data)

    # Store station MAC address and get ID.
    station = get_station_id(station_mac)
    if not station:
        insert_value_station(cursor, station_mac)
        station = get_station_id(station_mac)

    sensor_name = get_sensor_name(sensor_id)
    if sensor_name:
        print("Sensor {} reading = {}.".format(sensor_name.decode(), sensor_data))

    # ,-------------------------------------------------------,
    # | Currently the time stamp is made here for convenience |
    # | in case the station board cannot set it's clock.      |
    # '-------------------------------------------------------'
    read_time = datetime.now()

    sensor_data = (read_time, station, sensor_name, sensor_data)
    insert_value_data(cursor, sensor_data)

# -----------------------------------------------------------------------------
# Tidy up.
# -----------------------------------------------------------------------------
if DATA_OVER_USB:
    ser.close()
else:
    sock.close()
cursor.close()
db.close()
