#!/usr/bin/python3

import sqlite3
import time

def insert_val_string(pfx, d):
    """Dictionary to string and tuple for insert statement"""
    return ( pfx + "(" + ",".join(d.keys())+") VALUES (" + ",".join(['?']*len(d)) + ")", tuple(d.values()) )

class ConfigDB:
    """Interface to configuration database"""
    
    def __init__(self, conn = None):
        """Initialize with database connection"""
        self.curs = conn.cursor() if conn is not None else None
        
    def make_configset(self, name, family, descrip, t = time.time()):
        """Define a new config_set and return identifier"""
        self.curs.execute(*insert_val_string("INSERT INTO config_set", {"name": name, "family": family, "descrip": descrip, "time": t}))
        return self.curs.lastrowid

    def find_configset(self, name, family = None):
        """Find configuration set by name and (optional) family; return None if nonexistent or ambiguous"""
        if family is not None:
            self.curs.execute("SELECT rowid FROM config_set WHERE name = ? AND family = ?",(name,family))
            r = self.curs.fetchone()
            return r[0] if r else None
        else:
            self.curs.execute("SELECT rowid FROM config_set WHERE name = ?",(name,))
            r = self.curs.fetchall()
            return r[0][0] if len(r)==1 else None
    
    def get_setname(self, csid):
        """Get name information for config set by rowid"""
        self.curs.execute("SELECT family,name FROM config_set WHERE rowid = ?",(csid,))
        return self.curs.fetchone()

    def set_config_value(self, csid, name, value):
        """Set a configuration parameter"""
        if name is None: # workaround for special case: sqlite3 does not enforce uniqueness on NULL
            self.curs.execute("SELECT COUNT(*) FROM config_values WHERE csid = ? AND name is NULL", (csid,))
            if self.curs.fetchone()[0]:
                self.curs.execute("UPDATE config_values SET value = ? WHERE csid = ? AND name is NULL", (value, csid))
                return
        self.curs.execute(*insert_val_string("INSERT OR REPLACE INTO config_values", {"csid":csid, "name":name, "value":value}))
        
    def get_config(self, csid):
        """Get configuration parameter values by set ID"""
        self.curs.execute("SELECT name,value FROM config_values WHERE csid = ?", (csid,))
        return dict(self.curs.fetchall())

    def mark_config_application(self, csid, t = time.time()):
        """Mark application of configuration set in DB"""
        self.curs.execute(*insert_val_string("INSERT INTO config_history", {"csid":csid, "time":t}))
        
    def find_config_at(self, time, family):
        """Find configuration in use (nearest previously applied) of specified family"""
        q = "SELECT csid FROM config_history JOIN config_set ON config_set.rowid = csid WHERE config_history.time <= ? AND config_set.family = ? ORDER BY config_history.time DESC LIMIT 1"
        self.curs.execute(q,(time,family))
        r = self.curs.fetchone()
        return r[0] if r else None

    def clone_config(self, csid, name, descrip):
        """Clone configuration to new name and description"""
        self.curs.execute("SELECT family FROM config_set WHERE rowid = ?", (csid,))
        family = self.curs.fetchone()
        if not family:
            return None
        self.curs.execute("SELECT COUNT(*) FROM config_set WHERE name = ? AND family = ?", (name,family[0]))
        if self.curs.fetchone()[0]:
            return None
        
        cvals = self.get_config(csid)
        newid = self.make_configset(name, family[0], descrip)
        for (k,v) in cvals.items():
            self.set_config_value(newid, k, v)
        return newid
    
    def has_been_applied(self, csid):
        """Whether a configuration has been previously used"""
        self.curs.execute("SELECT COUNT(*) FROM config_history WHERE csid = ?", (csid,))
        return self.curs.fetchone()[0]
       
    def delete_if_not_applied(self, paramid):
        """Delete a parameter only if from a non-applied configuration set"""
        self.curs.execute("DELETE FROM config_values WHERE rowid = ? AND NOT (SELECT COUNT(*) FROM config_history WHERE config_history.csid = config_values.csid)", (paramid,))
    def set_if_not_applied(self, paramid, value):
        """Set a parameter only if from a non-applied configuration set"""
        self.curs.execute("UPDATE config_values SET value = ? WHERE rowid = ? AND NOT (SELECT COUNT(*) FROM config_history WHERE config_history.csid = config_values.csid)", (value, paramid,))
        
if __name__ == "__main__":
    import os
    dbname = "config_test.db"
    if not os.path.exists(dbname):
        os.system("sqlite3 %s < config_DB_description.txt"%dbname)

    conn = sqlite3.connect(dbname)
    C = ConfigDB(conn)
    
    csid = C.make_configset("all_1000", "PMT_HV", "all PMTs at 1000V")
    for i in range(32):
       C.set_config_value(csid, "V_%03i"%i, 1000.)
           
    C.mark_config_application(csid)
    
    print(C.find_configset("all_1000", "PMT_HV"))
    capp = C.find_config_at(time.time(), "PMT_HV")
    print(C.get_config(capp))
    
    conn.commit()
