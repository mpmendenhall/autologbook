#!/usr/bin/python3
## \file EnvironmentalMonitor.py Log from environmental sensors

from SystemLauncher import *
import xmlrpc.client
import sensor_defs
from sensor_defs import SensorItem, computer
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
        smons.append(bmp3xx.BMP3xxMonitor(DBL, options.bmp3xx))
    if options.dps310:
        from sensor_defs import dps310
        smons.append(dps310.DPS310Monitor(DBL, options.dps310))
    if options.bme680:
        from sensor_defs import bme680
        smons.append(bme680.BME680Monitor(DBL, options.bme680))
    if options.shtc3:
        from sensor_defs import shtc3
        smons.append(shtc3.SHTC3Monitor(DBL, options.shtc3))
    if options.pm:
        from sensor_defs import pm25
        smons.append(pm25.PMSA300IMonitor(DBL, options.pm))
    if options.as726x:
        from sensor_defs import as726x
        smons.append(as726x.AS726xMonitor(DBL, options.as726x))
    if options.as7341:
        from sensor_defs import as7341
        smons.append(as7341.AS7341Monitor(DBL, options.as7341))

    if options.gps:
        from sensor_defs import gpsmon
        smons.append(gpsmon.GPSMonitor(DBL, options.gps))
    if options.cpu:
        smons.append(computer.CPUMonitor(DBL, options.cpu))
    if options.chrony:
        smons.append(computer.ChronyMonitor(DBL, options.chrony))

    print("Dataset identifiers initialized.")
    return smons

class SensLogger(SensorItem):
    def __init__(self, options):
        SensorItem.__init__(self)
        self.options = options
        self.readouts = []
        self.DBL = None

    def log_readout(self, rid, val, t):
        self.readouts.append((rid,val,t))

    def read(self, SIO):
        """Send data to logger"""
        if not self.readouts: return

        print("\n**** Uploading", len(self.readouts), "readout datapoints. ****\n")
        if self.DBL is None: self.DBL = get_DBL(self.options)
        try:
            self.DBL.log_readouts(self.readouts)
            self.readouts = []
        except:
            traceback.print_exc()
            self.DBL = None

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--host",     default=log_DB_host, help="XMLRPC logger interface hostname")
    parser.add_option("--port",     default=log_xmlrpc_writeport, type=int, help="XMLRPC logger interface port; 0 for local test")
    parser.add_option("--gps",      type=float, help="log GPS readings")
    parser.add_option("--cpu",      type=float, help="log computer stats")
    parser.add_option("--chrony",   type=float, help="log chronyc tracking")
    parser.add_option("--bmp3xx",   type=float, help="log BMP3xx temperature/pressure readings")
    parser.add_option("--dps310",   type=float, help="log DPS310 temperature/pressure readings")
    parser.add_option("--bme680",   type=float, help="log BME680 environmental readings")
    parser.add_option("--shtc3",    type=float, help="log SHTC3 temperature/humidity readings")
    parser.add_option("--as726x",   type=float, help="log AS726x color spectrum readings")
    parser.add_option("--as7341",   type=float, help="log AS7341 multispectral sensor readings")
    parser.add_option("--pm",       type=float, help="log particulate matter readings")
    parser.add_option("--dt",       type=float, default = 30, help="data upload interval (s)")
    options, args = parser.parse_args()

    ss = init_sensors(options)
    if not ss:
        print("Zero sensors enabled.")
        exit(0)

    SQ = PriorityQueue()
    SIO = SensLogger(options)
    SIO.tnext = time.time() + 1
    SIO.dt = options.dt

    for s in ss:
        s.tnext = SIO.tnext + options.dt/10.
        SQ.put(s)

    SQ.put(SIO)

    while True:
        # wait for next readout event time
        tnow = time.time()
        s = SQ.get()
        dtnext = s.tnext - tnow
        if dtnext > 0:
            print("------ Waiting %.2f s until"%dtnext, time.ctime(s.tnext), " ------\n");
            time.sleep(dtnext)
            tnow = s.tnext
        else:
            # spread readouts apart on collision
            db = 0.1*options.dt/SQ.qsize()
            print("** Late by", -dtnext, "s; bumping next read by", db, "s **\n")
            tnow += db

        s.tnext = None
        try: s.read(SIO)
        except: traceback.print_exc()
        if s.tnext is None: s.tnext = tnow + s.dt
        s.tnext = max(s.tnext, time.time() + 1)
        SQ.put(s)
