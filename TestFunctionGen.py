#!/usr/bin/python3

import xmlrpc.client
from math import *
import time

DBL = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
DBL.log_message("TestFunctionGen.py", "Starting function generator.")

# set up channels and filters
DBL.create_instrument("funcgen", "test function generator", "ACME Foobar1000", "0001")
r0 = DBL.create_readout("5min", "funcgen", "5-minute-period wave", None)
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
    DBL.log_message("TestFunctionGen.py", "stopping function generator.")
    DBL.commit()
    