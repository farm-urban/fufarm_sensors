import smbus2
import bme280

def weather_read() :
    
    port = 1
    address =0x77 #I2C device address
    bus = smbus2.SMBus(port)
    calibration_params = bme280.load_calibration_params(bus, address)

    data = bme280.sample(bus, address, calibration_params)

    temp = data.temperature
    hum = data.humidity
    press = data.pressure

    temp = round(temp,1)
    hum = round(hum,1)
    press = round(press,1)
    
    values = [temp, hum, press]
    return values
