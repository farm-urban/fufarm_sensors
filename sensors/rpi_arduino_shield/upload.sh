#!/bin/bash
export PATH=/opt/arduino-cli/bin:$PATH

#folder_name=$(basename $PWD)
folder_name=$PWD

if [ -c /dev/ttyACM0 ]; then 
  atty=/dev/ttyACM0
elif [ -c /dev/ttyACM1 ]; then 
  atty=/dev/ttyACM1
else
  echo Cannot find valid tty file
  exit 1
fi

arduino-cli compile --fqbn arduino:avr:leonardo $folder_name
if [ $? -ne 0 ]; then
  echo Failed to compile!
  exit 1
fi

arduino-cli upload -p $atty --fqbn arduino:avr:leonardo  $folder_name
if [ $? -ne 0 ]; then
  echo Failed to upload!
  exit 1
fi

echo "To check serial output use: screen -S arduino  $atty 9600"
echo "To exit screen type: ctrl-a k"
