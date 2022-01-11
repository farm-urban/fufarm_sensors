
## InfluxDbCloud
To install command-line binaries (`influx`): https://docs.influxdata.com/influxdb/v2.0/install/

To setup authentication:

```
influx config create --config-name fu_cloud \
  --host-url https://westeurope-1.azure.cloud2.influxdata.com \
  --org accounts@farmurban.co.uk \
  --token <your-auth-token> \
  --active
  ```
  
**To create manually:**

File: ```~/.influxdbv2/configs```
``` 
[fu_cloud]
  url = "https://westeurope-1.azure.cloud2.influxdata.com"
  token = "jmhtEZEPNrX59lKNzhqtCPbbnDwUX605dZAo4ai-33FvO2MrR3TpM5e0eH08j2rwqbA7XT96ea_ssMwRi1hq01WEZA=="
  org = "accounts@farmurban.co.uk"
  active = true
```
### Data Backup
Oh host machine
```
influx query 'from(bucket: "cryptfarm") |> range(start: -1y)' --raw > cryptfarm.csv
```

On target machine
```
influx bucket create --name cryptfarm
influx write --bucket cryptfarm --format csv  --file cryptfarm.csv
```



#### CSV Export
To download data as csv for export (to e.g. Pandas):
```
influx query 'from(bucket:"Heath") |> range(start: 2021-07-13T18:00:00Z, stop: 2021-08-31T16:30:00Z)' --raw > heathdata.csv
```


To query schema: https://docs.influxdata.com/influxdb/cloud/query-data/flux/#explore-your-schema


## Use InfluxDB
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

## Log in to influxdb and setup database and measurement
create database farmdb
use farmdb

## Querying Influxdb data
## Using Flux


```
from(bucket: "cryptfarm")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "sensors" and  r["station_id"] == "rpi" and (r["_field"] == "tempair" or r["_field"] == "tempwet" or r["_field"] == "light"))
  |> map(fn: (r) => ({
  r with
  _value:
    if r["_field"] == "light" then (r["_value"] / 50.0) + 20.0
    else r["_value"]
  }))
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")

```

### Using FLUXQL
```
influx -precision rfc3339
SHOW DATABASES
USE FARMDB

SHOW MEASUREMENTS
name: measurements
name
----
fu_sensor

SHOW SERIES
key
---
fu_sensor,sensor=distance,stationid=rpi2utc
fu_sensor,sensor=flow_rate,stationid=rpi2utc

SHOW FIELD KEYS
name: fu_sensor
fieldKey    fieldType
--------    ---------
measurement float

SHOW TAG KEYS
name: fu_sensor
tagKey
------
sensor
stationid


SELECT <field_key>[,<field_key>,<tag_key>] FROM <measurement_name>[,<measurement_name>] WHERE <conditional_expression> [(AND|OR) <conditional_expression> [...]]

SELECT "measurement" FROM fu_sensor WHERE "sensor" = 'flow_rate' AND  time > now() - 1h

```


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
