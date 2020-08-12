#!/usr/bin/python3
## \file sensor_defs.py Helper classes for sensor readout/logging

import xmlrpc.client
import time
import board
import busio
import adafruit_bmp3xx
import adafruit_pm25
from gps import *
import platform
import subprocess

class BMP3xxMonitor:
    def h2P(h): return 1013.25 * (1 - 2.25577e-5 * h)**5.25588
    def P2h(P): return (1 - (P/1013.25)**(1./5.25588))/2.25577e-5

    def __init__(self, DBL):
        self.g_id = DBL.create_readgroup("BMP388", "BMP388 pressure/temperature sensor")
        self.T_id = DBL.create_readout("T", "BMP388", "ambient temperature", "deg. C")
        self.P_id = DBL.create_readout("P", "BMP388", "ambient pressure", "mbar")
        self.P = self.T = self.t = None

    def read(self, i2c):
        bmp3xx = adafruit_bmp3xx.BMP3XX_I2C(i2c)
        bmp3xx.pressure_oversampling = 32
        bmp3xx.temperature_oversampling = 32
        self.T = bmp3xx.temperature
        self.P = bmp3xx.pressure
        self.t = time.time()
        print("BMP3xx", self.t, self.T, "C,\t", self.P, "mbar")
        return True

    def write(self, DBL):
        DBL.log_readout(self.T_id, self.T, self.t)
        DBL.log_readout(self.P_id, self.P, self.t)

class PMSA300IMonitor:
    def __init__(self, DBL):
        self.g_id = DBL.create_readgroup("PMSA300I", "PMSA300I particulate matter monitor")
        self.PM003_id = DBL.create_readout("PM0.3", "PMSA300I", "Particles > 0.3um / 0.1L air", "n/dl")
        self.PM005_id = DBL.create_readout("PM0.5", "PMSA300I", "Particles > 0.5um / 0.1L air", "n/dl")
        self.PM010_id = DBL.create_readout("PM1",  "PMSA300I", "Particles > 1.0um / 0.1L air", "n/dl")
        self.PM025_id = DBL.create_readout("PM2.5","PMSA300I", "Particles > 2.5um / 0.1L air", "n/dl")
        self.PM050_id = DBL.create_readout("PM5",  "PMSA300I", "Particles > 5.0um / 0.1L air", "n/dl")
        self.PM100_id = DBL.create_readout("PM10", "PMSA300I", "Particles > 10um / 0.1L air",  "n/dl")
        self.PME10_id = DBL.create_readout("PM1.0e", "PMSA300I", "Estimated PM1.5 mass density",  "μg/m^3")
        self.PME25_id = DBL.create_readout("PM2.5e", "PMSA300I", "Estimated PM2.5 mass density",  "μg/m^3")
        self.PME100_id = DBL.create_readout("PM10e", "PMSA300I", "Estimated PM10 mass density",   "μg/m^3")

    def read(self, i2c):
        #from digitalio import DigitalInOut, Direction, Pull
        # If you have a GPIO, its not a bad idea to connect it to the RESET pin
        # reset_pin = DigitalInOut(board.G0)
        # reset_pin.direction = Direction.OUTPUT
        # reset_pin.value = False

        reset_pin = None
        pm25 = adafruit_pm25.PM25_I2C(i2c, reset_pin)
        self.t = time.time()
        try: self.aqdata = pm25.read()
        except: self.aqdata = None
        print(self.aqdata)
        return self.aqdata is not None

    def write(self, DBL):
        if not self.aqdata: return
        self.t = time.time()

        DBL.log_readout(self.PM003_id, self.aqdata["particles 03um"], self.t)
        DBL.log_readout(self.PM005_id, self.aqdata["particles 05um"], self.t)
        DBL.log_readout(self.PM010_id, self.aqdata["particles 10um"], self.t)
        DBL.log_readout(self.PM025_id, self.aqdata["particles 25um"], self.t)
        DBL.log_readout(self.PM050_id, self.aqdata["particles 50um"], self.t)
        DBL.log_readout(self.PM100_id, self.aqdata["particles 100um"], self.t)

        DBL.log_readout(self.PME10_id,  self.aqdata["pm10 env"],  self.t)
        DBL.log_readout(self.PME25_id,  self.aqdata["pm25 env"],  self.t)
        DBL.log_readout(self.PME100_id, self.aqdata["pm100 env"], self.t)

class GPSMonitor:
    def __init__(self, DBL):
        self.g_id = DBL.create_readgroup("GPS", "Global Positioning System receiver")
        self.lat_id = DBL.create_readout("lat", "GPS", "Latitude", "degrees N")
        self.lon_id = DBL.create_readout("lon", "GPS", "Longitude", "degrees E")
        self.alt_id = DBL.create_readout("alt", "GPS", "Altitude", "m")
        self.lat = self.lon = self.alt = self.t = None

    def read(self):
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
        report = gpsd.next()
        retries = 6
        while report['class'] != 'TPV' and retries:
            #print(report['class'])
            report = gpsd.next()
            retries -= 1
        if report['class'] != 'TPV': return False

        tstr = getattr(report,'time',None)
        self.lat = getattr(report,'lat', None)
        self.lon = getattr(report,'lon', None)
        self.alt = getattr(report,'alt', None)
        self.t = time.time()
        print("GPS", self.t, tstr, self.lat, "N, ", self.lon, "E, ", self.alt, "m")
        return True

                #print  getattr(report,'epv','nan'),"\t",
            #print  getattr(report,'ept','nan'),"\t",
            #print  getattr(report,'speed','nan'),"\t",
            #print getattr(report,'climb','nan'),"\t"


    def write(self, DBL):
        if self.lat is not None: DBL.log_readout(self.lat_id, self.lat, self.t)
        if self.lon is not None: DBL.log_readout(self.lon_id, self.lon, self.t)
        if self.alt is not None: DBL.log_readout(self.alt_id, self.alt, self.t)

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

    def read(self):
        self.t = time.time()
        if self.has_tgpu: self.Tgpu = float(subprocess.check_output(["vcgencmd","measure_temp"]).decode()[5:9])
        self.Tcpu = float(open("/sys/class/thermal/thermal_zone0/temp",'r').read())/1000.
        print("CPU", self.Tcpu, self.Tgpu)
        return True

    def write(self, DBL):
        DBL.log_readout(self.Tcpu_id,    self.Tcpu, self.t)
        if self.Tgpu is not None: DBL.log_readout(self.Tgpu_id, self.Tgpu, self.t)
