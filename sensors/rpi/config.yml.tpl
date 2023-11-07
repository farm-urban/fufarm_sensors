APP:
  mock: False
  log_level: "DEBUG"
  poll_interval: 60 * 5
  gpio_sensors: False
  station_id: "main_sump"

MQTT:
  username: MQTT_USER
  password: MQTT_PASSWORD
  host: MQTT_HOST
  port: 1883
  sensor_topic: "main_sump/sensor"
  bluelab_topic: "bluelab"

BLUELAB:
  available: False
  tag_to_stationid: [["52rf", "lettus_grow"], ["4q3f", "main_sump"]]
  log_dir: "/home/pi/.local/share/Bluelab/Connect/logs"
