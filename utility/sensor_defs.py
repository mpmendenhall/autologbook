#!/usr/bin/python3
## \file sensor_defs.py Helper classes for sensor readout/logging

import xmlrpc.client
import time
import board
import busio
import adafruit_bmp3xx
from gps import *

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
