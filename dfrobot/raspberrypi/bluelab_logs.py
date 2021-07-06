#!/usr/bin/env python3

import csv
import datetime
import os
from pathlib import Path
import sys
from typing import Union

LOGDIR = '/home/pi/.local/share/Bluelab/Connect/logs'

def last_log(logdir: Union[str, Path]):

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
        logdir = Path(csv_file)
    data = []
    with open(latest) as f:
        reader = csv.reader(f)
        # ['2021-07-06 11:36:00', 'EC', 'C', '0.0', '7.3', '20']
        for i, row in enumerate(reader):
            if i == 0:
                continue
            if i == 1:
                assert row[1] == 'EC', f"Incorrect EC unit: {row[1]}"
                assert row[2] == 'C', f"Incorrect temp unit: {row[2]}"
            row[0] = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') 
            row[3] = float(row[3])
            row[4] = float(row[4])
            row[5] = float(row[5])
            data.append(row)
    return data

latest = last_log(LOGDIR)
data = get_data(latest)
print(data)
