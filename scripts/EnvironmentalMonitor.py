#!/usr/bin/python3
## \file EnvironmentalMonitor.py Log from environmental sensors

from sensor_defs import *
from SystemLauncher import *
import traceback
from optparse import OptionParser
import ssl

parser = OptionParser()
parser.add_option("--host", default=log_DB_host, help="XMLRPC logger interface hostname")
parser.add_option("--port", default=log_xmlrpc_writeport, type=int, help="XMLRPC logger interface port")
parser.add_option("--gps",      action="store_true", help="log GPS readings")
parser.add_option("--cpu",      action="store_true", help="log computer stats")
parser.add_option("--bmp3xx",   action="store_true", help="log BMP3xx temperature/pressure readings")
parser.add_option("--pm",       action="store_true", help="log particulate matter readings")
options, args = parser.parse_args()

# request for remote server requiring SSH tunnel?
if log_DB_host == "localhost" and options.host != log_DB_host:
    tunnel_back(options.host, options.port)
    options.host = "localhost"

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile = 'https_cert.pem') # validation of server credentials
context.load_cert_chain('https_cert.pem', 'https_key.pem') # my certs for auth to server

xmlrpc_url = 'https://%s:%i'%(options.host, options.port)
print("Connecting to", xmlrpc_url)

with xmlrpc.client.ServerProxy(xmlrpc_url, allow_none=True, context=context) as DBL:
    monitor_group = DBL.create_readgroup("EnvironmentalMonitoring.py", "Environmental sensors readout")
    DBL.log_message(monitor_group, "Starting environmental monitor.")

    if options.bmp3xx: bmp3xx = BMP3xxMonitor(DBL)
    if options.gps: gpsm = GPSMonitor(DBL)
    if options.cpu: cpum = CPUMonitor(DBL)
    if options.pm:  pm25 = PMSA300IMonitor(DBL)
    print("Dataset identifiers initialized.")

use_i2c = options.bmp3xx or options.pm

def read_sensors(i):
    DBL = xmlrpc.client.ServerProxy(xmlrpc_url, allow_none=True, context=context)

    if use_i2c:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
        if options.bmp3xx and bmp3xx.read(i2c): bmp3xx.write(DBL)
        if not i%6 and options.pm and pm25.read(i2c): pm25.write(DBL)

    if not i%6:
        if options.gps and gpsm.read(): gpsm.write(DBL)
        if options.cpu and cpum.read(): cpum.write(DBL)

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

