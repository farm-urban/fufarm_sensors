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

Line protocol
https://docs.influxdata.com/influxdb/v1.7/write_protocols/line_protocol_tutorial/

weather,location=us-midwest temperature=82,humidity=71 1465839830100400200

fu_sensor,stationid=XX,sensor=XX value=XX <TIMESTAMP>

curl -i -XPOST "http://localhost:8086/write?db=science_is_cool" --data-binary 'weather,location=us-midwest temperature=82 1465839830100400200'



https://github.com/ayoy/upython-aq-monitor


Set up network

get data form sensors

send to osx influxdb

    # "address": "/dev/cu.usbmodemPy5a3af1",