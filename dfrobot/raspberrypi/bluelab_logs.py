#!/usr/bin/env python3

from collections import namedtuple
import csv
import datetime
import os
from pathlib import Path
import sys
from typing import Union, Optional
import warnings

LOGDIR = '/home/pi/.local/share/Bluelab/Connect/logs'
GrowData = namedtuple('GrowData', ['tag', 'timestamp', 'ec', 'ph', 'temp'])

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
    """
With one system:
Time (Europe/London),Conductivity unit,Temperature unit,52rf Conductivity,52rf pH,52rf Temperature
2021-07-04 15:33:00,EC,C,---,7.7,---

With two systems:
Time (Europe/London),Conductivity unit,Temperature unit,52rf Conductivity,52rf pH,52rf Temperature, run time, run time, run time,4q3f Conductivity,4q3f pH,4q3f Temperature, run time, run time, run time
2021-07-11 18:23:00,EC,C,1.3,8.2,21,0.0,0.0,0.0,1.3,8.1,21,0.0,0.0,0.0
    """
    if not isinstance(csv_file, Path):
        csv_file = Path(csv_file)
    data = []
    systems = []
    with open(csv_file) as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                ncol = len(row)
                # ncol 6 is monitor 1
                # ncol 9 is monitor 2 and control 1
                # ncol 15 is control 2
                print("NROWS IS ",len(row))
                tag1 = row[3].split()[0]
                systems.append(tag1)
                if len(row) == 6:
                    pass # 1 system
                elif len(row) == 15:
                    tag2 = row[9].split()[0]
                    systems.append(tag2)
                else:
                    raise RuntimeError("Unrecognised csv format - too many systems?")
                continue
            if i == 1:
                assert row[1] == 'EC', f"Incorrect EC unit: {row[1]}"
                assert row[2] == 'C', f"Incorrect temp unit: {row[2]}"
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

            if len(systems) == 2:
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

            d1 = GrowData(tag1, timestamp, ec1, ph1, temp1)
            if len(systems) == 1:
                data.append([d1])
            elif len(systems) == 2:
                d2 = GrowData(tag2, timestamp, ec2, ph2, temp2)
                data.append([d1, d2])
    return data

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


if __name__ == "__main__":
    #poll_interval = 50000 * 60
    #last_timestamp = datetime.datetime.now() - datetime.timedelta(seconds=poll_interval)
    #print(sample_bluelab_data(last_timestamp, poll_interval))

#    poll_interval = 1
#    target_timestamp = datetime.datetime(2021, 7, 6, 11, 38)
#    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
#    last_log = "bluelab_logs/monitor_one.csv"
#    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
#    assert x[0].timestamp == target_timestamp


    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 7, 6, 11, 38)
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    last_log = "bluelab_logs/control_two.csv"
    last_log = "bluelab_logs/monitor_two.csv"
    last_log = "bluelab_logs/control_one.csv"
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp

