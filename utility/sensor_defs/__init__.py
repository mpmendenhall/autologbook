#!/usr/bin/python3
## \file sensor_defs.py Helper classes for sensor readout/logging

import time

__all__ = ["SensorIO", "AnalogUV", "AQI", "as726x", "bmp3xx", "computer", "gpsmon", "humidity", "pm25", "shtc3", "veml6070"]

class SensorIO:
    """Shared resources for sensor monitoring"""
    def __init__(self):
        self.i2c = None
        self.DBL = None

class SensorItem:
    def __init__(self, dt = 60):
        self.dt = dt             # read repeat frequency
        self.tnext = time.time() # next requested read time

    def __lt__(self, other):
        return self.tnext < other.tnext
