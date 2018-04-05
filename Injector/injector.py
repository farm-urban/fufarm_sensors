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

import logging
import time

# local imports
import fu_database
import fu_connector

logger = logging.getLogger(__name__)

def main(serial_config=None, socket_config=None, database=None,
         connector=None, max_readings=None):
    if not database:
        database = fu_database.Database(db_config=fu_database.db_config())
    if not connector:
        connector = fu_connector.connectorFactory(socket_config=socket_config,
                                                  serial_config=serial_config)
    #set_time()
    i = 0
    logger.info("Waiting for sensor data.\n")
    while True:
        if max_readings and i >= max_readings:
            break
        data = connector.get_data()
        if data:
            logger.info("Received %s bytes of sensor data.", len(data))
            database.process_data(data)
        time.sleep(1)
        i += 1

    connector.shutdown()
    database.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
