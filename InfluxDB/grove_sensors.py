#!/usr/bin/env python3
"""
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c
git clone https://github.com/Seeed-Studio/grove.py
export PYTHONPATH=/opt/grove.py

sudo bash -c "cat <<EOF >/etc/systemd/system/bruntwood_sensors.service
[Unit]
After=openvpn-client@rpizero1.service

[Service]
ExecStart=python3 /opt/fu_sensors/InfluxDB/grove_sensors.py
WorkingDirectory=/opt/fu_sensors/InfluxDB
Environment="PYTHONPATH=/opt/grove.py"
Restart=always
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=bruntwood_sensors
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOF
"

sudo systemctl enable bruntwood_sensors.service
sudo systemctl start bruntwood_sensors.service


"""
import requests
import time

from grove import grove_ultrasonic_ranger

INFLUX_URL = 'http://10.8.0.1:8086/write?db=bruntwood'
STATION_MAC = 'bruntwood'
SAMPLE_WINDOW = 60 * 5
MOCK = False


def send_data(iline):
    print('sending data\n{}'.format(iline))
    if MOCK:
        return
    success = False
    number_of_retries = 3
    while not success and number_of_retries > 0:
        try:
            requests.post(INFLUX_URL, data=iline)
            success = True
        except Exception as e:
            print('network error: {}'.format(e))
            number_of_retries -= 1
            pass
    return success


def readings_to_influxdb_line(readings, station_id, include_timestamp=False):
    data = ""
    for k, v in readings.items():
        data += 'fu_sensor,stationid={},sensor={} measurement={}' \
               .format(station_id, k, v)
        if include_timestamp is True:
            timestamp = utime.mktime(rtc.now())
            data += ' {}000000000'.format(timestamp)
        data += "\n"
    return data

pin = 5
sonar = grove_ultrasonic_ranger.GroveUltrasonicRanger(pin)

readings = {}
while True:
    sample_start = time.time()
    sample_end = sample_start + SAMPLE_WINDOW
    rate_cnt = 0
    while time.time() < sample_end:
        pass
    time.sleep(2)  # Need to add in pause or the distance sensor or else it measures 0.0
    readings['distance'] = sonar.get_distance()
    iline = readings_to_influxdb_line(readings, STATION_MAC)
    success = send_data(iline)
