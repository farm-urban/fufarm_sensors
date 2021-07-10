
https://tasmota.github.io/docs/MQTT/

sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo apt-get install python3-pip
sudo pip3 install paho-mqtt

# To test

# subscribe to all topics and show debug info
mosquitto_sub -h 192.168.4.1 -p 1883  -t \# -d

# Get energy info
mosquitto_sub -h 192.168.4.1 -p 1883  -t tele/tasmota_5014E2/SENSOR 

## This periodically returns
{"Time":"1970-01-01T00:25:13","ENERGY":{"TotalStartTime":"2021-07-10T11:54:41","Total":0.003,"Yesterday":0.000,"Today":0.003,"Period":0,"Power":0,"ApparentPower":0,"ReactivePower":0,"Factor":0.00,"Voltage":0,"Current":0.000}}

# To force status update on all channels
mosquitto_pub -h 192.168.4.1 -p 1883 -t cmnd/tasmota_5014E2/Status -m "0"

# To force update on channel 10
mosquitto_pub -h 192.168.4.1 -p 1883 -t cmnd/tasmota_5014E2/Status -m "10"
# On status 10 channel
mosquitto_sub -h 192.168.4.1 -p 1883  -t  stat/tasmota_5014E2/STATUS10
## This returns
{"StatusSNS":{"Time":"1970-01-01T00:30:21","ENERGY":{"TotalStartTime":"2021-07-10T11:54:41","Total":0.004,"Yesterday":0.000,"Today":0.004,"Power":22,"ApparentPower":24,"ReactivePower":10,"Factor":0.91,"Voltage":246,"Current":0.097}}}

# Turn switch on or off
mosquitto_pub -h 192.168.4.1 -p 1883 -t cmnd/tasmota_5014E2/Power -m "1"
mosquitto_pub -h 192.168.4.1 -p 1883 -t cmnd/tasmota_5014E2/Power -m "TOGGLE"

# Change report interval
mosquitto_pub -h 192.168.4.1 -p 1883 -t cmnd/tasmota_5014E2/TelePeriod -m "10"
