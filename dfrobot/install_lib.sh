#!/bin/bash

LIBDIR=$HOME/Arduino/libraries
CLI_DIR=/opt/arduino-cli

export PATH=$CLI_DIR/bin:$PATH
if [ ! -f  $CLI_DIR/bin/arduino-cli ]
then
    echo "Running setup"
    mkdir $CLI_DIR
    pushd $CLI_DIR
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
    popd
    arduino-cli config init
    arduino-cli core update-index
    arduino-cli core install  arduino:avr
fi

# arduino-cli board list
# arduino-cli lib search debouncer

# For SEN0137 Temperature and Humidity sensor
arduino-cli lib install "DHT sensor library for ESPx"

# For DFR0198: Waterproof DS18B20 Sensor Kit
arduino-cli lib install OneWire

# JSON
arduino-cli lib install ArduinoJson

# DEFOBOT EC
#wget https://github.com/DFRobot/DFRobot_EC/archive/master.zip
#unzip master.zip
#rm master.zip
#mv DFRobot_EC-master $LIBDIR
git clone https://github.com/linucks/DFRobot_EC.git $LIBDIR/DFRobot_EC

# DEFOBOT pH
git clone https://github.com/linucks/DFRobot_PH.git $LIBDIR/DFRobot_PH
