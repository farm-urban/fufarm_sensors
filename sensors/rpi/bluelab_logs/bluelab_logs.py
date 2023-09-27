#!/usr/bin/env python3
from collections import namedtuple
from collections.abc import Generator
import csv
import datetime
from enum import Enum
from pathlib import Path
import statistics
from typing import Union, Optional
import warnings

LOGDIR = '/home/pi/.local/share/Bluelab/Connect/logs'
GrowData = namedtuple('GrowData', ['tag', 'timestamp', 'ec', 'ph', 'temp'])

MONITOR = 'monitor'
CONTROL = 'control'

def create_parser(mode: str, system: str):
    """Returns a dynamic function that parses a subset of a row."""
    def parser(timestamp: str, irow: Generator[str]):
        try:
            field = next(irow)
            ec = float(field)
        except ValueError:
            warnings.warn(f"Invalid EC value: {field}")
            ec = None
        try:
            field = next(irow)
            ph = float(field)
        except ValueError:
            warnings.warn(f"Invalid pH value: {field}")
            ph = None
        try:
            field = next(irow)
            temp = float(field)
        except ValueError:
            warnings.warn(f"Invalid temp value: {field}")
            temp = None

        if mode == CONTROL:
            runtime = next(irow)
            runtime = next(irow)
            runtime = next(irow)

        return GrowData(system, timestamp, ec, ph, temp)
    
    return parser

def get_last_log(logdir: Union[str, Path]):

    def time_tuple(p):
        x = p.stem.split()
        return (datetime.datetime.strptime(x[0], '%Y-%m-%d').date(), int(x[1]))

    if not isinstance(logdir, Path):
        logdir = Path(logdir)

    csv_files = [x for x in logdir.iterdir() if (x.is_file() and x.suffix == '.csv')]
    latest = sorted(csv_files, key=time_tuple)[-1]
    return logdir / latest


def parse_header(reader):
    # Reader header to determine mode, get system names and create the pasers
    header = iter(next(reader))

    _timezone = next(header)
    _ecUnit = next(header)
    _tempUnit = next(header)

    system = None
    mode = MONITOR
    parsers = []
    for field in header:
        f1, f2 = field.split()
        if f2.strip() == 'Conductivity':
            # Start of new system block
            if system is None: # First system
                system = f1.strip()
            else:
                parsers.append(create_parser(mode, system))
                system = f1.strip()
                mode = MONITOR
        if f1.strip() == 'run':
            mode = CONTROL
    parsers.append(create_parser(mode, system))  # Add last system
    return parsers


def get_data(csv_file: Union[str, Path]):
    """See bluelab_logs directory for csv files with format
    """
    if not isinstance(csv_file, Path):
        csv_file = Path(csv_file)
    readings = []
    with open(csv_file) as f:
        reader = csv.reader(f)
        parsers = parse_header(reader)
        try:
            for i, row in enumerate(reader):
                irow = iter(row)
                timestamp = datetime.datetime.strptime(next(irow), '%Y-%m-%d %H:%M:%S')
                ecUnit = next(irow)
                assert ecUnit == 'EC', f"Incorrect EC unit: {ecUnit}"
                tempUnit = next(irow)
                assert tempUnit == 'C', f"Incorrect temp unit: {tempUnit}"
                readings.append([p(timestamp, irow) for p in parsers])
        except Exception as e:
            warnings.warn(f"Error parsing Bluelab log file: {e}")
    return readings


def sample_bluelab_data(last_timestamp: datetime.datetime,
                        poll_interval: int,
                        log_dir: Optional[str]=LOGDIR,
                        last_log: Optional[str]=None
                        ):
    BUFFER = 30
    if not last_log:
        last_log = get_last_log(log_dir)
    data = get_data(last_log)
    values = []
    end = None
    nsystems = len(data[0])
    # Collect all samples that are after the last timestamp
    for d in data:
        if d[0].timestamp >= last_timestamp: # ignore any values before we last sampled
            values.append(d)
    if not len(values):
        return None

    interval = last_timestamp - values[-1][0].timestamp
    if interval > datetime.timedelta(seconds=poll_interval + BUFFER):
        raise RuntimeError(f"Last value is outside expected range: {last_timestamp}:{values[-1][0].timestamp} | {interval}")
    
    # Results are averages of all values
    results = []
    if nsystems == 1:
        tag1 = values[-1][0].tag
        timestamp1 = values[-1][0].timestamp
        ec1 = statistics.mean([d[0].ec for d in values if d[0].ec is not None])
        ph1 = statistics.mean([d[0].ph for d in values if d[0].ph is not None])
        temp1 = statistics.mean([d[0].temp for d in values if d[0].temp is not None])
        d1 = GrowData(tag1, timestamp1, ec1, ph1, temp1)
        results.append(d1)

    elif nsystems == 2:
        tag1 = values[-1][0].tag
        timestamp1 = values[-1][0].timestamp
        ec1 = statistics.mean([d[0].ec for d in values if d[0].ec is not None])
        ph1 = statistics.mean([d[0].ph for d in values if d[0].ph is not None])
        temp1 = statistics.mean([d[0].temp for d in values if d[0].temp is not None])
        d1 = GrowData(tag1, timestamp1, ec1, ph1, temp1)
        results.append(d1)

        tag2 = values[-1][1].tag
        timestamp2 = values[-1][1].timestamp
        ec2 = statistics.mean([d[1].ec for d in values if d[1].ec is not None])
        ph2 = statistics.mean([d[1].ph for d in values if d[1].ph is not None])
        temp2 = statistics.mean([d[1].temp for d in values if d[1].temp is not None])
        d2 = GrowData(tag2, timestamp2, ec2, ph2, temp2)
        results.append(d2)
    return results

## Unit tests
def test_control1():
    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 7, 11, 17, 51)
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    last_log = "control1.csv"
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp
    assert x[0].ec == 1.3

def test_monitor2():
    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 8, 2, 7, 57)
    last_log = "monitor2.csv"
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp
    assert x[1].ec == 2.0

def test_control2():
    poll_interval = 1
    target_timestamp = datetime.datetime(2021, 8, 2, 7, 50)
    last_log = "control2.csv"
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp
    assert x[1].ec == 2.0


def test_monitor1control1():
    poll_interval = 1
    target_timestamp = datetime.datetime(2023, 1, 14, 19, 40)
    last_log = "monitor1control1.csv"
    last_timestamp = target_timestamp - datetime.timedelta(seconds=poll_interval)
    x = sample_bluelab_data(last_timestamp, poll_interval, last_log=last_log)
    assert x[0].timestamp == target_timestamp
    assert x[1].ec == 1.3

if __name__ == "__main__":
    test_control1()

