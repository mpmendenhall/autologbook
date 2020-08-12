#!/usr/bin/python3
## \file Null_LogDB.py Local testing fakeout drop-in for LogDB_XMLRPC_server interface

class Null_LogDB:
    """Local do-nothing fakeout logger for testing"""
    def __init__(self): pass
    def create_readgroup(self, n, *args): return n
    def create_readout(self, n, g, *args): return g + ':' + n
    def log_message(self, sid, msg): print(sid, ":", msg)
    def log_readout(self, rid, v, t): print(rid, ":", t, v)
    def commit(self): pass
