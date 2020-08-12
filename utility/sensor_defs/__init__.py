#!/usr/bin/python3
## \file sensor_defs.py Helper classes for sensor readout/logging

import time
import platform
import subprocess

__all__ = ["SensorIO", "CPUMonitor", "bmp3xx", "gpsmon", "pm25", "shtc3"]

class SensorIO:
    """Shared resources for sensor monitoring"""
    def __init__(self):
        self.i2c = None
        self.DBL = None

class CPUMonitor:
    """Local system load/health indicators"""
    def __init__(self, DBL):
        self.hostname = platform.node()
        self.g_id = DBL.create_readgroup(self.hostname, "Computer '" + self.hostname + "' status")
        self.Tcpu_id = DBL.create_readout("Tcpu", self.hostname, "CPU temperature", "deg. C")
        self.Tgpu_id = DBL.create_readout("Tgpu", self.hostname, "GPU temperature", "deg. C")

        try:
            subprocess.check_output(["vcgencmd","measure_temp"])
            self.has_tgpu = True
        except:
            self.has_tgpu = False
            self.Tgpu = None

    def read(self, SIO):
        self.t = time.time()
        if self.has_tgpu: self.Tgpu = float(subprocess.check_output(["vcgencmd","measure_temp"]).decode()[5:9])
        self.Tcpu = float(open("/sys/class/thermal/thermal_zone0/temp",'r').read())/1000.
        print("\n", self.hostname, "Tcpu =", self.Tcpu, "C, Tgpu =", self.Tgpu, "C")

        SIO.DBL.log_readout(self.Tcpu_id,    self.Tcpu, self.t)
        if self.Tgpu is not None: SIO.DBL.log_readout(self.Tgpu_id, self.Tgpu, self.t)