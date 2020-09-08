## \file logger_DB_interface.py Convenience functions for working with log DB

import sqlite3
import time
import os
import shlex

warn_wall = True # whether to send "wall" messages on warning/errors

def logdb_cxn(db):
    """Connection to logger DB"""
    conn = sqlite3.connect(db, 60)
    curs = conn.cursor()
    curs.execute("PRAGMA foreign_keys = ON")
    return conn,curs

class readout_info:
    """Information on readout entry in DB, with most recent values"""
    def __init__(self, rid, nm, ds, un):
        self.rid = rid
        self.name = nm
        self.descrip = ds
        self.units = un

        self.time = None
        self.val = None

def make_insert_command(tname, valdict, cols = None):
    """Generate 'insert' command from dictionary and optional insert columns list"""
    if cols is None: cols = valdict.keys()
    icmd = "INSERT INTO %s("%tname + ", ".join(cols) + ") VALUES (" + ",".join(["?"]*len(cols)) +")"
    vals = tuple([valdict.get(c,None) for c in cols])
    return (icmd, vals)

def get_readout_id(curs, name):
    """Get identifier for readout by name and optional instrument name"""
    curs.execute("SELECT readout_id FROM readout_types WHERE name = ?", (name,))
    r = curs.fetchall()
    return r[0][0] if len(r) == 1 else None

def get_readout_info(curs, rid):
    """Get readout information by ID number"""
    curs.execute("SELECT readout_id,name,descrip,units FROM readout_types WHERE readout_id = ?", (rid,))
    r = curs.fetchall()
    return readout_info(*r[0]) if len(r) == 1 else None

def add_reading(curs, tid, value, t = None):
    """Log reading, using current time for timestamp if not specified"""
    t = time.time() if t is None else t
    curs.execute(*make_insert_command("readings",{"readout_id":tid, "time":t, "value":value}))

def add_message(curs, src, msg, t = None):
    """Log a textual message, using current time for timestamp if not specified"""
    t = time.time() if t is None else t
    curs.execute(*make_insert_command("textlog",{"readout_id":src, "time":t, "msg":msg}))
    is_err = "ERROR" in msg.upper()
    if warn_wall and (is_err or "WARNING" in msg.upper()):
        if os.path.exists('/usr/bin/cowsay'):
            os.system("echo %s | cowsay %s | wall"%(shlex.quote(msg), '-d' if is_err else '-p'))
        else: os.system("echo %s | wall"%shlex.quote(msg))
