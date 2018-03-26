# =============================================================================
# This program tests the feasibility of a sensor monitoring system for
# Farm Urban.
#
# Licensing ?
#
# Darren Faulke (VEC)
# =============================================================================

#   ,-----------------------------------------------------------,
#   | These are the libraries for the PySense board sensors.    |
#   | These are from the PyCom github repository.               |
#   '-----------------------------------------------------------'
from pysense     import Pysense     # Main pysense module.
from LTR329ALS01 import LTR329ALS01 # Ambient light.
from MPL3115A2   import MPL3115A2   # Barometer & temperature.
#from MPL3115A2   import ALTITUDE    # Barometric pressure.
from MPL3115A2   import PRESSURE    # Barometric altitude.
from SI7006A20   import SI7006A20   # Humidity & temperature.

#   ,-----------------------------------------------------------,
#   | These are the libraries for the DS18B20 sensor.           |
#   | The onewire library is from the PyCom github repository.  |
#   | The machine library is built-in.                          |
#   '-----------------------------------------------------------'
from machine import Pin
from onewire import OneWire
from onewire import DS18X20     # Liquid temperature.

#import utime
from machine import RTC
# =============================================================================
# Flags.
# =============================================================================
error = False;

# =============================================================================
# Set up sensors.
# =============================================================================

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
sensors = {'water_temperature'    :  0,
           'barometer_pressure'   :  5,
           'barometer_temperature':  6,
           'humidity_humidity'    : 10,
           'humidity_temperature' : 11,
           'ambient_light_0'      : 15,
           'ambient_light_1'      : 16,
           'ph_level'             : 20}

#   ,-----------------------------------------------------------,
#   | These are the PySense specific sensors.                   |
#   '-----------------------------------------------------------'
board = Pysense()
light_sensor = LTR329ALS01(board)
barometric_pressure = MPL3115A2(board, mode=PRESSURE)
#barometric_altitude = MPL3115A2(board, mode=ALTITUDE)
humidity_sensor = SI7006A20(board)

#   ,-----------------------------------------------------------,
#   | This is the DS18B20 liquid temperature sensor.            |
#   '-----------------------------------------------------------'
lts_pin = OneWire(Pin('P10')) # Set up input GPIO.
liquid_temp_sensor = DS18X20(lts_pin)

#   ,-----------------------------------------------------------,
#   | Now let's see which sensors are attached and working.     |
#   '-----------------------------------------------------------'

'''DS18B20'''
lts_ready = lts_pin.reset()
if PRINT_OUTPUT:
    print("Liquid temperature sensor present = {}.".format(lts_ready))

'''MPL3115A2'''
barometer_ready = barometric_pressure._read_status()
if PRINT_OUTPUT:
    print("Barometer sensor present = {}.".format(barometer_ready))

#   ,-----------------------------------------------------------,
#   | There are no available functions to test the presence of  |
#   | the light or humidity sensors so these are just assumed   |
#   | to be available for now. It should be possible to simply  |
#   | scan the I2C bus at the addresses for each sensor to      |
#   | detect them.                                              |
#   '-----------------------------------------------------------'

'''LTR329ALS01'''
light_sensor_ready = True       # There is no available function to test.
if PRINT_OUTPUT:
    print("Light sensor present = {}.".format(light_sensor_ready))

'''SI7006A20'''
humidity_sensor_ready = True    # There is no available function to test.
if PRINT_OUTPUT:
    print("Humidity sensor present = {}.".format(humidity_sensor_ready))

if PRINT_OUTPUT:
    print("")

# =============================================================================
# Get date and time from server.
# =============================================================================
rtc = RTC()

#   ,-----------------------------------------------------------,
#   | The rtc module can set time directly from an NTP server   |
#   | using e.g.                                                |
#   |       rtc.ntp_sync("pool.ntp.org")                        |
#   | but testing is on a local network without access to an    |
#   | NTP server. Instead this function sends a command to get  |
#   | a datatime packet from the database injector.             |
#   '-----------------------------------------------------------'
def get_time():
    old_time = rtc.now()
    if NTP_AVAILABLE:
        rtc.ntp_sync(NTP_ADDRESS)
        new_time = rtc.now()
        if PRINT_OUTPUT:
            print("Getting time from NTP server {}.".format(NTP_ADDRESS))
            print("Current time is {}".format(old_time))
            print("Revised time is {}".format(new_time))
    else:
        packet = "ntp"
        sock.sendto(packet, HOST_ADDRESS)
        ntp_time, ip_from = sock.recvfrom(512)
        dec_time = ntp_time.decode('utf-8')
        set_time = tuple(map(int, dec_time.split(",")))
        rtc.init(set_time)
        new_time = rtc.now()
        if PRINT_OUTPUT:
            print("Getting time from database injector.")
            print("Current time is {}".format(old_time))
            print("Revised time is {}".format(new_time))

# =============================================================================
# Takes readings and sends data to database injector.
# =============================================================================
def send_data(mac, sensor, value):

    # Pack the data into a C type structure.
    packet = struct.pack("@12sHf", mac, sensor, value)

    if PRINT_OUTPUT:
        print("Sent {} bytes.".format(len(packet)))
        print("Data packet = {}.".format(packet))
        print("")

    if DATA_OVER_USB:
        uart.write(packet)
    else:
        sock.sendto(packet, HOST_ADDRESS)
    time.sleep(1)

def take_readings():

#   ,-----------------------------------------------------------,
#   | Change the LED to indicate that it is taking readings.    |
#   '-----------------------------------------------------------'
    pycom.rgbled(BLUE)

#   ,-------------------------------------------------------,
#   | DS18B20 liquid temperature sensor.                    |
#   '-------------------------------------------------------'
    if lts_ready:
        if PRINT_OUTPUT:
            print("Water temperature readings:")

        liquid_temp_sensor.start_conversion()
        reading = False
        while not reading:
            water_temperature = liquid_temp_sensor.read_temp_async()
            if water_temperature is not None:
                reading = True

        if PRINT_OUTPUT:
            print("\tWater temperature = {} \u00b0C.".format(water_temperature))
            print("")

        send_data(station_mac, sensors['water_temperature'], water_temperature)

#   ,-------------------------------------------------------,
#   | MPL3115A2 barometer sensor.                           |
#   '-------------------------------------------------------'
    if barometer_ready:
        if PRINT_OUTPUT:
            print("Barometer readings:")

        barometer_temperature = barometric_pressure.temperature()
        if PRINT_OUTPUT:
            print("\tTemperature = {} \u00b0C".format(barometer_temperature))
            print("")

        send_data(station_mac, sensors['barometer_temperature'], barometer_temperature)

#   ,-------------------------------------------------------,
#   | SI7006A20 humidity sensor.                            |
#   '-------------------------------------------------------'
    if humidity_sensor_ready:
        if PRINT_OUTPUT:
            print("Humidity sensor readings:")

        humidity_humidity = humidity_sensor.humidity()
        humidity_temperature = humidity_sensor.temperature()

        if PRINT_OUTPUT:
            print("\tHumidity    = {} %.".format(humidity_humidity))
            print("")

        send_data(station_mac, sensors['humidity_humidity'], humidity_humidity)

        if PRINT_OUTPUT:
            print("\tTemperature = {} \u00b0C.".format(humidity_temperature))
            print("")

        send_data(station_mac, sensors['humidity_temperature'], humidity_temperature)

#   ,-------------------------------------------------------,
#   | LTR329ALS01 light sensor.                             |
#   '-------------------------------------------------------'
    if light_sensor_ready:
        if PRINT_OUTPUT:
            print("Ambient light sensor readings:")

        ambient_light_0 = light_sensor.light()[0]
        ambient_light_1 = light_sensor.light()[1]

        if PRINT_OUTPUT:
            print("\tLight level (sensor 0) = {} lx.".format(ambient_light_0))
            print("")

        send_data(station_mac, sensors['ambient_light_0'], ambient_light_0)

        if PRINT_OUTPUT:
            print("\tLight level (sensor 1) = {} lx.".format(ambient_light_1))
            print("")

        send_data(station_mac, sensors['ambient_light_1'], ambient_light_1)

    pycom.rgbled(GREEN)

# =============================================================================
# Main loop.
# =============================================================================
#get_time()

error = False
take_readings()

chrono.start()
start_time = time.time()
while not error:

    check_time = time.time()
    elapsed_time = check_time - start_time
    if elapsed_time >= SENSOR_INTERVAL * 60:
        take_readings()
        start_time = time.time()
