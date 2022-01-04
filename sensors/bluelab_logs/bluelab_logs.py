#!/usr/bin/env python3

from collections import namedtuple
import csv
import datetime
from enum import Enum
import os
from pathlib import Path
import sys
from typing import Union, Optional
import warnings

LOGDIR = '/home/pi/.local/share/Bluelab/Connect/logs'
GrowData = namedtuple('GrowData', ['tag', 'timestamp', 'ec', 'ph', 'temp'])

class ParseMode(Enum):
    MONITOR1 = 1
    MONITOR2 = 2
    CONTROL1 = 3
    CONTROL2 = 4

def get_last_log(logdir: Union[str, Path]):

    def time_tuple(p):
        x = p.stem.split()
        return (datetime.datetime.strptime(x[0], '%Y-%m-%d').date(), int(x[1]))

    if not isinstance(logdir, Path):
        logdir = Path(logdir)

    csv_files = [x for x in logdir.iterdir() if (x.is_file() and x.suffix == '.csv')]
    latest = sorted(csv_files, key=time_tuple)[-1]
    return logdir / latest


def get_data(csv_file: Union[str, Path]):
    """See bluelab_logs directory for csv files with format
    """
    if not isinstance(csv_file, Path):
        csv_file = Path(csv_file)
    readings = []
    with open(csv_file) as f:
        reader = csv.reader(f)
        mode, systems = parse_header(reader)
        for i, row in enumerate(reader):
            assert row[1] == 'EC', f"Incorrect EC unit: {row[1]}"
            assert row[2] == 'C', f"Incorrect temp unit: {row[2]}"
            if mode == ParseMode.MONITOR1:
                data = parse_monitor1(row, systems)
            elif mode == ParseMode.CONTROL1:
                data = parse_control1(row, systems)
            elif mode == ParseMode.MONITOR2:
                data = parse_monitor2(row, systems)
            elif mode == ParseMode.CONTROL2:
                data = parse_control2(row, systems)
            readings.append(data)
    return readings

def parse_header(reader):
    # Check header to determine node and get system names
    systems = []
    row0 = next(reader)
    ncol = len(row0)
    if ncol == 6:
        mode = ParseMode.MONITOR1
    elif ncol == 9:
        field = row0[6].strip()
        if field == 'run time':
            mode = ParseMode.CONTROL1
        else:
            mode = ParseMode.MONITOR2
    elif ncol == 15:
        mode = ParseMode.CONTROL2
    else:
        raise RuntimeError("Unrecognised csv format - too many systems?")

    # Add system names
    tag1 = row0[3].split()[0]
    systems.append(tag1)
    if mode == ParseMode.MONITOR2:
        tag2 = row0[6].split()[0]
        systems.append(tag2)
    elif mode == ParseMode.CONTROL2:
        tag2 = row0[9].split()[0]
        systems.append(tag2)

    return mode, systems

def parse_monitor1(row, systems):
    timestamp = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') 
    try:
        ec1 = float(row[3])
    except ValueError:
        warnings.warn(f"Invalid EC value: {row[3]}")
        ec1 = -9999
    try:
        ph1 = float(row[4])
    except ValueError:
        warnings.warn(f"Invalid pH value: {row[4]}")
        ph1 = -9999
    try:
        temp1 = float(row[5])
    except ValueError:
        warnings.warn(f"Invalid temp value: {row[5]}")
        temp1 = -9999

    return [GrowData(systems[0], timestamp, ec1, ph1, temp1)]


def parse_control1(row, systems):
    timestamp = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') 
    try:
        ec1 = float(row[3])
    except ValueError:
        warnings.warn(f"Invalid EC value: {row[3]}")
        ec1 = -9999
    try:
        ph1 = float(row[4])
    except ValueError:
        warnings.warn(f"Invalid pH value: {row[4]}")
        ph1 = -9999
    try:
        temp1 = float(row[5])
    except ValueError:
        warnings.warn(f"Invalid temp value: {row[5]}")
        temp1 = -9999

    return [GrowData(systems[0], timestamp, ec1, ph1, temp1)]


def parse_monitor2(row, systems):
    timestamp = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') 
    try:
        ec1 = float(row[3])
    except ValueError:
        warnings.warn(f"Invalid EC value: {row[3]}")
        ec1 = -9999
    try:
        ph1 = float(row[4])
    except ValueError:
        warnings.warn(f"Invalid pH value: {row[4]}")
        ph1 = -9999
    try:
        temp1 = float(row[5])
    except ValueError:
        warnings.warn(f"Invalid temp value: {row[5]}")
        temp1 = -9999
    d1 = GrowData(systems[0], timestamp, ec1, ph1, temp1)

    try:
        ec2 = float(row[6])
    except ValueError:
        warnings.warn(f"Invalid EC2 value: {row[6]}")
        ec2 = -9999
    try:
        ph2 = float(row[7])
    except ValueError:
        warnings.warn(f"Invalid pH2 value: {row[7]}")
        ph2 = -9999
    try:
        temp2 = float(row[8])
    except ValueError:
        warnings.warn(f"Invalid temp2 value: {row[8]}")
        temp2 = -9999
    d2 = GrowData(systems[1], timestamp, ec2, ph2, temp2)

    return [d1, d2]


def parse_control2(row, systems):
    timestamp = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') 
    try:
        ec1 = float(row[3])
    except ValueError:
        warnings.warn(f"Invalid EC value: {row[3]}")
        ec1 = -9999
    try:
        ph1 = float(row[4])
    except ValueError:
        warnings.warn(f"Invalid pH value: {row[4]}")
        ph1 = -9999
    try:
        temp1 = float(row[5])
    except ValueError:
        warnings.warn(f"Invalid temp value: {row[5]}")
        temp1 = -9999
    d1 = GrowData(systems[0], timestamp, ec1, ph1, temp1)

    try:
        ec2 = float(row[9])
    except ValueError:
        warnings.warn(f"Invalid EC2 value: {row[9]}")
        ec2 = -9999
    try:
        ph2 = float(row[10])
    except ValueError:
        warnings.warn(f"Invalid pH2 value: {row[10]}")
        ph2 = -9999
    try:
        temp2 = float(row[11])
    except ValueError:
        warnings.warn(f"Invalid temp2 value: {row[11]}")
        temp2 = -9999
    d2 = GrowData(systems[1], timestamp, ec2, ph2, temp2)

    return [d1, d2]


def sample_bluelab_data(last_timestamp: datetime.datetime, poll_interval: int, last_log: Optional[str]=None):
    BUFFER = 30
    if last_log is None:
        last_log = get_last_log(LOGDIR)
    data = get_data(last_log)
    values = []
    end = None
    nsystems = len(data[0])
    for d in data:
        d1 = d[0]
        if d1.timestamp <= last_timestamp:
            continue
        values.append(d)
    if not len(values):
        return None

    interval = last_timestamp - d1.timestamp
    if interval > datetime.timedelta(seconds=poll_interval + BUFFER):
        raise RuntimeError(f"Last value is outside expected range: {last_timestamp}:{d1.timestamp} | {interval}")
    
    # Results are averages of all values
    results = []
    if nsystems == 1:
        tag1 = values[-1][0].tag
        timestamp1 = values[-1][0].timestamp
        ec1 = sum([d[0].ec for d in values])/len(values)
        ph1 = sum([d[0].ph for d in values])/len(values)
        temp1 = sum([d[0].temp for d in values])/len(values)
        d1 = GrowData(tag1, timestamp1, ec1, ph1, temp1)
        results.append(d1)

    elif nsystems == 2:
        tag1 = values[-1][0].tag
        timestamp1 = values[-1][0].timestamp
        ec1 = sum([d[0].ec for d in values])/len(values)
        ph1 = sum([d[0].ph for d in values])/len(values)
        temp1 = sum([d[0].temp for d in values])/len(values)
        d1 = GrowData(tag1, timestamp1, ec1, ph1, temp1)
        results.append(d1)

        tag2 = values[-1][1].tag
        timestamp2 = values[-1][1].timestamp
        ec2 = sum([d[1].ec for d in values])/len(values)
        ph2 = sum([d[1].ph for d in values])/len(values)
        temp2 = sum([d[1].temp for d in values])/len(values)
        d2 = GrowData(tag2, timestamp2, ec2, ph2, temp2)
        results.append(d2)
    return results

## Unit tests
def test_control1():
    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 7, 11, 17, 51)
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    last_log = "/opt/fu_sensors/dfrobot/raspberrypi/bluelab_logs/control1.csv"
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp


def test_monitor2():
    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 8, 2, 7, 57)
    last_log = "/opt/fu_sensors/dfrobot/raspberrypi/bluelab_logs/monitor2.csv"
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp


def test_control2():
    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 8, 2, 7, 50)
    last_log = "/opt/fu_sensors/dfrobot/raspberrypi/bluelab_logs/control2.csv"
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp


if __name__ == "__main__":
    test_control2()

