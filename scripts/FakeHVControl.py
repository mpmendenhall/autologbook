#!/usr/bin/python3

import xmlrpc.client
from math import *
import time
import random
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--port",  dest="port",    action="store", type="int", default = 8003, help="Localhost port for logger server read/write")
options, args = parser.parse_args()

DBL = xmlrpc.client.ServerProxy('http://localhost:%i'%options.port, allow_none=True)
DBL.log_message("FakeHVControl.py", "Starting fake HV.")

# set up channels and filters
DBL.create_readgroup("PMT_HV", "ACME Foobar4000 simulated PMT HV source")
Vchans = []
Ichans = []
for i in range(32):
    Vchans.append(DBL.create_readout("V_%i"%i, "PMT_HV", "Simulated HV channel voltage", "V"))
    Ichans.append(DBL.create_readout("I_%i"%i, "PMT_HV", "Simulated HV channel current", "mA"))
    DBL.set_ChangeFilter(Vchans[-1], 80, 60, False)
    DBL.set_ChangeFilter(Ichans[-1], 0.2, 60, False)
DBL.commit()

rset = DBL.define_readset(Vchans + Ichans)

try:
    while 1:
        t = time.time()
        rdata = []
        for i in range(32):
            rdata += [t,random.gauss(1500, 20)]
        for i in range(32):
            rdata += [t,random.gauss(0.85, 0.05)]
        DBL.log_readset(rset,rdata)
        DBL.commit()
        time.sleep(1)
except:
    DBL.log_message("FakeHVControl.py", "Stopping fake HV.")
    DBL.commit()
