import pycom
LED = {'amber' : 0xFF8000,
       'black' : 0x000000,
       'blue'  : 0x0000FF,
       'green' : 0x00FF00,
       'red'   : 0xFF0000 }

pycom.heartbeat(False)  # Turn off pulsing LED heartbeat.
pycom.rgbled(LED['red'])