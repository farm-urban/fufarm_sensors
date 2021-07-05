#!/usr/bin/env python3

import csv
import datetime
import os

logdir = '/home/pi/.local/share/Bluelab/Connect/logs'
csv_files = [x for x in os.listdir(logdir) if x.endswith('.csv')]

def time_tuple(s):
    x = s.strip('.csv').split()
    return (datetime.datetime.strptime(x[0], '%Y-%m-%d').date(), int(x[1]))

latest = sorted(csv_files, key=time_tuple)[-1]
with open(latest) as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)


