#!/usr/bin/python3

import xmlrpc.client
from math import *
import time

DBL = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
DBL.log_message("TestFunctionGen.py", "Starting function generator.")

# determine channels list
DBLread = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
r0 = r1 = None
for c in DBLread.instrument_readouts("funcgen"):
    nm = c["name"]
    if nm == "5min":
        r0 = c["rid"]
    if nm == "12h":
        r1 = c["rid"]
DBLread = None
assert(r0 is not None and r1 is not None)

try: 
    while 1:
        t = time.time()
        DBL.log_readout(r0, sin(2*pi*t/300), t)
        DBL.log_readout(r1, sin(2*pi*t/(3600*12)), t)
        DBL.commit()
        time.sleep(1)
except:
    DBL.log_message("TestFunctionGen.py", "stopping function generator.")
    DBL.commit()
    