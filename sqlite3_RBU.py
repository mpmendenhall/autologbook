#!/usr/bin/python3
# should work in either python2 or 3

import sqlite3
import queue
import time
import threading

class RBU_table_data:
    """Information on RBU-cloned table"""
    def __init__(self,tname,curs):
        """Initialize from table name and cursor to target DB"""
        self.tname = tname

        # load column information
        curs.execute("PRAGMA table_info(%s)"%tname)
        self.cols = [[c[1], c[2].upper().replace("UNIQUE","")] for c in curs.fetchall()]
        self.colnames = [c[0] for c in self.cols]

        # identify primary key (can't handle anything fancy...)
        self.primary = None
        for c in self.cols:
            if "PRIMARY KEY" in c[1]:
                self.primary = c[0]
                c[1] = c[1].replace("PRIMARY KEY", "")
                break
        if self.primary is None:
            self.primary = "rowid"

    def rbu_table_cmd(self):
        """Create RBU table"""
        print("Setting up table '%s' in RBU"%self.tname)
        rbucols = ["%s %s"%(c[0],c[1]) if c[1] else c[0] for c in self.cols]
        if self.primary == "rowid":
            rbucols.append("rbu_rowid")
        rbucols.append("rbu_control")
        return "CREATE TABLE data_%s ("%self.tname + ", ".join(rbucols) + ")"
    
class RBU_cloner:
    """Copies sqlite3 commands between active database connecion and Resumable Bulk Update (RBU) copy"""
    
    def __init__(self, curs = None):
        """Initialize with cursors for primary database"""
        self.rbu_curs = curs
        
        self.rbu_outname = "test_rbu_%i.db"
        self.rbu_prevName = None        # name of previously completed RBU file
        self.rbu_q = queue.Queue()
        self.rbu_stuffer_thread = None
        self.stuffer_lock = threading.Lock()
        self.autocommit = False
        
        # list of tables (with column names) configured in RBU
        self.tables = {}
        self.old_tables = []
        self.tables_lock = threading.Lock()

    def setup_table(self, tname):
        """Initialize table in RBU"""
        if tname in self.tables:
            return
        self.tables_lock.acquire()
        self.tables[tname] = RBU_table_data(tname, self.rbu_curs)
        self.rbu_q.put((self.tables[tname].rbu_table_cmd(), ()))
        self.tables_lock.release()

    @staticmethod
    def make_insert_command(tname, valdict, cols = None):
        """Generate 'insert' command from dictionary and optional insert columns list"""
        if cols is None:
            cols = valdict.keys()
        icmd = "INSERT INTO %s("%tname + ", ".join(cols) + ") VALUES (" + ",".join(["?"]*len(cols)) +")"
        vals = tuple([valdict.get(c,None) for c in cols])
        return (icmd, vals)
        
    @staticmethod
    def _insert(curs, tname, valdict, cols = None):
        """Generate and execute an insert command"""
        icmd,vals = RBU_cloner.make_insert_command(tname, valdict, cols)
        if curs:
            curs.execute(icmd, vals)
        else:
            print(icmd, vals)

    def insert(self, tname, valdict):
        """Insert a row into named table, given dictionary of column name/values"""
        self.setup_table(tname)

        self._insert(self.rbu_curs, tname, valdict)
        if self.autocommit:
            self.conn.commit()
        valdict["rbu_control"] = 0
        self.rbu_q.put(self.make_insert_command("data_"+tname, valdict))

    def update(self, tname, whereclause, updvals):
        """Perform an 'update' operation, specified by a WHERE clause and dictionary of update columns"""
        self.setup_table(tname)

        # determine primary key for affected rows
        pkey = self.tables[tname].primary
        self.rbu_curs.execute("SELECT %s FROM %s WHERE %s"%(pkey, tname, whereclause))
        rws = [r[0] for r in self.rbu_curs.fetchall()]

        # update main DB
        ucmd = "UPDATE " + tname + " SET " + ", ".join([c+" = ?" for c in updvals.keys()]) + " WHERE " + whereclause
        self.rbu_curs.execute(ucmd, tuple(updvals.values()))

        # generate RBU commands for each row
        rbucols = self.tables[tname].colnames
        updvals["rbu_control"] = ''.join(['x' if c in updvals else '.' for c in rbucols])
        if pkey == "rowid":
            rbucols.append("rbu_rowid")
            pkey = "rbu_rowid"
        rbucols.append("rbu_control")
        for r in rws:
            updvals[pkey] = r
            self.rbu_q.put(self.make_insert_command("data_"+tname, updvals, rbucols))
        
    def delete(self, tname, whereclause):
        """Perform a 'delete' operation, specified by a WHERE clause"""
        self.setup_table(tname)

        # determine primary key for affected rows
        pkey = self.tables[tname].primary
        self.rbu_curs.execute("SELECT %s FROM %s WHERE %s"%(pkey, tname, whereclause))
        rws = [r[0] for r in self.rbu_curs.fetchall()]

        # update main DB
        self.rbu_curs.execute("DELETE FROM " + tname + " WHERE " + whereclause)

        # generate RBU delete command for each row
        if pkey == "rowid":
            pkey = "rbu_rowid"
        for r in rws:
            self.rbu_q.put(self.make_insert_command("data_"+tname, {pkey: r, "rbu_control": 1}))

    def rbu_stuffer(self):
        """Thread loop for writing commands to RBU DB"""
        
        # set up new file
        fname = self.rbu_outname%int(time.time())
        print("Initializing RBU output in",fname)
        rbu_conn = sqlite3.connect(fname)
        rbu_curs = rbu_conn.cursor()
        t_start = time.time()
        self.tables_lock.acquire()
        for t in self.old_tables:
            print("Regenerating table",t)
            rbu_curs.execute(self.tables[t].rbu_table_cmd())
        self.tables_lock.release()

        # loop on commands queue
        while self.stuffer_lock.acquire(False):
            self.stuffer_lock.release()
            try:
                cmd = self.rbu_q.get(False)
            except:
                time.sleep(1)
                continue
                
            print("RBU command:",cmd)
            if "CREATE TABLE" in cmd[0]:
                 self.old_tables.append(cmd[0].split(" ")[2][5:])
            rbu_curs.execute(cmd[0], cmd[1])

        # close out
        print("Stuffer thread stopping.") 
        rbu_conn.commit()
        rbu_conn.close()
        self.rbu_prevName = fname
    
    def stop_stuffer(self):
        """Stop RBU stuffer thread and close out file"""
        print("Stopping stuffer thread...")
        self.stuffer_lock.acquire()
        self.rbu_stuffer_thread.join()
        self.stuffer_lock.release()
        
    def flush_stuffer(self):
        """Wait for stuffer buffer to clear"""
        #print("Waiting for RBU queue to clear...")
        while True:
            qs = self.rbu_q.qsize()
            if not qs:
                break
            #print("\t...", qs)
            time.sleep(1)
    
    def restart_stuffer(self):
        """Freeze, write, and re-open new RBU DB"""
        if self.rbu_stuffer_thread:
            self.stop_stuffer()
        self.rbu_stuffer_thread = threading.Thread(target = self.rbu_stuffer)
        self.rbu_stuffer_thread.start()
        
        
        
        
        
        
        
if __name__ == "__main__":
    conn = sqlite3.connect('test.db')
    R = RBU_cloner(conn.cursor())
    R.restart_stuffer()
    
    for j in range(2):
        for i in range(10):
            R.insert("readings", {"type_id":1, "value":3.14, "time":i})
            time.sleep(0.5)
        if j < 1:
            R.flush_stuffer()
            R.restart_stuffer()
        else:
            R.stop_stuffer()
        
    conn.commit()
