#!/bin/bash
export PATH=/opt/arduino-cli/bin:$PATH
arduino-cli compile --fqbn arduino:avr:leonardo dfrobot \
&& \
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo  dfrobot
