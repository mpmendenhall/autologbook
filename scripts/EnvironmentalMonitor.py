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
options, args = parser.parse_args()

# request for remote server requiring SSH tunnel?
if log_DB_host == "localhost" and options.host != log_DB_host:
    tunnel_back(options.host, options.port)
    options.host = "localhost"

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile = 'https_cert.pem') # accepted certs from clients
context.load_cert_chain('https_cert.pem', 'https_key.pem') # my certs

#context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#context.load_cert_chain('https_cert.pem', 'https_key.pem') # my certs
#context.load_verify_locations('https_cert.pem') # verify server certs

xmlrpc_url = 'https://%s:%i'%(options.host, options.port)
print("Connecting to", xmlrpc_url)

with xmlrpc.client.ServerProxy(xmlrpc_url, allow_none=True, context=context) as DBL:
    monitor_group = DBL.create_readgroup("EnvironmentalMonitoring.py", "Environmental sensors readout")
    DBL.log_message(monitor_group, "Starting environmental monitor.")

    bmp3xx = BMP3xxMonitor(DBL)
    gpsm = GPSMonitor(DBL)
    print("Dataset identifiers initialized.")

def read_sensors(i):
    DBL = xmlrpc.client.ServerProxy(xmlrpc_url, allow_none=True, context=context)

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

