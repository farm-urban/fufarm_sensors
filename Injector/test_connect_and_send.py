#!/usr/bin/env python
import binascii
import socket
import struct

AP_IP_PORT = ("192.168.4.1", 3000)

sockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockt.setblocking(False)

sensor = 0  # water_temperature
value = 999
STATION_MAC = binascii.hexlify(b"123456")
packet = struct.pack("@12sHf", STATION_MAC, sensor, value)
print("SENDING ", packet)
sockt.sendto(packet, AP_IP_PORT)
