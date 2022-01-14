
Use Atom to get repl to access wipy

To reset the filesystem
```
import os, machine
os.fsformat('/flash') OR os.mkfs('/flash')
machine.reset()
```

+
+To check a connection with curl:
+
+```
+curl -i -XPOST 'http://farmuaa1.farmurban.co.uk:8086/api/v2/write?bucket=cryptfarm&org=Farm%20Urban' \
+  --header 'Authorization: Token scW9V68kenPTzEkGUAtky-7awOMuo71pPGnCJ3gEdJWNNFBrlvp5atHTSFttVY4rRj0796xBgkuaF_YkSQExBg==' \
+  --data-raw 'sensors,station_id=farmwipy1 humidity_temperature=2.620937e+01,ambient_light_0=8.000000e+00,humidity_humidity=9.385734e+01,ambient_light_1=4.000000e+00,barometer_pressure=1.039117e+05,barometer_temperature=2.418750e+01'
+```
