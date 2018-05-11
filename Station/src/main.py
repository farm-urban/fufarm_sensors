"""
    This program tests the feasibility of a sensor monitoring system

    Copyright (C) 2018  Darren Faulke (VEC), Jens Thomas (Farm Urban)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
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

def get_time():
    """
#   | The RTC module can set time directly from an NTP server   |
#   | using e.g.                                                |
#   |       rtc.ntp_sync("pool.ntp.org")                        |
#   | but testing is on a local network without access to an    |
#   | NTP server. Instead this function sends a command to get  |
#   | a datatime packet from the database injector.             |
    """
    old_time = RTC.now()
    if NTP_AVAILABLE:
        RTC.ntp_sync(NTP_ADDRESS)
        new_time = RTC.now()
        out_str = """Getting time from NTP server {0}
Current time is {1}
Revised time is {2}""".format(NTP_ADDRESS, old_time, new_time)
        logger.info(out_str)
    else:
        packet = "ntp"
        SOCK.sendto(packet, HOST_ADDRESS)
        ntp_time, ip_from = SOCK.recvfrom(512)
        dec_time = ntp_time.decode('utf-8')
        set_time = tuple(map(int, dec_time.split(",")))
        RTC.init(set_time)
        new_time = RTC.now()
        out_str = """Getting time from database injector.
Current time is {0}
Revised time is {1}""".format(old_time, new_time)
        logger.info(out_str)


def send_data(sensor, value):
    """Takes readings and sends data to database injector."""
    # Pack the data into a C type structure.
    packet = struct.pack("@12sHf", STATION_MAC, sensor, value)
    logger.info("Sent {} bytes.\nData packet = {}".format(len(packet), packet))
    if DATA_OVER_USB:
        UART.write(packet)
    else:
        SOCK.sendto(packet, HOST_ADDRESS)
    time.sleep(1)

def take_readings():
    pycom.rgbled(BLUE) # Change the LED to indicate that it is taking readings.
    if lts_ready: # DS18B20 liquid temperature sensor.
        logger.info("Water temperature readings:")
        liquid_temp_sensor.start_conversion()
        reading = False
        while not reading:
            water_temperature = liquid_temp_sensor.read_temp_async()
            if water_temperature is not None:
                reading = True
        logger.info("Water temperature = {} \u00b0C.".format(water_temperature))
        send_data(sensors['water_temperature'], water_temperature)

    if barometer_ready: # MPL3115A2 barometer sensor.
        logger.info("Barometer readings:")
        barometer_temperature = barometric_pressure.temperature()
        logger.info("Temperature = {} \u00b0C".format(barometer_temperature))
        send_data(sensors['barometer_temperature'], barometer_temperature)

    if humidity_sensor_ready: # SI7006A20 humidity sensor.
        logger.info("Humidity sensor readings:")
        humidity_humidity = humidity_sensor.humidity()
        humidity_temperature = humidity_sensor.temperature()
        logger.info("Humidity    = {} %.".format(humidity_humidity))
        send_data(sensors['humidity_humidity'], humidity_humidity)
        logger.info(u"Temperature = {} \u00b0C.".format(humidity_temperature))
        send_data(sensors['humidity_temperature'], humidity_temperature)

    if light_sensor_ready: # LTR329ALS01 light sensor.
        logger.info("Ambient light sensor readings:")
        ambient_light_0 = light_sensor.light()[0]
        ambient_light_1 = light_sensor.light()[1]
        logger.info("Light level (sensor 0) = {} lx.".format(ambient_light_0))
        send_data(sensors['ambient_light_0'], ambient_light_0)
        logger.info("Light level (sensor 1) = {} lx.".format(ambient_light_1))
        send_data(sensors['ambient_light_1'], ambient_light_1)

    pycom.rgbled(GREEN)
    return

RTC = machine.RTC() # Get date and time from server.
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
# DS18B20
lts_ready = lts_pin.reset()
logger.info("Liquid temperature sensor present = %s.", lts_ready)

# MPL3115A2
barometer_ready = barometric_pressure._read_status()
logger.info("Barometer sensor present = %s.", barometer_ready)

#   ,-----------------------------------------------------------,
#   | There are no available functions to test the presence of  |
#   | the light or humidity sensors so these are just assumed   |
#   | to be available for now. It should be possible to simply  |
#   | scan the I2C bus at the addresses for each sensor to      |
#   | detect them.                                              |
#   '-----------------------------------------------------------'

# LTR329ALS01
light_sensor_ready = True       # There is no available function to test.
logger.info("Light sensor present = %s.", light_sensor_ready)
# SI7006A20
humidity_sensor_ready = True    # There is no available function to test.
logger.info("Humidity sensor present = %s.", humidity_sensor_ready)

# =============================================================================
# Main loop.
# =============================================================================
#get_time()
logger.info("Starting Main Loop")
chrono.start()
start_time = time.time()
error = False
while not error:
    check_time = time.time()
    elapsed_time = check_time - start_time
    if elapsed_time >= SENSOR_INTERVAL * 60:
        take_readings()
        start_time = time.time()
