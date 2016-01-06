#!/usr/bin/python3

from sqlite3_RBU import *
import time
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import os
import random

class instr_info:
    """Information on instrument entry in DB"""
    def __init__(self, rid, nm, ds, dn, sn):
        self.rid = rid
        self.name = nm
        self.descrip = ds
        self.dev_name = dn
        self.sn = sn

class readout_info:
    """Information on readout entry in DB, with most recent values"""
    def __init__(self, rid, nm, ds, un, iid):
        self.rid = rid
        self.name = nm
        self.descrip = ds
        self.units = un
        self.instrument_id = iid
       
        self.time = None
        self.val = None
         
class DB_Reader:
    """Base class for reading DB file"""
    def __init__(self, dbname, conn = None):
            """Initialize with name of database to open; defaults to read-only if conn not supplied"""
            self.dbname = dbname
            self.conn = conn if conn is not None else sqlite3.connect("file:%s?mode=ro"%dbname, uri=True)
            self.curs = self.conn.cursor()
    
    def get_inst_type(self, name):
        """Get instrument identifier by name"""
        self.curs.execute("SELECT rowid,name,descrip,dev_name,serial FROM instrument_types WHERE name = ?", (name,))
        r = self.curs.fetchall()
        return instr_info(*r[0]) if len(r) == 1 else None
    
    def get_readout_id(self, name, inst_name = None):
        """Get identifier for readout by name and optional instrument name"""
        if inst_name is None:
            self.curs.execute("SELECT rowid FROM readout_types WHERE name = ?", (name,))
        else:
            self.curs.execute("SELECT readout_types.rowid FROM readout_types JOIN instrument_types ON instrument_id = instrument_types.rowid WHERE readout_types.name = ? AND instrument_types.name = ?", (name, inst_name))
        r = self.curs.fetchall()
        return r[0][0] if len(r) == 1 else None
    
    def get_readout_info(self, rid):
        """Get readout information by rowid"""
        self.curs.execute("SELECT rowid,name,descrip,units,instrument_id FROM readout_types WHERE rowid = ?", (rid,))
        r = self.curs.fetchall()
        return readout_info(*r[0]) if len(r) == 1 else None
    
class DB_Logger(DB_Reader, RBU_cloner):
    """Base class for writing data log"""

    def __init__(self, dbname, conn = None):
        """Initialize with name of database to open"""
        DB_Reader.__init__(self, dbname, conn if conn is not None else sqlite3.connect(dbname))
        RBU_cloner.__init__(self, self.conn.cursor())
        
        self.instruments = {}   # cache of instrument information
        self.readouts = {}      # cache of readout information
        self.filters = {}       # data reduction filters per channel
        
        os.system("mkdir -p RBU_Data/")
        self.rbu_outname = "RBU_Data/"+dbname.split(".")[0]+"_rbu_%i.db"
        self.t_prev_update = 0          # timestamp of last update
        self.update_timeout = 60        # timeout [s] to push new updates to remote
        
    def __del__(self):
        """Close DB connection on deletion"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            
    def create_instrument(self, nm, descrip, devnm, sn, overwrite = False):
        """Assure instrument entry exists, creating/updating as needed"""
        self.curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO instrument_types(name,descrip,dev_name,serial) VALUES (?,?,?,?)", (nm,descrip,devnm,sn))
        inst = self.get_inst_type(nm)
        self.instruments[inst.rid] = inst
        
    def create_readout(self, name, inst_name, descrip, units, overwrite = False):
        """Assure a readout exists, creating as necessary; return readout ID"""
        inst = self.get_inst_type(inst_name)
        if inst is None:
            return None
        self.curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO readout_types(name,descrip,units,instrument_id) VALUES (?,?,?,?)", (name,descrip,units,inst.rid))
        self.curs.execute("SELECT rowid FROM readout_types WHERE name = ? AND instrument_id = ?", (name,inst.rid))
        r = self.curs.fetchall()
        rid = r[0][0] if len(r) == 1 else None
        if rid is not None:
            self.readouts[rid] = self.get_readout_info(rid)
        return rid
    
    def log_readout(self, tid, value, t = None):
        """Log reading, using current time for timestamp if not specified"""
        t = time.time() if t is None else t
        
        self.log_readout_hook(tid, value, t)
        if self.filters.get(tid, (lambda a,b,c: True))(tid,t,value):
            self.insert("readings", {"type_id":tid, "time":t, "value":value})
            
        # update latest readout value
        self.readouts[tid].time = t
        self.readouts[tid].val = value
        
    def log_readout_hook(self, tid, value, t):
        """Hook for subclass to check readout values"""
        pass
    
    
    ######################################
    # xmlrpc interface for reading DB info
    
    def get_updates(self):
        """Return filename, if available, of RBU updates info"""
        t = time.time()
        if t > self.t_prev_update + 60:
            self.t_prev_update = t
            self.restart_stuffer()
            return self.rbu_prevName
        else:
            return None

    def get_newest(self):
        """Return newest readings for xmlrpc interface"""
        rdout = {}
        for rid in self.readouts:
            rdout[str(rid)] = self.readouts[rid]
        return rdout
    
    def get_readout(self, i):
        """Get readout fpr xmlrpc interface"""
        return self.readouts.get(i,None)
    
    def get_instrument(self, i):
        """Get instrument for xmlrpc interface"""
        return self.instruments.get(i,None)
    
    def get_datapoints(self, rid, t0, t1):
        """Get datapoints for specified readout ID in time stamp range"""
        self.servcurs.execute("SELECT time,value FROM readings WHERE type_id = ? AND time >= ? AND time <= ? ORDER BY time LIMIT 2000", (int(rid), t0, t1))
        return self.servcurs.fetchall()
    
    def get_channel_info(self, rid):
        """Get information on one channel"""
        if rid not in self.readouts:
            return None
        
    
    def launch_dataserver(self):
        # server thread interface to DB
        self.servconn = sqlite3.connect("file:%s?mode=ro"%self.dbname, uri=True)
        self.servcurs = self.servconn.cursor()
        
        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(("localhost", 8000), requestHandler=RequestHandler, allow_none=True)
        #server.register_introspection_functions()
        server.register_function(D.get_updates, 'update')
        server.register_function(D.get_newest, 'newest')
        server.register_function(D.get_datapoints, 'datapoints')
        server.register_function(D.get_readout, 'readout')
        server.register_function(D.get_instrument, 'instrument')
        server.serve_forever()
        
    #######################################
    # sockets interface for submitting data TODO
    
    
    
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
                self.DBL.insert("readings", {"type_id":tid, "time":tprev, "value":vprev})
                self.prev_saved = (tprev,vprev)
                
        # comparison to previously saved point
        vjump |= abs(v - self.prev_saved[1]) >= self.dv or abs(t - self.prev_saved[0]) >= self.dt
        if vjump:
            self.prev_saved = (t,v)
        return vjump











if __name__=="__main__":
    # database file
    if not os.path.exists("test.db"):
        os.system("sqlite3 test.db < base_DB_description.txt")
    
    
    D = DB_Logger("test.db")
    # set up instruments, readouts
    D.create_instrument("funcgen", "test function generator", "ACME Foobar1000", "0001")
    r0 = D.create_readout("5min", "funcgen", "5-minute-period wave", None)
    r1 = D.create_readout("12h", "funcgen", "12-hour-period wave", None)
    D.create_instrument("PMT_HV", "simulated PMT HV source", "ACME Foobar4000", "e27182")
    Vchans = []
    Ichans = []
    for i in range(32):
        Vchans.append(D.create_readout("V_%i"%i, "PMT_HV", "Simulated HV channel voltage", "V"))
        Ichans.append(D.create_readout("I_%i"%i, "PMT_HV", "Simulated HV channel current", "mA"))
        D.filters[Vchans[-1]] = ChangeFilter(D, 80, 60, False)
        D.filters[Ichans[-1]] = ChangeFilter(D, 0.2, 60, False)
    D.conn.commit()
    # set up data filters
    D.filters[r0] = ChangeFilter(D, 0.2, 30)
    D.filters[r1] = DecimationFilter(30)
    # start RBU duplication thread
    D.restart_stuffer()
    
    # run server
    serverthread =  threading.Thread(target = D.launch_dataserver)
    serverthread.start()
    
    # generate test signals
    from math import *
    t0 = 0
    while 1:
        t = time.time()
        v0 = sin(2*pi*t/300)
        v1 = sin(2*pi*t/(12*3600))
        D.log_readout(r0, v0, t)
        D.log_readout(r1, v1, t)
        for i in range(32):
            D.log_readout(Vchans[i], random.gauss(1500, 20), t)
            D.log_readout(Ichans[i], random.gauss(0.85, 0.05), t)
        D.conn.commit()
        time.sleep(1)
    