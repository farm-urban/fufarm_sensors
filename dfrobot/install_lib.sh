#!/bin/bash
# arduino-cli lib search debouncer
# For SEN0137 Temperature and Humidity sensor
arduino-cli lib install "DHT sensor library for ESPx"
# For DFR0198: Waterproof DS18B20 Sensor Kit
arduino-cli lib install OneWire
# Json
arduino-cli lib install ArduinoJson

# DEFOBOT EC
wget https://github.com/DFRobot/DFRobot_EC/archive/master.zip
unzip master.zip
mv DFRobot_EC-master/ ~/Arduino/libraries/