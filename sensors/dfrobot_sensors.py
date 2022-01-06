import json
import logging
import serial
import time
import warnings

ARDUINO_TERMINAL = "/dev/ttyACM0"
BAUD_RATE = 9600


def parse_serial_json(myserial):
    """Don't think this is used anywhere yet"""
    buffer = ""
    MAXLOOP = 20
    loop_count = 0
    data = None
    while True:
        if loop_count >= MAXLOOP:
            warnings.warn("parse_serial_json exceeded MAXLOOP")
            return None
        buffer += myserial.read().decode("utf-8")
        try:
            data = json.loads(buffer)
            buffer = ""
        except json.JSONDecodeError:
            time.sleep(1)
        loop_count += 1
    return data


def sensor_readings():
    global serial_terminal, logger
    if serial_terminal.in_waiting > 0:
        line = serial_terminal.readline().decode("utf-8").rstrip()
        data = {}
        try:
            data = json.loads(line)
            logger.debug("dfrobot sensors got data:%s", data)
        except json.decoder.JSONDecodeError as e:
            logger.warning(
                "Error reading dfrobot Arduino data: %s\nDoc was: %s", e.msg, e.doc
            )
        #        data = parse_serial_json(ser)
        #        if data is None:
        #             warnings.warn("No data from parse_serial_json")
        #             data = {}
        #             send = False
        if DIRECT_SENSORS:
            data["flow"] = _flow_rate
            data["distance"] = _distance

        # Clear anything remaining
        while serial_terminal.in_waiting > 0:
            c = serial_terminal.read()
        serial_terminal.reset_input_buffer()
        serial_terminal.reset_output_buffer()
        return data
    else:
        return None


logger = logging.getLogger()

serial_terminal = serial.Serial(ARDUINO_TERMINAL, BAUD_RATE, timeout=1)
serial_terminal.flush()
