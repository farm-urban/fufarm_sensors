"""Configuration variables
"""
LOG_LEVEL = "DEBUG"
DATA_OVER_USB = False  # jmht - send data over the USB cable rather then wifi

# =============================================================================
# Networking.
# =============================================================================
NETWORK_SSID = "JensIsAwesome"  # Router broadcast name.
NETWORK_KEY = "12345678"  # Access key.
NETWORK_TIMEOUT = 20  # Connection timeout (s)

STATION_MAC = None
STATIC_IP = False
# These are only needed for static IP address.
NETWORK_IP = "192.168.0.103"  # IP address.
NETWORK_MASK = "255.255.255.0"  # Network mask.
NETWORK_GATEWAY = "192.168.0.1"  # Gateway.
NETWORK_DNS = "192.168.0.1"  # DNS server (N/A).
NETWORK_CONFIG = (NETWORK_IP, NETWORK_MASK, NETWORK_GATEWAY, NETWORK_DNS)

HOST_NAME = "192.168.4.1"  # Raspberry pi address
HOST_PORT = 3000  # UDP port.
HOST_ADDRESS = (HOST_NAME, HOST_PORT)

NTP_AVAILABLE = False  # NTP server available?
NTP_ADDRESS = "pool.ntp.org"
SENSOR_INTERVAL = 0.2

#   ,-----------------------------------------------------------,
#   | All sensors are set up here to avoid modifying code for   |
#   | each station. Ideally, the sensor availability should be  |
#   | determined and then used if they are present, otherwise   |
#   | ignored.                                                  |
#   | For this to work properly, a database of sensors and IDs  |
#   | should be maintained as it is difficult to process UDP    |
#   | packets that are inconsistent.                            |
#   '-----------------------------------------------------------'

#   ,-----------------------------------------------------------,
#   | This is a dictionary to define sensor numbers from a key. |
#   | Sensors are grouped in 5s so that more sensors may be     |
#   | added at a later date.                                    |
#   | These sensor ID are also encoded into the database.       |
#   | This allows the sensor ID to be sent as part of the data  |
#   | packet and the data inserted into the database by 'key'   |
#   | rather than by ID.                                        |
#   '-----------------------------------------------------------'
SENSORS = {
    "water_temperature": 0,
    "barometer_pressure": 5,
    "barometer_temperature": 6,
    "humidity_humidity": 10,
    "humidity_temperature": 11,
    "ambient_light_0": 15,
    "ambient_light_1": 16,
    "ph_level": 20,
}
