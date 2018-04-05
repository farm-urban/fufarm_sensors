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


class Injector

class Connector

"""

import datetime
from datetime import datetime
import logging
import socket
import time
# 3rd-party imports
import serial

# local imports
import fu_database

logger = logging.getLogger(__name__)

TEST_CONNECTOR = None
USB_CONFIG = {'port' : '/dev/cu.usbmodemPy5a3af1',
              'baudrate' : 9600,
              'bytesize' : serial.EIGHTBITS
             }

class Connector(object):
    """Class for handling data transfer over sockets/USB/..."""
    def __init__(self, usb_config=None, socket_config=None):
        assert usb_config or socket_config, "Need configuration data!"
        self.serial = None
        self.socket = None
        self.in_waiting = None
        self.packet_size = 20
        if usb_config:
            for k in ['port', 'baudrate', 'bytesize']:
                assert k in usb_config
            port = usb_config['port']
            baudrate = usb_config['baudrate']
            bytesize = usb_config['bytesize']
            if port.startswith('loop://'): # for testing
                self.serial = serial.serial_for_url(port, baudrate=baudrate,
                                                    bytesize=bytesize, timeout=2)
            else:
                self.serial = serial.Serial(port=port, baudrate=baudrate,
                                            bytesize=bytesize, timeout=2)
            logger.debug("SETUP SERIAL %s", self.serial)
            self.in_waiting = 'in_waiting'
            if not hasattr(self.serial, self.in_waiting):
                self.in_waiting = 'inWaiting'
                if not hasattr(self.serial, self.in_waiting):
                    raise AttributeError("Ser object doesn't have in_waiting or inWaiting atrributes!")
            self.in_waiting = getattr(self.serial, self.in_waiting)
        elif socket_config:
            #UDP_IP = "192.168.0.101"
            #UDP_PORT = 9000
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # poller.register(socket)
            logger.info("\tBinding socket to {}, port {}".format(socket_config['UDP_IP'],
                                                                 socket_config['UDP_PORT']))
            self.socket.bind((socket_config['UDP_IP'], socket_config['UDP_PORT']))
        else:
            raise AttributeError

    def get_data(self):
        data = None
        if self.serial:
            to_read = self.in_waiting()
            logger.info("GOT to_read %s ", to_read)
            if to_read == self.packet_size:
                data = self.serial.read(self.packet_size)
            else:
                # Just clear the output buffer
                self.serial.read(to_read)
        elif self.socket:
            data, addr = self.socket.recvfrom(512)
        else:
            raise AttributeError
        return data

    def send(self, packet):
        if self.serial:
            self.serial.write(packet)
        elif self.socket:
            self.socket.sendto(packet, HOST_ADDRESS)
        else:
            assert AttributeError

    def shutdown(self):
        if self.serial:
            self.serial.close()
        elif self.socket:
            self.socket.close()
        else:
            raise AttributeError

    def Xset_time(self):
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
            data, addr = self.socket.recvfrom(512)
            stringdata = data.decode('utf-8')
            if stringdata == "ntp":
                logger.info("Received request for NTP.")
                ntp_string = "{}".format(datetime.now())
                #ntp_bytes = ntp_string.encode('utf-8')
                ntp_tuple = time.strptime(ntp_string, "%Y-%m-%d %H:%M:%S.%f")
                packet = "{},{},{},{},{},{},{},{}".format(ntp_tuple.tm_year,\
                                                        ntp_tuple.tm_mon,\
                                                        ntp_tuple.tm_mday,\
                                                        ntp_tuple.tm_hour,\
                                                        ntp_tuple.tm_min,\
                                                        ntp_tuple.tm_sec,\
                                                        ntp_tuple.tm_wday,\
                                                        ntp_tuple.tm_yday)
                logger.info("Packet = %s.", packet)
                self.socket.sendto(packet.encode('utf-8'), addr)
                waiting_ntp = False

def main(database=None, connector=None, max_readings=None):
    if not database:
        database = fu_database.Database(db_config=fu_database.DB_CONFIG)
    if not connector:
        connector = Connector(usb_config=USB_CONFIG)
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
