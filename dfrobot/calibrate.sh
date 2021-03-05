#!/bin/bash
export PATH=/opt/arduino-cli/bin:$PATH

usage="Usage $0 ph|ec";
atty=/dev/ttyACM0

if [ $# -ne 1 ]; then
    echo $usage
    exit 1;
fi

if [ $1 = "ph" ]
then
    sketch=ph_calibration
elif [ $1 = "ec" ]
then
    sketch=ec_calibration
else
    echo $usage
    exit 1;
fi

pushd $sketch
arduino-cli compile --fqbn arduino:avr:leonardo $sketch \
&& \
arduino-cli upload -p $atty --fqbn arduino:avr:leonardo  $sketch
popd

if [ $? -ne 0 ]; then
   echo "Error compling code"
   exit 1
fi

echo "To access type: screen -S arduino  $atty 9600"
echo "To exit screen type: ctrl-a k"
