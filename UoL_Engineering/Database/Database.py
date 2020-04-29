#!/usr/bin/env python

import MySQLdb
import datetime
import time
from time import strftime
import sys

#import all the reading functions from Sensor folder
sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/water_temp')
from water_temp import temp_read

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/weather_sensor')
from weather_sensor import weather_read

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors')
from images import convertToBinaryData
image = '/home/pi/Vertical_Farm/Sensors/Images/chard.jpg'

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/water_level')
from water_level import distance

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/pH')
from pH import pH_read

sys.path.insert(0, '/home/pi/Vertical_Farm/Sensors/EC')
from EC import EC_read

#variables for MySQL
db = MySQLdb.connect(host= "remotemysql.com", user="o0sRSRjnwl", passwd="n4J1tq4yYW", db="o0sRSRjnwl")  #connection parameters (host_name, username, password, databse_name)
cur = db.cursor()

while True:

    water_temp = temp_read()

    weather = weather_read()
    air_temp = weather[0]
    humidity = weather[1]
    pressure = weather [2]

    distance = distance()

    pH = pH_read()
    EC = EC_read()

    #binary_image = convertToBinaryData(image)

    print water_temp
    print air_temp
    print humidity
    print pressure
    print distance
    print pH
    print EC
    #print binary_image

    datetimeWrite = (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
    print datetimeWrite

    sql = ("""INSERT INTO hydroponic_vertical_farm (date,water_temp,humidity,pressure,air_temp,water_level,pH,EC) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (datetimeWrite,water_temp, humidity, pressure, air_temp, distance, pH, EC))
    try:
        print "Writing to database..."
        #Execute the SQL command
        cur.execute(*sql)
        #Commit your changes in the database
        db.commit()
        print "Write complete"

    except:
        db.rollback()
        print "Failed writing to database"

    cur.close()
    db.close()
    break

