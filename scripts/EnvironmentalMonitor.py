#!/usr/bin/python3
## \file EnvironmentalMonitor.py Log from environmental sensors

from SystemLauncher import *
import xmlrpc.client
import sensor_defs
import time
import traceback
from optparse import OptionParser
import ssl
from Null_LogDB import *

parser = OptionParser()
parser.add_option("--host",     default=log_DB_host, help="XMLRPC logger interface hostname")
parser.add_option("--port",     default=log_xmlrpc_writeport, type=int, help="XMLRPC logger interface port")
parser.add_option("--gps",      action="store_true", help="log GPS readings")
parser.add_option("--cpu",      action="store_true", help="log computer stats")
parser.add_option("--bmp3xx",   action="store_true", help="log BMP3xx temperature/pressure readings")
parser.add_option("--shtc3",    action="store_true", help="log SHTC3 temperature/humidity readings")
parser.add_option("--pm",       action="store_true", help="log particulate matter readings")
parser.add_option("--dt",       type=float, default= 10, help="minimum wait between readouts (s)")
options, args = parser.parse_args()

def get_DBL():
    if not options.port: return Null_LogDB()
    xmlrpc_url = 'https://%s:%i'%(options.host, options.port)
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile = 'https_cert.pem') # validation of server credentials
    context.load_cert_chain('https_cert.pem', 'https_key.pem') # my certs for auth to server
    return xmlrpc.client.ServerProxy(xmlrpc_url, allow_none=True, context=context)

use_i2c = False

def init_sensors():
    #with get_DBL() as DBL:
        DBL = get_DBL()
        monitor_group = DBL.create_readgroup(thishost + ":EnvironmentalMonitoring.py", "Environmental sensors readout on "+thishost)
        DBL.log_message(monitor_group, "Starting environmental monitor on " + thishost +".")

        smons = []

        if options.bmp3xx:
            from sensor_defs import bmp3xx
            smons.append(bmp3xx.BMP3xxMonitor(DBL))
        if options.shtc3:
            from sensor_defs import shtc3
            smons.append(shtc3.SHTC3Monitor(DBL))
        if options.pm:
            from sensor_defs import pm25
            smons.append(pm25.PMSA300IMonitor(DBL))

        if options.gps:
            from sensor_defs import gpsmon
            smons.append(gpsmon.GPSMonitor(DBL))
        if options.cpu:
            smons.append(sensor_defs.CPUMonitor(DBL))

        print("Dataset identifiers initialized.")

        global use_i2c
        use_i2c = len([None for s in smons if hasattr(s,'i2c')])

        return smons


def read_sensors(smons):
    SIO = sensor_defs.SensorIO()
    SIO.DBL = get_DBL()
    if use_i2c: SIO.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
    for s in smons:
        try: s.read(SIO)
        except: traceback.print_exc()
    SIO.DBL.commit()

smons = init_sensors()
if use_i2c:
    import board
    import busio
while True:
    print("\n------ Sensors readout", time.asctime(), " ------\n");
    try: read_sensors(smons)
    except:
        traceback.print_exc()
        time.sleep(30)
    print("\n----- waiting", options.dt, "s from", time.asctime(), " ------\n");
    time.sleep(options.dt)
