#!/usr/bin/python3
## \file logger_DB_XMLRPC_server.py server to provide logger DB data over http

from logger_DB_interface import *
import threading
import time
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import os
from optparse import OptionParser

class LogServer():
    """Base class for writing data log"""
    
    def __init__(self, dbname, port):
        """Initialize with name of database to open"""
        self.dbname = dbname    # database file
        self.port = port        # server port
        
        self.readgroups = []     # cache of readout groups (id,name,descrip)
        #self.instr_idx = {}     # instruments name -> rowid index
        #self.readouts = {}      # cache of readout information
        #self.readsets = []      # pre-defined sets of readouts for negotiating bulk transfers

    def get_readout_info(self, i):
        """Get description of readout by ID"""
        self.curs.execute("SELECT name,descrip,units,readgroup_id FROM readout_types WHERE readout_id = ?", (i,))
        r = self.curs.fetchone()
        return {"name": r[0], "descrip": r[1], "units":r[2],"readgroup_id":r[3]} if r else r
    
    #def get_instrument_readouts(self, instrname):
    #    """Get all newest readouts for one instrument"""
    #    if instrname not in self.instr_idx:
    #        return None
    #    self.curs.execute("SELECT rowid FROM readout_types WHERE readgroup_id = ?", (self.instr_idx[instrname],))
    #    return [self.readouts[r[0]] for r in self.curs.fetchall()]
    
    def get_datapoints(self, rid, t0, t1):
        """Get datapoints for specified readout ID in time stamp range"""
        self.curs.execute("SELECT time,value FROM readings WHERE readout_id = ? AND time >= ? AND time <= ? ORDER BY time DESC LIMIT 2000", (int(rid), t0, t1))
        return self.curs.fetchall()
    
    def get_readgroups(self):
        """Get complete list of readout groups (id, name, descrip)"""
        #if not self.readgroups:
        self.curs.execute("SELECT readgroup_id,name,descrip FROM readout_groups")
        self.readgroups = self.curs.fetchall()
        return self.readgroups
    
    def get_readtypes(self, rgroup=None):
        """Get list of readout types (id, name, descrip, units[, readgroup_id]) for all or group"""
        if rgroup is None: self.curs.execute("SELECT readout_id,name,descrip,units,readgroup_id FROM readout_types")
        else: self.curs.execute("SELECT readout_id,name,descrip,units FROM readout_types WHERE readgroup_id = ?", (rgroup,))
        return self.curs.fetchall()
    
    def get_messages(self, t0, t1, nmax=100, srcid=None):
        """Get messages in time range, (time, srcid, message)"""
        if not (nmax < 100): nmax = 100
        if srcid is None:
            self.curs.execute("SELECT time,src,msg FROM textlog WHERE time >= ? AND time <= ? ORDER BY time DESC LIMIT ?", (t0, t1, nmax))
        else:
            self.curs.execute("SELECT time,src,msg FROM textlog WHERE time >= ? AND time <= ? AND src=? ORDER BY time DESC LIMIT ?", (t0, t1, srcid, nmax))
        return self.curs.fetchall()
    
    def get_newest(self, ilist):
        """Return newest (id,time,value) for each list item"""
        rs = []
        for i in ilist:
            self.curs.execute("SELECT readout_id,time,value FROM readings WHERE readout_id = ? ORDER BY time DESC LIMIT 1", (i,))
            rs.append(self.curs.fetchone())
        return rs
    
    def launch_dataserver(self):
        """Launch server providing database read access"""
        # server thread interface to DB
        self.servconn = sqlite3.connect("file:%s?mode=ro"%self.dbname, uri=True)
        self.curs = self.servconn.cursor()
        
        # xmlrpc web interface for data updates
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)
        server = SimpleXMLRPCServer(("localhost", self.port), requestHandler=RequestHandler, allow_none=True)
        #server.register_introspection_functions()
        
        server.register_function(self.get_readgroups, 'readgroups')
        server.register_function(self.get_readtypes, 'readtypes')
        server.register_function(self.get_messages, 'messages')
        server.register_function(self.get_readout_info, 'readout_info')
        server.register_function(self.get_datapoints, 'datapoints')
        server.register_function(self.get_newest, 'newest')
        
        server.serve_forever()

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("--port",  dest="port",    action="store", type="int",    help="Localhost port")
    parser.add_option("--db",    dest="db",      action="store", type="string", help="path to database")
    options, args = parser.parse_args()
    
    D = LogServer(options.db, options.port)
    threading.Thread(target = D.launch_dataserver).start()
