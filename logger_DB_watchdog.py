#!/usr/bin/python3
## \file logger_DB_watchdog.py Print watchdog alerts from log messages

from optparse import OptionParser
import xmlrpc.client
import time

def doit():
    parser = OptionParser()
    parser.add_option("--server",   help="XMLRPC server")
    parser.add_option("--cfg",      help="alarm configuration file")
    parser.add_option("--snooze",   action="store_true", help="Skip checking server")
    parser.add_option("--verbose",  action="store_true", help="extra verbosity")

    t0 = time.time()
    print("Last updated", time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(t0)))
    options, args = parser.parse_args()
    if options.snooze:
        print("Watchdog is snoozing.")
        return

    # config file: [id] [min] [max] [timeout]
    cfg = []
    if options.cfg:
        cfg = [l.split() for l in open(options.cfg,"r").readlines() if l[0] != '#']
        cfg = [(int(c[0]), float(c[1]), float(c[2]), float(c[3])) for c in cfg if len(c)==4]

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

    def dname(i):
        ri = s.readout_info(cid)
        return groups[ri['readgroup_id']][0]+"::"+ri['name']

    d = dict([(i[0],i[1:]) for i in s.newest([c[0] for c in cfg]) if i is not None])
    for cid,mn,mx,dt in cfg:
        if cid not in d:
            print("ERROR missing entry for log DB id", cid)
            continue

        t,v = d[cid]
        if options.verbose: print(dname(cid), "=", v, time.strftime('on %a, %d %b %Y %H:%M:%S', time.localtime(t)))
        if t < t0 - dt:
            print("ERROR last update for '%s' was %.1f minutes ago."%(dname(cid), (t0-t)/60.))
            continue
        if not (mn <= v and v <= mx):
            print("ERROR '%s' = %g outside range %g -- %g on"%(dname(cid), v, mn, mx), time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(t)))
            continue

if __name__=="__main__": doit()
