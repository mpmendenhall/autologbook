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

    def find_configset(self, name, family):
        """Find configuration set by name and family"""
        self.curs.execute("SELECT rowid FROM config_set WHERE name = ? AND family = ?",(name,family))
        r = self.curs.fetchone()
        return r[0] if r else None

    def set_config_value(self, csid, name, value):
        """Set a configuration parameter"""
        self.curs.execute(*insert_val_string("INSERT INTO config_values", {"csid":csid, "name":name, "value":value}))
        
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
