#!/usr/bin/python3
## \file logger_DB_watchdog.py Print watchdog alerts from log messages

from optparse import OptionParser
import xmlrpc.client
import time

class LogDB_Watchdog:
    def __init__(self):
        self.s = None

    def setup_parser(self):
        parser = OptionParser()
        parser.add_option("--server",   help="XMLRPC server")
        parser.add_option("--cfg",      help="alarm configuration file")
        parser.add_option("--lastlog",  type=float, help="Require a log message within past [n] minutes")
        parser.add_option("--snooze",   action="store_true", help="Skip checking server")
        parser.add_option("--verbose",  action="store_true", help="extra verbosity")
        return parser

    def check_lastlog(self, lastlog):
        """Check whether recent logbook messages have been posted"""
        if lastlog is not None and not self.s.messages(self.t0 - 60*options.lastlog, self.t0 + 1e7, 1):
            print("ERROR no log messages produced in previous %g minutes."%lastlog)

    def check_messages(self):
        """Check for errors in logbook messages"""
        for m in self.s.messages(self.t0 - 6*3600, self.t0 + 1e7, 200):
            M = m[-1].upper()
            if "ERROR" in M or "WARNING" in M: print(m)

    def check_readings(self, cfgname):
        """Check readings against ranges in config file"""
        # config file: [id] [min] [max] [timeout]

        cfg = []
        if cfgname:
            cfg = [l.split() for l in open(cfgname, "r").readlines() if l[0] != '#']
            cfg = [(int(c[0]), float(c[1]), float(c[2]), float(c[3])) for c in cfg if len(c)==4]

        def dname(i):
            ri = self.s.readout_info(cid)
            return self.groups[ri['readgroup_id']][0]+"::"+ri['name']

        d = dict([(i[0],i[1:]) for i in self.s.newest([c[0] for c in cfg]) if i is not None])
        for cid,mn,mx,dt in cfg:
            if cid not in d:
                print("ERROR missing entry for log DB id", cid)
                continue

            t,v = d[cid]
            if self.verbose: print(dname(cid), "=", v, time.strftime('on %a, %d %b %Y %H:%M:%S', time.localtime(t)))
            if t < self.t0 - dt:
                print("ERROR last update for '%s' was %.1f minutes ago."%(dname(cid), (self.t0-t)/60.))
                continue
            if not (mn <= v and v <= mx):
                print("ERROR '%s' = %g outside range %g -- %g on"%(dname(cid), v, mn, mx), time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(t)))
                continue


    def run(self):

        options, args = self.setup_parser().parse_args()
        self.verbose = options.verbose

        self.t0 = time.time()
        print("Last updated", time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime(self.t0)))
        if options.snooze:
            print("Watchdog is snoozing.")
            return

        try:
            self.s = xmlrpc.client.ServerProxy(options.server, allow_none=True)
            self.groups = {x[0]: (x[1],x[2]) for x in self.s.readgroups()}
        except:
            print("ERROR Unable to contact logger XMLRPC server", options.server)
            return

        self.check_lastlog(options.lastlog)
        self.check_readings(options.cfg)

if __name__=="__main__":
    LogDB_Watchdog().run()
