#!/usr/bin/python3
## \file TestFunctionGen.py Submit test reading points to logging DB

from AutologbookConfig import *
import xmlrpc.client
from math import *
import time
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--host",  dest="host",    default = log_xmlrpc_host, help="Hostname for logger server read/write")
parser.add_option("--port",  dest="port",    type="int", default = log_xmlrpc_writeport, help="Port for logger server read/write")
options, args = parser.parse_args()

DBL = xmlrpc.client.ServerProxy('http://%s:%i'%(options.host, options.port), allow_none=True)
myGrp = DBL.create_readgroup("TestFunctionGen.py", "Test log event generator")
DBL.log_message(myGrp, "Starting function generator.")
DBL.commit()

# set up channels and filters
DBL.create_readgroup("funcgen", "ACME Foobar1000 function generator")
r0 = DBL.create_readout("5min", "funcgen", "5-minute-period wave", "bogons")
r1 = DBL.create_readout("12h", "funcgen", "12-hour-period wave", None)
DBL.set_ChangeFilter(r0, 0.2, 30)
DBL.set_DecimationFilter(r1, 20)
DBL.commit()

try:
    while 1:
        t = time.time()
        DBL.log_readout(r0, sin(2*pi*t/300), t)
        DBL.log_readout(r1, sin(2*pi*t/(3600*12)), t)
        DBL.commit()
        time.sleep(1)
except:
    DBL.log_message(myGrp, "stopping function generator.")
    DBL.commit()
