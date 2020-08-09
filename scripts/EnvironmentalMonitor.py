#!/usr/bin/python3
## \file EnvironmentalMonitor.py Log from environmental sensors

from sensor_defs import *
from AutologbookConfig import *
import traceback

with xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host, log_xmlrpc_writeport), allow_none=True) as DBL:
    monitor_group = DBL.create_readgroup("EnvironmentalMonitoring.py", "Environmental sensors readout")
    DBL.log_message(monitor_group, "Starting environmental monitor.")

    bmp3xx = BMP3xxMonitor(DBL)
    gpsm = GPSMonitor(DBL)
    print("Dataset identifiers initialized.")

def read_sensors(i):
    DBL = xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host, log_xmlrpc_writeport), allow_none=True)

    i2c = busio.I2C(board.SCL, board.SDA)
    if bmp3xx.read(i2c): bmp3xx.write(DBL)

    if not i%6:
        if gpsm.read(): gpsm.write(DBL)

    DBL.commit()

ii = 0
while True:
    print("\n---- Environmental sensors readout", ii, "----\n");
    try:
        read_sensors(ii)
        ii += 1
    except:
        ii = 0
        traceback.print_exc()
    time.sleep(10)
