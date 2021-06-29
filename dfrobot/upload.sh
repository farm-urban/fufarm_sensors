#!/bin/bash
export PATH=/opt/arduino-cli/bin:$PATH

folder_name=$(basename $PWD)

arduino-cli compile --fqbn arduino:avr:leonardo $folder_name \
&& \
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo  $folder_name
