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

from datetime import datetime
import logging
import struct
import sys
import mysql.connector
from mysql.connector import errorcode

logger = logging.getLogger(__name__)
# -----------------------------------------------------------------------------
# Database access.
# -----------------------------------------------------------------------------
DB_CONFIG = {
    'user': 'foo',
    'password': 'password',
    'host': 'localhost',
    'database' : 'farmurban'
    }

class Database(object):
    """Class for managing data in a database (currently MySQL)

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
    MOCK_SENSOR_ID = 9999
    sensor_id_map = {'water_temperature'     :  0,
                     'barometer_pressure'    :  5,
                     'barometer_temperature' :  6,
                     'humidity_humidity'     : 10,
                     'humidity_temperature'  : 11,
                     'ambient_light_0'       : 15,
                     'ambient_light_1'       : 16,
                     'ph_level'              : 20,
                     'mock'                  : MOCK_SENSOR_ID}

    def __init__(self, db_config):
        self.connection = None
        self.cursor = None
        self.setup_database(db_config)
        return

    def close(self):
        self.connection.close()
        self.cursor.close()

    def insert_value_station(self, mac):
        INSERT_STATION = ("INSERT IGNORE INTO stations (mac, id) VALUES (%s, %s)")
        logger.info("Storing station ID for %s", mac.decode)
        station_data = (mac, "NULL")
        self.cursor.execute(INSERT_STATION, station_data)
        self.connection.commit()

    def insert_value_sensor(self, name, id):
        INSERT_SENSOR = ("INSERT IGNORE INTO sensors (sensor, id) VALUES (%s, %s)")
        logger.info("ID {:2} = {}.".format(id, name))
        self.cursor.execute(INSERT_SENSOR, (name, id))
        self.connection.commit()

    def insert_value_data(self, data):
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
        self.cursor.execute(INSERT_DATA, (time, station, value))
        res = self.connection.commit()
        logger.info("Got result: %s" % res)

    def get_station_id(self, mac):
        QUERY_STATION = ("SELECT id FROM stations WHERE mac = %s")
        id_str = "unknown"
        self.cursor.execute(QUERY_STATION, (mac,))
        id = self.cursor.fetchone()
        if id:
            id = id[0]
            id_str = id
        else:
            id = None
        logger.info("Station %s is %s", mac.decode(), id_str)
        return id

    def get_sensor_name(self, id):
        QUERY_SENSOR = ("SELECT sensor FROM sensors WHERE id = %s")
        name_str = "unknown"
        self.cursor.execute(QUERY_SENSOR, (id,))
        name = self.cursor.fetchone()
        if name:
            name = name[0]
            name_str = name.decode()
        else:
            name = None
        logger.info("Sensor %s is %s", id, name_str)
        return name

    def connect_or_create_database(self, database):
        """Establish database connection or create the database if it doesn't exist."""
        try:
            self.connection.database = database
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.info("\tCreating new database \"{}\": ".format(database))
                self.create_database(database)
                self.connection.database = database
            else:
                logger.info(err)
                exit(1)
        else:
            logger.info("\tDatabase \"{}\" already exists.".format(self.connection.database))
        return

    def create_database(self, database):
        try:
            self.cursor.execute(
                "CREATE DATABASE {} CHARACTER SET utf8 COLLATE utf8_bin".format(database))
        except mysql.connector.Error as err:
            logger.citical("\tFailed to create database: {}".format(err))
            raise

    def create_tables(self):
        """Create the tables if they don't exist."""
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
        tables = {
            'stations' : (CREATE_TABLE_STATIONS),
            'sensors' : (CREATE_TABLE_SENSORS),
            'water_temperature' : (CREATE_TABLE_WATER_TEMPERATURE),
            'barometer_temperature' : (CREATE_TABLE_BAROMETER_TEMPERATURE),
            'humidity_humidity' : (CREATE_TABLE_HUMIDITY_HUMIDITY),
            'humidity_temperature' : (CREATE_TABLE_HUMIDITY_TEMPERATURE),
            'ambient_light_0' : (CREATE_TABLE_AMBIENT_LIGHT_0),
            'ambient_light_1' : (CREATE_TABLE_AMBIENT_LIGHT_1),
            'ph_level' : (CREATE_TABLE_PH_LEVEL),
            'mock' : (CREATE_TABLE_MOCK)
            }
        for name, ddl in tables.items():
            try:
                self.cursor.execute(ddl)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    logger.info("\tTable \"{}\" already exists.".format(name))
                else:
                    logger.info(err.msg)
            else:
                logger.info("\tCreated new table \"{}\"".format(name))

    def populate_sensors(self):
        """Populate the sensors table."""
        logger.debug("Entering sensor ID.")
        for sensor, id in self.sensor_id_map.items():
            self.insert_value_sensor(sensor, id)

    def process_data(self, data):
        """Process a received packet of sensor data"""
        # Unpack the UDP data into it's components.
        station_mac,\
        sensor_id,\
        sensor_data = struct.unpack("@12sHf", data)

        # Store station MAC address and get ID.
        station = self.get_station_id(station_mac)
        if not station:
            self.insert_value_station(station_mac)
            station = self.get_station_id(station_mac)

        sensor_name = self.get_sensor_name(sensor_id)
        if sensor_name:
            logger.info("Sensor %s reading = %s", sensor_name.decode(), sensor_data)
        # ,-------------------------------------------------------,
        # | Currently the time stamp is made here for convenience |
        # | in case the station board cannot set it's clock.      |
        # '-------------------------------------------------------'
        read_time = datetime.now()
        logging.debug("SENSOR DATA: %s %s %s %s", read_time, station, sensor_name, sensor_data)
        sensor_data = (read_time, station, sensor_name, sensor_data)
        self.insert_value_data(sensor_data)
        return

    def setup_database(self, db_config):
        logger.info("Initialising Database")
        database = db_config.pop('database')
        try:
            self.connection = mysql.connector.connect(**db_config)
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
        self.cursor = self.connection.cursor()
        self.connect_or_create_database(database)
        self.create_tables()
        self.populate_sensors()
        return
