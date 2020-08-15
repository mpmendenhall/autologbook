#!/usr/bin/python3
## \file EnvironmentalMonitor.py Log from environmental sensors

from SystemLauncher import *
import xmlrpc.client
import sensor_defs
from sensor_defs import SensorItem
import time
import traceback
from optparse import OptionParser
import ssl
from Null_LogDB import *
from queue import PriorityQueue

def get_DBL(options):
    """Get DB Logger connection"""
    if not options.port: return Null_LogDB()
    xmlrpc_url = 'https://%s:%i'%(options.host, options.port)
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile = 'https_cert.pem') # validation of server credentials
    context.load_cert_chain('https_cert.pem', 'https_key.pem') # my certs for auth to server
    return xmlrpc.client.ServerProxy(xmlrpc_url, allow_none=True, context=context)

def init_sensors(options):
    """Initialize sensors to read"""

    DBL = get_DBL(options)
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
    if options.as726x:
        from sensor_defs import as726x
        smons.append(as726x.AS726xMonitor(DBL))

    if options.gps:
        from sensor_defs import gpsmon
        smons.append(gpsmon.GPSMonitor(DBL))
    if options.cpu:
        smons.append(sensor_defs.CPUMonitor(DBL))

    print("Dataset identifiers initialized.")
    return smons

class SensLogger(SensorItem):
    def __init__(self, options):
        SensorItem.__init__(self)
        self.options = options
        self.readouts = []

    def log_readout(self, rid, val, t):
        self.readouts.append((rid,val,t))

    def read(self, SIO):
        """Send data to logger"""
        if not self.readouts: return

        print("\n**** Uploading", len(self.readouts), "readout datapoints. ****\n")
        DBL = get_DBL(self.options)
        DBL.log_readouts(self.readouts)
        self.readouts = []

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--host",     default=log_DB_host, help="XMLRPC logger interface hostname")
    parser.add_option("--port",     default=log_xmlrpc_writeport, type=int, help="XMLRPC logger interface port; 0 for local test")
    parser.add_option("--gps",      action="store_true", help="log GPS readings")
    parser.add_option("--cpu",      action="store_true", help="log computer stats")
    parser.add_option("--bmp3xx",   action="store_true", help="log BMP3xx temperature/pressure readings")
    parser.add_option("--shtc3",    action="store_true", help="log SHTC3 temperature/humidity readings")
    parser.add_option("--as726x",   action="store_true", help="log AS726x color spectrum readings")
    parser.add_option("--pm",       action="store_true", help="log particulate matter readings")
    parser.add_option("--dt",       type=float, default= 10, help="minimum wait between readouts (s)")
    options, args = parser.parse_args()

    SIO = SensLogger(options)
    SIO.tnext = time.time()
    SIO.dt = options.dt/2.

    SQ = PriorityQueue()
    SQ.put(SIO)
    for s in init_sensors(options):
        s.dt = options.dt
        s.tnext = SIO.tnext - 1
        SQ.put(s)

    while True:
        tnow = time.time()
        s = SQ.get()
        dtnext = s.tnext - tnow
        if dtnext > 0:
            print("------ Waiting", dtnext, "s from", time.asctime(), " ------\n");
            time.sleep(dtnext)
            tnow = s.tnext

        try: s.read(SIO)
        except: traceback.print_exc()
        s.tnext = tnow + s.dt
        SQ.put(s)
