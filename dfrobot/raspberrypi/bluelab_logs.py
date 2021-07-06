#!/usr/bin/env python3

from collections import namedtuple
import csv
import datetime
import os
from pathlib import Path
import sys
from typing import Union
import warnings

LOGDIR = '/home/pi/.local/share/Bluelab/Connect/logs'

GrowData = namedtuple('GrowData', ['timestamp', 'ec', 'ph', 'temp'])

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
    if not isinstance(csv_file, Path):
        csv_file = Path(csv_file)
    data = []
    with open(csv_file) as f:
        reader = csv.reader(f)
        # ['2021-07-06 11:36:00', 'EC', 'C', '0.0', '7.3', '20']
        for i, row in enumerate(reader):
            if i == 0:
                continue
            if i == 1:
                assert row[1] == 'EC', f"Incorrect EC unit: {row[1]}"
                assert row[2] == 'C', f"Incorrect temp unit: {row[2]}"
            timestamp = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') 
            try:
                ec = float(row[3])
            except ValueError:
                warnings.warn(f"Invalid EC value: {row[3]}")
                ec = -9999
            try:
                ph = float(row[4])
            except ValueError:
                warnings.warn(f"Invalid pH value: {row[4]}")
                ph = -9999
            try:
                temp = float(row[5])
            except ValueError:
                warnings.warn(f"Invalid temp value: {row[5]}")
                temp = -9999
            d = GrowData(timestamp, ec, ph, temp)
            data.append(d)
    return data

def extract_values(last_timestamp: datetime.datetime, poll_interval: int):
    BUFFER = 30
    last_log = get_last_log(LOGDIR)
    data = get_data(last_log)
    values = []
    end = None
    for d in data:
        if d.timestamp <= last_timestamp:
            continue
        values.append(d)
    interval = last_timestamp - d.timestamp
    if interval > datetime.timedelta(seconds=poll_interval + BUFFER):
        raise RuntimeError(f"Last value is outside expected range: {last_timestamp}:{d.timestamp}-{interval}")
    ec = sum([d.ec for d in data])/len(data)
    ph = sum([d.ph for d in data])/len(data)
    temp = sum([d.temp for d in data])/len(data)
    return [ec, ph, temp]


poll_interval = 10 * 60
last_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=poll_interval)
print(extract_values(last_timestamp, poll_interval))


