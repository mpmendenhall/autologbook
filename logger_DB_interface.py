## \file logger_DB_interface.py Convenience functions for working with log DB

import sqlite3
import time

def logdb_cxn(db):
    """Connection to logger DB"""
    conn = sqlite3.connect(db)
    curs = conn.cursor()
    curs.execute("PRAGMA foreign_keys = ON")
    return conn,curs

class readgroup_info:
    """Information on instrument entry in DB"""
    def __init__(self, rid, nm, ds):
        self.rid = rid
        self.name = nm
        self.descrip = ds

class readout_info:
    """Information on readout entry in DB, with most recent values"""
    def __init__(self, rid, nm, ds, un, iid):
        self.rid = rid
        self.name = nm
        self.descrip = ds
        self.units = un
        self.readgroup_id = iid
       
        self.time = None
        self.val = None

def make_insert_command(tname, valdict, cols = None):
    """Generate 'insert' command from dictionary and optional insert columns list"""
    if cols is None: cols = valdict.keys()
    icmd = "INSERT INTO %s("%tname + ", ".join(cols) + ") VALUES (" + ",".join(["?"]*len(cols)) +")"
    vals = tuple([valdict.get(c,None) for c in cols])
    return (icmd, vals)
    
def get_readrgoup(curs, name):
    """Get readout group by name"""
    curs.execute("SELECT readgroup_id,name,descrip FROM readout_groups WHERE name = ?", (name,))
    r = curs.fetchall()
    return readgroup_info(*r[0]) if len(r) == 1 else None

def get_readout_id(curs, name, group_name = None):
    """Get identifier for readout by name and optional instrument name"""
    if group_name is None:
        curs.execute("SELECT readout_id FROM readout_types WHERE name = ?", (name,))
    else:
        curs.execute("SELECT readout_id FROM readout_types JOIN readout_groups ON readgroup_id = readout_groups.readgroup_id WHERE readout_types.name = ? AND readout_groups.name = ?", (name, group_name))
    r = curs.fetchall()
    return r[0][0] if len(r) == 1 else None
    
def get_readout_info(curs, rid):
    """Get readout information by ID number"""
    curs.execute("SELECT readout_id,name,descrip,units,readgroup_id FROM readout_types WHERE readout_id = ?", (rid,))
    r = curs.fetchall()
    return readout_info(*r[0]) if len(r) == 1 else None
        
def create_readgroup(curs, nm, descrip, overwrite = False):
    """Assure instrument entry exists, creating/updating as needed"""
    curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO readout_groups(name,descrip) VALUES (?,?)", (nm,descrip))
    return get_readrgoup(curs,nm)
    
def create_readout(curs, group_id, name, descrip, units, overwrite = False):
    """Assure a readout exists, creating as necessary; return readout ID"""
    curs.execute("INSERT OR " + ("REPLACE" if overwrite else "IGNORE") + " INTO readout_types(name,descrip,units,readgroup_id) VALUES (?,?,?,?)", (name,descrip,units,group_id))
    curs.execute("SELECT readout_id FROM readout_types WHERE name = ? AND readgroup_id = ?", (name,group_id))
    r = curs.fetchall()
    return r[0][0] if len(r) == 1 else None
    
def add_reading(curs, tid, value, t = None):
    """Log reading, using current time for timestamp if not specified"""        
    t = time.time() if t is None else t
    curs.execute(*make_insert_command("readings",{"readout_id":tid, "time":t, "value":value}))

def add_message(curs, src, msg, t = None):
    """Log a textual message, using current time for timestamp if not specified"""
    t = time.time() if t is None else t
    curs.execute(*make_insert_command("textlog",{"src":src, "time":t, "msg":msg}))
