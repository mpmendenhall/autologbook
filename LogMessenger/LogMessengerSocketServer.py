#!/bin/env python3
## \file LogMessengerSocketServer.py Daemon accepting socket connections to fill logger DB
# ./LogMessengerSocketServer.py --db test.db --port 9999

import os
import socket
import threading
import socketserver
import time
import struct
from logger_DB_interface import *
import queue
from optparse import OptionParser

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("Starting socket connection.")
        rq = queue.Queue()
        verbose = False
        
        while True:
            try:
                rqtp = struct.unpack("i",self.request.recv(4))[0]
            except:
                break
            if verbose: print("request type %i"%rqtp)
            
            if rqtp == 1: # origin ID
                origin = self.recv_string()
                descrip = self.recv_string()
                #print("getting origin '%s' '%s'"%(origin,descrip))
                callq.put( (create_readgroup, (curs, origin, descrip), rq) )
                self.request.sendall(struct.pack("q",rq.get().rid))
                
            elif rqtp == 2: # datapoint ID
                gid = self.recv_i64()
                datname = self.recv_string()
                descrip = self.recv_string()
                units = self.recv_string() 
                if verbose: print("getting datapoint %i:'%s' '%s' [%s]"%(gid,datname,descrip,units))
                callq.put( (create_readout, (curs, gid, datname, descrip, units), rq) )
                self.request.sendall(struct.pack("q", rq.get()))
                
            elif rqtp == 3: # add datapoint
                datid = self.recv_i64()
                val = self.recv_double()
                ts = self.recv_double()
                if verbose: print("Datapoint %i: %g, %g"%(datid, val, ts))
                callq.put( (add_reading, (curs, datid, val, ts), rq) )
                rq.get()
                
            elif rqtp == 4: # add message
                src = self.recv_i64()
                m = self.recv_string()
                ts = self.recv_double()
                print("[%i] "%src+m)
                callq.put( (add_message, (curs, src, m, ts), rq) )
                rq.get()
                
            elif rqtp == 5: # status notification
                src = self.recv_i64()
                status = self.recv_i64()
                callq.put( (set_status, (src,status), rq) )
                rq.get()
                
            elif rqtp == 6: # clear status counter
                status = self.recv_i64()
                callq.put( (clear_status, (status,), rq) )
                rq.get()
                
            elif rqtp == 7: # get status count
                status = self.recv_i64()
                callq.put( (count_status, (status,), rq) )
                self.request.sendall(struct.pack("q", rq.get()))
            
            elif rqtp == 8: # clear all
                callq.put( (clear_all, (), rq) )
                rq.get()

            else:
                # unrecognized request type
                assert False

        print("Ending socket connection.")
        
    def recv_string(self):
        n = struct.unpack("N", self.request.recv(8))[0]
        return str(self.request.recv(n), 'ascii')
    
    def recv_i64(self):
        return struct.unpack("q", self.request.recv(8))[0]
    
    def recv_double(self):
        return struct.unpack("d", self.request.recv(8))[0]
    
    
    
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# most recent status signal by origin
current_status = {}
# accumulated origin lists by status
status_sets = {}

def set_status(origin, status):
    t = time.time()
    current_status[origin] = (status,t)
    status_sets.setdefault(status,set()).add(origin)

def clear_status(status):
    try: status_sets.pop(status)
    except: pass

def clear_all():
    current_status.clear()
    status_sets.clear()

def count_status(status):
    try: return len(status_sets[status])
    except: return 0

def DB_stuffer_process():
    """Database communication process"""
    while True:
        nwait = 0
        while True:
            try:
                item = callq.get_nowait()
                item[2].put(item[0](*item[1]))
                callq.task_done()
                nwait = 0
            except queue.Empty:
                nwait += 1
                time.sleep(0.001)
                if nwait > 100: break

        conn.commit()
        time.sleep(0.1)

class LogServerConnection:
    """Connection to logging server"""
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
    def clear_all(self):
        self.send(8,"i")
    def clear_status(self,status):
        self.send(6,"i")
        self.send(status,"q")   
    def count_status(self, status):
        self.send(7,"i")
        self.send(status,"q")   
        return self.recv_i64()
    def send(self,i,tp):
        self.sock.send(struct.pack(tp,i))
    def recv_i64(self):
        return struct.unpack("q", self.sock.recv(8))[0]

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--port",  dest="port",    action="store", type="int", help="server port")
    parser.add_option("--host",  dest="host",    action="store", type="string", default="localhost", help="server host")
    parser.add_option("--db",    dest="db",      action="store", type="string", help="path to database")
    options, args = parser.parse_args()

    if not os.path.exists(options.db):
        print("\nLogging database '%s' not found.\nPerhaps initialize it with:\nsqlite3 '%s' < ../logger_DB_schema.sql\n"%(options.db, options.db))
        exit(1)
        
    callq = queue.Queue()
    conn = sqlite3.connect(options.db)
    curs = conn.cursor()
    curs.execute("PRAGMA foreign_keys = ON") 
        
    server = ThreadedTCPServer((options.host, options.port), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    
    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    
    DB_stuffer_process()
    
    server.shutdown()
    server.server_close()
