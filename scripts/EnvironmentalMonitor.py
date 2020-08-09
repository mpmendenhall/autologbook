#!/usr/bin/python3

from AutologbookConfig import *
import xmlrpc.client
import traceback

import time
import board
import busio
import adafruit_bmp3xx
from gps import *

def h2P(h): return 1013.25 * (1 - 2.25577e-5 * h)**5.25588
def P2h(P): return (1 - (P/1013.25)**(1./5.25588))/2.25577e-5
h = 160
P0 = h2P(h)

with xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host, log_xmlrpc_writeport), allow_none=True) as DBL:
    monitor_group = DBL.create_readgroup("EnvironmentalMonitoring.py", "Environmental sensors readout")
    DBL.log_message(monitor_group, "Starting environmental monitor.")

    bmp3xx_group = DBL.create_readgroup("BMP388", "BMP388 pressure/temperature sensor")
    bmp3xx_T = DBL.create_readout("T", "BMP388", "ambient temperature", "deg. C")
    bmp3xx_P = DBL.create_readout("P", "BMP388", "ambient pressure", "mbar")

    gps_group = DBL.create_readgroup("GPS", "Global Positioning System receiver")
    gps_lat = DBL.create_readout("lat", "GPS", "Latitude", "degrees N")
    gps_lon = DBL.create_readout("lon", "GPS", "Longitude", "degrees E")
    gps_alt = DBL.create_readout("alt", "GPS", "Altitude", "m")

def read_sensors(i):
    DBL = xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host, log_xmlrpc_writeport), allow_none=True)
    i2c = busio.I2C(board.SCL, board.SDA)

    t = time.time()

    bmp3xx = adafruit_bmp3xx.BMP3XX_I2C(i2c)
    bmp3xx.pressure_oversampling = 32
    bmp3xx.temperature_oversampling = 32
    T = bmp3xx.temperature
    P = bmp3xx.pressure
    DBL.log_readout(bmp3xx_T, T, t)
    DBL.log_readout(bmp3xx_P, P, t)

    if not i%6:
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

        report = gpsd.next()
        retries = 6
        while report['class'] != 'TPV' and retries:
            print(report['class'])
            report = gpsd.next()
            retries -= 1

        if report['class'] == 'TPV':
            tstr = getattr(report,'time',None)

            lat = getattr(report,'lat', None)
            if lat is not None: DBL.log_readout(gps_lat, lat, t)
            lon = getattr(report,'lon', None)
            if lon is not None: DBL.log_readout(gps_lon, lon, t)
            alt = getattr(report,'alt', None)
            if alt is not None: DBL.log_readout(gps_alt, alt, t)
            print(tstr,lat,lon,alt)

            #
            #print  getattr(report,'epv','nan'),"\t",
            #print  getattr(report,'ept','nan'),"\t",
            #print  getattr(report,'speed','nan'),"\t",
            #print getattr(report,'climb','nan'),"\t"

    DBL.commit()

ii = 0
while True:
    print("\nEnvironmental sensors readout", ii);
    try:
        read_sensors(ii)
        ii += 1
    except:
        ii = 0
        traceback.print_exc()
    time.sleep(10)
