"""Configuration variables
"""
LOG_LEVEL = "DEBUG"
DATA_OVER_USB = False  # jmht - send data over the USB cable rather then wifi

# =============================================================================
# Networking.
# =============================================================================
NETWORK_SSID = "virginmedia7305656"  # Router broadcast name.
NETWORK_KEY = "vbvnqjxn"  # Access key.
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
SENSOR_INTERVAL = 60 * 10  # in seconds
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
