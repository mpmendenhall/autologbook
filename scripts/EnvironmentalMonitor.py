#!/usr/bin/python3

from AutologbookConfig import *
import xmlrpc.client
import traceback

import time
import board
import busio
import adafruit_bmp3xx

def h2P(h): return 1013.25 * (1 - 2.25577e-5 * h)**5.25588
def P2h(P): return (1 - (P/1013.25)**(1./5.25588))/2.25577e-5
h = 160
P0 = h2P(h)

with xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host, log_xmlrpc_writeport), allow_none=True) as DBL:
    bmp3xx_group = DBL.create_readgroup("BMP388", "BMP388 pressure/temperature sensor")
    bmp3xx_T = DBL.create_readout("T", "BMP388", "ambient temperature", "deg. C")
    bmp3xx_P = DBL.create_readout("P", "BMP388", "ambient pressure", "mbar")

def read_sensors():
    DBL = xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host, log_xmlrpc_writeport), allow_none=True)
    i2c = busio.I2C(board.SCL, board.SDA)

    bmp3xx = adafruit_bmp3xx.BMP3XX_I2C(i2c)
    bmp3xx.pressure_oversampling = 32
    bmp3xx.temperature_oversampling = 32
    t = time.time()
    T = bmp3xx.temperature
    P = bmp3xx.pressure
    DBL.log_readout(bmp3xx_T, T, t)
    DBL.log_readout(bmp3xx_P, P, t)

    DBL.commit()

while True:
    try: read_sensors()
    except: traceback.print_exc()
    time.sleep(10)
