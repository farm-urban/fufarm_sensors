# FROM homeassistant/aarch64-base-python
FROM homeassistant/amd64-base-python

ENV BASEDIR=/sensors
ENV RPIDIR=$BASEDIR/rpi
RUN mkdir $BASEDIR

# Copy data for add-on
COPY rpi $RPIDIR
COPY rpi_arduino_shield $BASEDIR/rpi_arduino_shield

WORKDIR $RPIDIR
RUN pip3 install -r requirements.txt
CMD [ "./rpi_mqtt_sensors.py" ]