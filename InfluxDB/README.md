## Wipy Code
Code lives in InfluxDB/pysense

## Raspberry Pi
* [GPIO Layout](https://www.raspberrypi.org/documentation/usage/gpio/)

## Random Notes
PyMakr.json
/Users/jmht/Library/Application Support/Code/User/pymakr.json


Use InfluxDB:
https://www.influxdata.com/developers/
https://docs.influxdata.com/influxdb/v1.7/introduction/getting-started/

Setup on mac with homebrew:

To have launchd start influxdb now and restart at login:
  brew services start influxdb
Or, if you don't want/need a background service you can just run:
  influxd -config /usr/local/etc/influxdb.conf

  login with:
  influx -precision rfc3339

DB schema
measurement name:
fu_sensor

fields (not indexed):
value

tags (indexed):
stationid
sensor

# Log in to influxdb and setup database and measurement
create database farmdb
use farmdb


Line protocol
https://docs.influxdata.com/influxdb/v1.7/write_protocols/line_protocol_tutorial/

weather,location=us-midwest temperature=82,humidity=71 1465839830100400200

fu_sensor,stationid=XX,sensor=XX value=XX <TIMESTAMP>

curl -i -XPOST "http://localhost:8086/write?db=science_is_cool" --data-binary 'weather,location=us-midwest temperature=82 1465839830100400200'



https://github.com/ayoy/upython-aq-monitor


HC SRO4 sensor stuff
HR-SR04+ is to work at 3V (https://cpc.farnell.com/multicomp-pro/psg04176/ultrasonic-distance-sensor/dp/SN36937)

* https://core-electronics.com.au/tutorials/hc-sr04-ultrasonic-sensor-with-pycom-tutorial.html
* https://github.com/mithru/MicroPython-Examples/tree/master/08.Sensors/HC-SR04


    # "address": "/dev/cu.usbmodemPy5a3af1",
