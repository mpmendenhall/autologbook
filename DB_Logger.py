#!/usr/bin/python3

from sqlite3_RBU import *
import time
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import os

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
         

class DB_Logger(RBU_cloner):
    """Base class for writing data log"""
    
    def __init__(self, dbname):
        """Initialize with name of database to open"""
        RBU_cloner.__init__(self)
        self.dbname = dbname
        self.instruments = {}   # cache of instrument information, by rowid index
        self.instr_idx = {}     # instruments name -> rowid index
        self.readouts = {}      # cache of readout information
        self.filters = {}       # data reduction filters per channel
        
        os.system("mkdir -p RBU_Data/")
        self.rbu_outname = "RBU_Data/"+dbname.split(".")[0]+"_rbu_%i.db"
        self.t_prev_update = 0          # timestamp of last update
        self.update_timeout = 60        # timeout [s] to push new updates to remote
    
    #######################
    # read server functions
    
    @staticmethod
    def get_inst_type(curs, name):
        """Get instrument identifier by name"""
        curs.execute("SELECT rowid,name,descrip,dev_name,serial FROM instrument_types WHERE name = ?", (name,))
        r = curs.fetchall()
        return instr_info(*r[0]) if len(r) == 1 else None
    
    @staticmethod
    def get_readout_id(curs, name, inst_name = None):
        """Get identifier for readout by name and optional instrument name"""
        if inst_name is None:
            curs.execute("SELECT rowid FROM readout_types WHERE name = ?", (name,))
        else:
            curs.execute("SELECT readout_types.rowid FROM readout_types JOIN instrument_types ON instrument_id = instrument_types.rowid WHERE readout_types.name = ? AND instrument_types.name = ?", (name, inst_name))
        r = curs.fetchall()
        return r[0][0] if len(r) == 1 else None
    
    @staticmethod
    def get_readout_info(curs, rid):
        """Get readout information by rowid"""
        curs.execute("SELECT rowid,name,descrip,units,instrument_id FROM readout_types WHERE rowid = ?", (rid,))
        r = curs.fetchall()
        return readout_info(*r[0]) if len(r) == 1 else None
        
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
        return list(self.readouts.values())
    
    def get_readout(self, i):
        """Get one newest readout for xmlrpc interface"""
        return self.readouts.get(i,None)
    
    def get_instrument(self, i):
        """Get instrument for xmlrpc interface"""
        return self.instruments.get(i, None)
    
    def get_instrument_readouts(self, instrname):
        """Get all newest readouts for one instrument"""
        if instrname not in self.instr_idx:
            return None
        self.servcurs.execute("SELECT rowid FROM readout_types WHERE instrument_id = ?", (self.instr_idx[instrname],))
        return [self.readouts[r[0]] for r in self.servcurs.fetchall()]
    
    def get_datapoints(self, rid, t0, t1):
        """Get datapoints for specified readout ID in time stamp range"""
        self.servcurs.execute("SELECT time,value FROM readings WHERE type_id = ? AND time >= ? AND time <= ? ORDER BY time LIMIT 2000", (int(rid), t0, t1))
        return self.servcurs.fetchall()
    
    def get_messages(self, t0, t1):
        """Get messages in time range"""
        self.servcurs.execute("SELECT time,src,msg FROM textlog WHERE time >= ? AND time <= ? ORDER BY time DESC LIMIT 100", (t0, t1))
        return self.servcurs.fetchall()
    
    def launch_dataserver(self):
        """Launch server providing database read access"""
        # server thread interface to DB
        self.servconn = sqlite3.connect("file:%s?mode=ro"%self.dbname, uri=True)
        self.servcurs = self.servconn.cursor()
        
        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(("localhost", 8000), requestHandler=RequestHandler, allow_none=True)
        #server.register_introspection_functions()
        #server.register_function(self.get_updates, 'update')
        server.register_function(self.get_newest, 'newest')
        server.register_function(self.get_instrument_readouts, 'instrument_readouts')
        server.register_function(self.get_datapoints, 'datapoints')
        server.register_function(self.get_readout, 'readout')
        server.register_function(self.get_instrument, 'instrument')
        server.register_function(self.get_messages, 'messages')
        server.serve_forever()
        
 
    ########################
    # write server functions
    
    def create_instrument(self, curs, nm, descrip, devnm, sn, overwrite = False):
        """Assure instrument entry exists, creating/updating as needed"""
        curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO instrument_types(name,descrip,dev_name,serial) VALUES (?,?,?,?)", (nm,descrip,devnm,sn))
        inst = self.get_inst_type(curs,nm)
        self.instruments[inst.rid] = inst
        self.instr_idx[inst.name] = inst.rid
        return inst.rid
    
    def ws_create_instrument(self, nm, descrip, devnm, sn, overwrite = False):
        """Write server version of create_instrument"""
        return self.create_instrument(self.rbu_curs, nm, descrip, devnm, sn, overwrite)
    
    def create_readout(self, curs, name, inst_name, descrip, units, overwrite = False):
        """Assure a readout exists, creating as necessary; return readout ID"""
        inst = self.get_inst_type(curs, inst_name)
        if inst is None:
            return None
        curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO readout_types(name,descrip,units,instrument_id) VALUES (?,?,?,?)", (name,descrip,units,inst.rid))
        curs.execute("SELECT rowid FROM readout_types WHERE name = ? AND instrument_id = ?", (name,inst.rid))
        r = curs.fetchall()
        rid = r[0][0] if len(r) == 1 else None
        if rid is not None:
            self.readouts[rid] = self.get_readout_info(curs,rid)
        return rid
    
    def ws_create_readout(self, name, inst_name, descrip, units, overwrite = False):
        """Write server version of create_readout"""
        return self.create_readout(self.rbu_curs, name, inst_name, descrip, units, overwrite)
    
    def log_readout(self, tid, value, t = None):
        """Log reading, using current time for timestamp if not specified"""        
        assert(tid in self.readouts)

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
    
    def log_message(self, src, msg, t = None):
        """Log a textual message, using current time for timestamp if not specified"""
        t = time.time() if t is None else t
        self.insert("textlog", {"src":src, "time":t, "msg":msg})
    
    def commit_writes(self):
        self.rbu_conn.commit()
    
    def set_ChangeFilter(self, iid, dv, dt, extrema = True):
        """Set "change" data reduction filter on readout"""
        self.filters[iid] = ChangeFilter(self, dv, dt, extrema)
        
    def set_DecimationFilter(self, iid, nth):
        """Set data decimation filter on readout"""
        self.filters[iid] = DecimationFilter(nth)
        
    def launch_writeserver(self):
        """Launch server providing database read access"""
        # server thread interface to DB
        self.writeconn = sqlite3.connect(self.dbname)
        self.rbu_curs = self.writeconn.cursor()
        self.log_message("DB_Logger.py", "Starting Logger write server.")
        
        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(("localhost", 8002), requestHandler=RequestHandler, allow_none=True)
        server.register_function(self.ws_create_instrument, 'create_instrument')
        server.register_function(self.ws_create_readout, 'create_readout')
        server.register_function(self.set_ChangeFilter, 'set_ChangeFilter')
        server.register_function(self.set_DecimationFilter, 'set_DecimationFilter')
        server.register_function(self.log_readout, 'log_readout')
        server.register_function(self.log_message, 'log_message')
        server.register_function(self.writeconn.commit, 'commit')
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
                self.DBL.insert("readings", {"type_id":tid, "time":tprev, "value":vprev})
                self.prev_saved = (tprev,vprev)
                
        # comparison to previously saved point
        vjump |= abs(v - self.prev_saved[1]) >= self.dv or abs(t - self.prev_saved[0]) >= self.dt
        if vjump:
            self.prev_saved = (t,v)
        return vjump


if __name__=="__main__":
    # database file
    dbname = "test.db"
    if not os.path.exists(dbname):
        os.system("sqlite3 %s < base_DB_description.txt"%dbname)

    D = DB_Logger(dbname)

    # start RBU duplication thread
    D.restart_stuffer()
    
    # run read server
    serverthread = threading.Thread(target = D.launch_dataserver)
    serverthread.start()
    
    # run write server
    writethread = threading.Thread(target = D.launch_writeserver)
    writethread.start()
    