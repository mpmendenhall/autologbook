#!/usr/bin/python3
## \file LogDB_XMLRPD_server.py XMLRPC server interface to Autologbook DB

from logger_DB_interface import *
import time
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import os
import sys
from optparse import OptionParser
import threading
import pickle
import zlib
import ssl
import socket
import traceback

######################
######################
class DB_Logger_Reader:
    """Base class for reading data log"""

    def __init__(self, dbname, host, readport):
        """Initialize with name of database to open"""
        self.host = host
        self.readport = readport
        self.dbname = dbname
        self.readsets = []      # pre-defined sets of readouts for negotiating bulk transfers


    #######################
    # read server functions

    def get_readtypes(self, rgroup = None):
        """Get list of readout types (id, name, descrip, units) for all or group"""
        if rgroup is None: self.read_curs.execute("SELECT readout_id,name,descrip,units FROM readout_types")
        else: self.read_curs.execute('SELECT readout_id,name,descrip,units FROM readout_types WHERE name LIKE ? || "/%"', (rgroup,))
        return self.read_curs.fetchall()

    def get_readout_info(self, rid):
        """Get (name, descrip, units) on one readout"""
        ri = get_readout_info(self.read_curs, rid)
        return (ri.name, ri.descrip, ri.units) if ri is not None else None

    def get_datapoints(self, rid, t0, t1, nmax = 300):
        """Get datapoints for specified readout ID in time stamp range"""
        self.read_curs.execute("SELECT COUNT(*) FROM readings WHERE readout_id = ? AND time >= ? AND time <= ?", (int(rid), t0, t1))
        if self.read_curs.fetchone()[0] > nmax:
            self.read_curs.execute("SELECT avg(time),avg(value) FROM readings WHERE readout_id = ? AND time >= ? AND time <= ? GROUP BY round(time/?) ORDER BY time DESC", (int(rid), t0, t1, (t1-t0)/nmax));
        else:
            self.read_curs.execute("SELECT time,value FROM readings WHERE readout_id = ? AND time >= ? AND time <= ? ORDER BY time DESC", (int(rid), t0, t1))
        return self.read_curs.fetchall()

    def get_datapoints_compressed(self, rid, t0, t1, nmax = 300):
        """Get datapoints as compressed cPickle"""
        dp = self.get_datapoints(rid, t0, t1, nmax)
        return zlib.compress(pickle.dumps(dp))

    def get_newest(self, ilist):
        """Return newest (id,time,value) for each list item"""
        rs = []
        for i in ilist:
            self.read_curs.execute("SELECT readout_id,time,value FROM readings WHERE readout_id = ? ORDER BY time DESC LIMIT 1", (i,))
            res = self.read_curs.fetchone()
            if res is not None: rs.append(tuple(res))
        return rs

    def get_messages(self, t0, t1, nmax=100, srcid=None):
        """Get messages in time range, (time, srcid, message)"""
        if not (nmax < 10000): nmax = 10000
        if srcid is None:
            self.read_curs.execute("SELECT time,readout_id,msg FROM textlog WHERE time >= ? AND time <= ? ORDER BY time DESC LIMIT ?", (t0, t1, nmax))
        else:
            self.read_curs.execute("SELECT time,readout_id,msg FROM textlog WHERE time >= ? AND time <= ? AND readout_id=? ORDER BY time DESC LIMIT ?", (t0, t1, srcid, nmax))
        return self.read_curs.fetchall()

    def launch_dataserver(self):
        """Launch server providing database read access"""
        # server thread interface to DB
        self.read_conn = sqlite3.connect("file:%s?mode=ro"%self.dbname, timeout=30, uri=True)
        self.read_curs = self.read_conn.cursor()

        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(('', self.readport), requestHandler=RequestHandler, allow_none=True)
        #server.register_introspection_functions()
        server.register_function(self.get_newest,     'newest')
        server.register_function(self.get_readtypes,  'readtypes')
        server.register_function(self.get_datapoints, 'datapoints')
        server.register_function(self.get_datapoints_compressed, 'datapoints_compressed')
        server.register_function(self.get_readout_info, 'readout_info')
        server.register_function(self.get_messages,     'messages')

        print("Launching readserver on", self.host, self.readport)
        sys.stdout.flush()
        server.serve_forever()

    def try_launch_dataserver(self):
        while True:
            try: self.launch_dataserver()
            except:
                traceback.print_exc()
                sys.stdout.flush()
                time.sleep(10)


######################
######################
class DB_Logger_Writer:
    """Base class for writing data log"""

    def __init__(self, dbname, host, writeport):
        """Initialize with name of database to open"""
        self.dbname = dbname
        self.host = host
        self.writeport = writeport
        self.readouts = {}      # cache of readout information
        self.filters = {}       # data reduction filters per channel
        self.readsets = []      # pre-defined sets of readouts for negotiating bulk transfers

    def insert(self, tname, valdict, cols = None):
        """Generate and execute an insert command"""
        icmd, vals = make_insert_command(tname, valdict, cols)
        self.write_curs.execute(icmd, vals)

    def create_readout(self, name, descrip, units, overwrite = False):
        """Assure a readout exists, creating as necessary; return readout ID"""

        if overwrite:
            self.write_curs.execute("SELECT readout_id FROM readout_types WHERE name = ?", (name,))
            r = self.write_curs.fetchall()
            if len(r) == 1:
                self.write_curs.execute("UPDATE readout_types SET descrip=?,units=? WHERE readout_id = ?", (descrip, units, r[0][0]))
            else:
                self.write_curs.execute("INSERT INTO readout_types(name,descrip,units) VALUES (?,?,?)", (name,descrip,units))
        else:
            self.write_curs.execute("INSERT OR IGNORE INTO readout_types(name,descrip,units) VALUES (?,?,?)", (name,descrip,units))

        self.write_curs.execute("SELECT readout_id FROM readout_types WHERE name = ?", (name,))
        r = self.write_curs.fetchall()
        rid = r[0][0] if len(r) == 1 else None
        if rid is not None: self.readouts[rid] = get_readout_info(self.write_curs, rid)
        return rid

    def log_readout(self, rid, value, t = None):
        """Log reading, using current time for timestamp if not specified"""
        if rid not in self.readouts:
            self.readouts[rid] = get_readout_info(self.write_curs, rid)
        assert(self.readouts[rid] is not None)

        t = time.time() if t is None else t

        self.log_readout_hook(rid, value, t)
        if self.filters.get(rid, (lambda a,b,c: True))(rid,t,value):
            self.insert("readings", {"readout_id":rid, "time":t, "value":value})

        # update latest readout value
        self.readouts[rid].time = t
        self.readouts[rid].val = value

    def log_readouts(self, rs):
        """Log list of [(rid, val, [t]), ...]"""
        for r in rs: self.log_readout(*r)
        if len(rs): self.writeconn.commit()

    def log_readset(self, rsid, tvs):
        """log readouts [t,v,t,v...] in predefined readset (simplified data transfer)"""
        for (n,rid) in enumerate(self.readsets[rsid]):
            self.log_readout(rid, tvs[2*n+1], tvs[2*n])

    def log_readout_hook(self, tid, value, t):
        """Hook for subclass to check readout values"""
        pass

    def log_message(self, srcid, msg, t = None):
        """Log a textual message, using current time for timestamp if not specified"""
        t = time.time() if t is None else t
        self.insert("textlog", {"readout_id":srcid, "time":t, "msg":msg})

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
        self.log_message(self.create_readout("LogDB_XMLRPC_server.py", "Autologbook DB web interface server", None),
                         "Starting Logger write server on " + self.host + ":%i"%self.writeport)

        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        server = SimpleXMLRPCServer(None, bind_and_activate=False, requestHandler=RequestHandler, allow_none=True)
        server.register_function(self.create_readout, 'create_readout')
        server.register_function(self.set_ChangeFilter, 'set_ChangeFilter')
        server.register_function(self.set_DecimationFilter, 'set_DecimationFilter')
        server.register_function(self.log_readout, 'log_readout')
        server.register_function(self.log_readouts, 'log_readouts')
        server.register_function(self.log_message, 'log_message')
        server.register_function(self.writeconn.commit, 'commit')
        server.register_function(self.define_readset, 'define_readset')
        server.register_function(self.log_readset, 'log_readset')

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH) #, cafile = 'https_cert.pem') # accepted certs from clients
        #context.verify_mode = ssl.CERT_REQUIRED
        #context.check_hostname = False
        context.load_cert_chain('https_cert.pem', 'https_key.pem') # my certs for clients

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            sock.bind(('', self.writeport)) # listen on all interfaces
            sock.listen(40) # 20 pending connections before dropping more

            with context.wrap_socket(sock, server_side=True) as ssock:
                server.socket = ssock
                print("Launching writeserver on", self.host, self.writeport)
                sys.stdout.flush()
                server.serve_forever()

    def try_launch_writeserver(self):
        while True:
            try: self.launch_writeserver()
            except:
                traceback.print_exc()
                sys.stdout.flush()
                time.sleep(10)

########################
# data reduction

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


############################
############################
############################

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("--readport", dest="readport",    type="int", default = 0, help="Localhost port for read access")
    parser.add_option("--writeport",dest="writeport",   type="int", default = 0, help="Localhost port for read/write access")
    parser.add_option("--db",       dest="db",          help="path to database")
    options, args = parser.parse_args()

    threads = []
    fqdn = socket.getfqdn()

    # run read server
    if options.readport:
        Dr = DB_Logger_Reader(options.db, fqdn, options.readport)
        threads.append(threading.Thread(target = Dr.try_launch_dataserver))

    # run write server
    if options.writeport:
        Dw = DB_Logger_Writer(options.db, fqdn, options.writeport)
        threads.append(threading.Thread(target = Dw.try_launch_writeserver))

    for t in threads: t.start()

    nalive = len(threads)
    while nalive:
        nalive = 0
        for t in threads:
            if t.is_alive(): nalive += 1
            else: t.join()
        time.sleep(5)

    print("LogDB server done.")
