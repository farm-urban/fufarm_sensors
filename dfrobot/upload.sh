#!/bin/bash
export PATH=/opt/arduino-cli/bin:$PATH

folder_name=$(basename $PWD)
atty=/dev/ttyACM0

arduino-cli compile --fqbn arduino:avr:leonardo $folder_name \
&& \
arduino-cli upload -p $atty --fqbn arduino:avr:leonardo  $folder_name

echo "To check serial output use: screen -S arduino  $atty 9600"
echo "To exit screen type: ctrl-a k"
