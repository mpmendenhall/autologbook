#!/usr/bin/python3
## \file LogDB_XMLRPD_server.py XMLRPC server interface to Autologbook DB

from logger_DB_interface import *
import time
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import os
from optparse import OptionParser
import threading
import pickle
import zlib

class DB_Logger:
    """Base class for writing data log"""

    def __init__(self, dbname):
        """Initialize with name of database to open"""
        self.dbname = dbname

        self.instr_idx = {}     # instruments name -> rowid index
        self.readouts = {}      # cache of readout information
        self.filters = {}       # data reduction filters per channel
        self.readsets = []      # pre-defined sets of readouts for negotiating bulk transfers


    #######################
    # read server functions

    def get_readgroups(self):
        """Get complete list of readout groups (id, name, descrip)"""
        self.read_curs.execute("SELECT readgroup_id,name,descrip FROM readout_groups")
        return self.curs.fetchall()

    def get_readtypes(self, rgroup=None):
        """Get list of readout types (id, name, descrip, units[, readgroup_id]) for all or group"""
        if rgroup is None: self.curs.execute("SELECT readout_id,name,descrip,units,readgroup_id FROM readout_types")
        else: self.curs.execute("SELECT readout_id,name,descrip,units FROM readout_types WHERE readgroup_id = ?", (rgroup,))
        return self.curs.fetchall()

    def get_datapoints(self, rid, t0, t1, nmax = 200):
        """Get datapoints for specified readout ID in time stamp range"""
        self.read_curs.execute("SELECT COUNT(*) FROM readings WHERE readout_id = ? AND time >= ? AND time <= ?", (int(rid), t0, t1))
        if self.read_curs.fetchone()[0] > nmax:
            self.read_curs.execute("SELECT avg(time),avg(value) FROM readings WHERE readout_id = ? AND time >= ? AND time <= ? GROUP BY round(time/?) ORDER BY time DESC", (int(rid), t0, t1, (t1-t0)/nmax));
        else:
            self.read_curs.execute("SELECT time,value FROM readings WHERE readout_id = ? AND time >= ? AND time <= ? ORDER BY time DESC", (int(rid), t0, t1))
        return self.read_curs.fetchall()

    def get_datapoints_compressed(self, rid, t0, t1, nmax = 200):
        """Get datapoints as compressed cPickle"""
        dp = self.get_datapoints(rid, t0, t1, nmax)
        return zlib.compress(pickle.dumps(dp))

    def get_newest(self, ilist):
        """Return newest (id,time,value) for each list item"""
        rs = []
        for i in ilist:
            self.curs.execute("SELECT readout_id,time,value FROM readings WHERE readout_id = ? ORDER BY time DESC LIMIT 1", (i,))
            rs.append(self.curs.fetchone())
        return rs

    def get_messages(self, t0, t1, nmax=100, srcid=None):
        """Get messages in time range, (time, srcid, message)"""
        if not (nmax < 10000): nmax = 10000
        if srcid is None:
            self.read_curs.execute("SELECT time,src,msg FROM textlog WHERE time >= ? AND time <= ? ORDER BY time DESC LIMIT ?", (t0, t1, nmax))
        else:
            self.read_curs.execute("SELECT time,src,msg FROM textlog WHERE time >= ? AND time <= ? AND src=? ORDER BY time DESC LIMIT ?", (t0, t1, srcid, nmax))
        return self.read_curs.fetchall()

    def launch_dataserver(self):
        """Launch server providing database read access"""
        # server thread interface to DB
        self.read_conn = sqlite3.connect("file:%s?mode=ro"%self.dbname, timeout=30, uri=True)
        self.read_curs = self.read_conn.cursor()

        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(("localhost", self.readport), requestHandler=RequestHandler, allow_none=True)
        #server.register_introspection_functions()
        server.register_function(self.get_newest,     'newest')
        server.register_function(self.get_readgroups, 'readgroups')
        server.register_function(self.get_readtypes,  'readtypes')
        server.register_function(self.get_datapoints, 'datapoints')
        server.register_function(self.get_datapoints_compressed, 'datapoints_compressed')
        #server.register_function(self.get_readout,    'readout_info')
        server.register_function(self.get_instrument, 'instrument')
        server.register_function(self.get_messages,   'messages')

        server.serve_forever()

    ########################
    # write server functions

    def insert(self, tname, valdict, cols = None):
        """Generate and execute an insert command"""
        icmd, vals = make_insert_command(tname, valdict, cols)
        self.write_curs.execute(icmd, vals)

    def create_readgroup(self, nm, descrip, overwrite = False):
        """Assure instrument entry exists, creating/updating as needed"""
        self.write_curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO readout_groups(name,descrip) VALUES (?,?)", (nm,descrip))
        inst = get_readrgoup(self.write_curs, nm)
        self.instruments[inst.rid] = inst
        self.instr_idx[inst.name] = inst.rid
        return inst.rid

    def create_readout(self, name, group_name, descrip, units, overwrite = False):
        """Assure a readout exists, creating as necessary; return readout ID"""
        inst = get_readrgoup(self.write_curs, group_name)
        if inst is None: return None

        self.write_curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO readout_types(name,descrip,units,readgroup_id) VALUES (?,?,?,?)", (name,descrip,units,inst.rid))
        self.write_curs.execute("SELECT rowid FROM readout_types WHERE name = ? AND readgroup_id = ?", (name,inst.rid))
        r = self.write_curs.fetchall()
        rid = r[0][0] if len(r) == 1 else None
        if rid is not None: self.readouts[rid] = get_readout_info(self.write_curs, rid)
        return rid

    def log_readout(self, tid, value, t = None):
        """Log reading, using current time for timestamp if not specified"""
        assert(tid in self.readouts)

        t = time.time() if t is None else t

        self.log_readout_hook(tid, value, t)
        if self.filters.get(tid, (lambda a,b,c: True))(tid,t,value):
            self.insert("readings", {"readout_id":tid, "time":t, "value":value})

        # update latest readout value
        self.readouts[tid].time = t
        self.readouts[tid].val = value

    def log_readset(self, rsid, tvs):
        """log readouts [t,v,t,v...] in predefined readset (simplified data transfer)"""
        for (n,tid) in enumerate(self.readsets[rsid]):
            self.log_readout(tid, tvs[2*n+1], tvs[2*n])

    def log_readout_hook(self, tid, value, t):
        """Hook for subclass to check readout values"""
        pass

    def log_message(self, src, msg, t = None):
        """Log a textual message, using current time for timestamp if not specified"""
        t = time.time() if t is None else t
        self.insert("textlog", {"src":src, "time":t, "msg":msg})

    def set_ChangeFilter(self, iid, dv, dt, extrema = True):
        """Set "change" data reduction filter on readout"""
        self.filters[iid] = ChangeFilter(self, dv, dt, extrema)

    def set_DecimationFilter(self, iid, nth):
        """Set data decimation filter on readout"""
        self.filters[iid] = DecimationFilter(nth)

    def define_readset(self, rs):
        """Return index for pre-defined read set, creating new as needed"""
        try: return self.readsets.index(rs)
        except:
            self.readsets.append(rs)
            return len(self.readsets)-1

    def launch_writeserver(self):
        """Launch server providing database read access"""
        # server thread interface to DB
        self.writeconn = sqlite3.connect(self.dbname, timeout = 30)
        self.write_curs = self.writeconn.cursor()
        self.log_message("DB_Logger.py", "Starting Logger write server.")

        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(("localhost", self.writeport), requestHandler=RequestHandler, allow_none=True)
        server.register_function(self.create_readgroup, 'create_readgroup')
        server.register_function(self.create_readout, 'create_readout')
        server.register_function(self.set_ChangeFilter, 'set_ChangeFilter')
        server.register_function(self.set_DecimationFilter, 'set_DecimationFilter')
        server.register_function(self.log_readout, 'log_readout')
        server.register_function(self.log_message, 'log_message')
        server.register_function(self.writeconn.commit, 'commit')
        server.register_function(self.define_readset, 'define_readset')
        server.register_function(self.log_readset, 'log_readset')
        server.serve_forever()


########################
# data reduction filters

class DecimationFilter:
    """Data filter to keep every n'th point"""
    def __init__(self, nth):
            self.nth = nth
            self.n = 0
    def __call__(self, tid, t, v):
        recordable = not self.n
        self.n = (self.n+1)%self.nth
        return recordable

class ChangeFilter:
    """Filter to record points capturing data changes"""
    def __init__(self, DBL, dv, dt, extrema = True):
        self.DBL = DBL
        self.dv = dv
        self.dt = dt
        self.extrema = extrema
        self.prev_saved = None

    def __call__(self, tid, t, v):
        if not self.prev_saved:
            self.prev_saved = (t,v)
            return True

        # comparison to immediately preceding point
        vold = self.prev_saved[1]
        tprev = self.DBL.readouts[tid].time
        vprev = self.DBL.readouts[tid].val
        vjump = abs(v - vprev) >= self.dv
        keep_prev = vjump or abs(t - self.prev_saved[0]) >= self.dt
        if self.extrema:
            keep_prev |= ((vold <= vprev >= v) or (vold >= vprev <= v)) and not (vold == vprev == v)
        if keep_prev:
            if not self.prev_saved == (tprev,vprev):
                self.DBL.insert("readings", {"readout_id":tid, "time":tprev, "value":vprev})
                self.prev_saved = (tprev,vprev)

        # comparison to previously saved point
        vjump |= abs(v - self.prev_saved[1]) >= self.dv or abs(t - self.prev_saved[0]) >= self.dt
        if vjump:
            self.prev_saved = (t,v)
        return vjump


if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("--readport", dest="readport",    type="int", default = 0, help="Localhost port for read access")
    parser.add_option("--writeport",dest="writeport",   type="int", default = 0, help="Localhost port for read/write access")
    parser.add_option("--db",       dest="db",          help="path to database")
    options, args = parser.parse_args()

    D = DB_Logger(options.db)
    D.readport = options.readport
    D.writeport = options.writeport

    threads = []

    # run read server
    if options.readport: threads.append(threading.Thread(target = D.launch_dataserver))

    # run write server
    if options.writeport: threads.append(threading.Thread(target = D.launch_writeserver))

    print("Launching", len(threads), "DB logger threads")
    for t in threads: t.start()
    for t in threads: t.join()
    print("LogDB server done.")
