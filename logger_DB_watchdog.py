#!/usr/bin/python3
## \file logger_DB_watchdog.py Create watchdog file from log messages

from optparse import OptionParser
import xmlrpc.client
import time

def doit():
    parser = OptionParser()
    parser.add_option("--server",      help="XMLRPC server")

    t0 = time.time()
    print("Last updated",time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(t0)))
    options, args = parser.parse_args()

    try:
        s = xmlrpc.client.ServerProxy(options.server, allow_none=True)
        groups = {x[0]: (x[1],x[2]) for x in s.readgroups()}
        messages = s.messages(t0 - 48*3600, t0 + 1e7, 2000)
        if not messages:
            print("ERROR no log messages produced in previous 48 hours.")
        for m in messages:
            M = m[-1].upper()
            if "ERROR" in M or "WARNING" in M: print(m)
    except:
        print("ERROR Unable to contact logger XMLRPC server", options.server)
        return

if __name__=="__main__": doit()
