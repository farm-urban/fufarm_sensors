## Laurence's sensors
Laurence's [spreadsheet](https://docs.google.com/spreadsheets/d/1RAleg7ZHxuUZmmoM4lozdfwikm91hurRqoSRQPs-0vs/edit#gid=290336845) with list of sensors.

## Sensors
### Gravity: Arduino Shield for Raspberry Pi B+/2B/3B/3B+/4B
* https://www.dfrobot.com/product-1211.html


### Gravity: DHT22 Temperature & Humidity Sensor
* https://www.dfrobot.com/product-1102.html

### Gravity: Analog Electrical Conductivity Sensor /Meter V2 (K=1)
* https://www.dfrobot.com/product-1123.html

### Gravity: Analog pH Sensor/Meter Kit V2
* https://www.dfrobot.com/product-1782.html

## Notes
Couldn't connect to the Arduino from the Raspberry Pi (via terminal from OSX) to do the pH and EC calibration due to what appear to be problems with how the terminal input is handled. Therefore copies of the relevant repositories were made and the code updated to work with an updated protocol:
* https://github.com/linucks/DFRobot_EC
* https://github.com/linucks/DFRobot_PH

Need to isolate the pH and EC probes if using in the same solution. A solution is:
* https://www.dfrobot.com/product-1621.html

For long-term use of pH probe, need to use industrial version of the pH probe:
* https://www.dfrobot.com/product-1110.html
* https://www.dfrobot.com/product-1074.html

For EC probe also need an industrial version. [Michael Ratcliffe](http://www.michaelratcliffe.com/) has a simple suggestion
* https://arduino.stackexchange.com/questions/49895/how-to-measure-electrical-conductivity-using-arduino

The specifications of the current probe are:
* Supply Voltage: 3.0~5.0V
* Output Voltage: 0~3.4V
* Probe Connector: BNC
* Signal Connector: PH2.0-3Pin
* Measurement Accuracy: ±5% F.S.
* K = 1.0

## Sensors to pins
|Sensor|Pin|
|---|---|
|CO2|A0|
|EC|A1|
|pH|A2|
|Temp & Humidity|D2|
|Wet Temp|D3|

### General installations
```
sudo apt-get install git
sudo apt-get install python-pip
```

The scripts pyserial-miniterm and pyserial-ports are installed in '/home/pi/.local/bin' which is not on PATH.
Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
