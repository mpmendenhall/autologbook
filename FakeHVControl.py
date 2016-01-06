#!/usr/bin/python3

import xmlrpc.client
from math import *
import time
import random

DBL = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
DBL.log_message("FakeHVControl.py", "Starting fake HV.")

# determine channels list
DBLread = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
Vchans = {}
Ichans = {}
for c in DBLread.instrument_readouts("PMT_HV"):
    nm = c["name"]
    if nm[:2] == "I_":
        Ichans[int(nm[2:])] = c["rid"]
    if nm[:2] == "V_":
        Vchans[int(nm[2:])] = c["rid"]
DBLread = None

try:   
    while 1:
        t = time.time()
        for i in range(32):
            DBL.log_readout(Vchans[i], random.gauss(1500, 20), t)
            DBL.log_readout(Ichans[i], random.gauss(0.85, 0.05), t)
        DBL.commit()
        time.sleep(1)
except:
    DBL.log_message("FakeHVControl.py", "Stopping fake HV.")
    DBL.commit()
    