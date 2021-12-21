#!/usr/bin/python3
## \file LogMessengerSocketServer.py Daemon accepting socket connections to fill logger DB
# ./LogMessengerSocketServer.py --db test.db --port 9999

import os
import socket
import sys
import threading
import socketserver
import time
import struct
from logger_DB_interface import *
import queue
from optparse import OptionParser
import traceback

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

    def create_readout(self, name, descrip, units):
        """Get/create readout"""
        self.send(2,"i")
        self.send_string(name)
        self.send_string(descrip)
        self.send_string(units)
        return self.recv_i64()

    def add_reading(self, rid, value, t = None):
        """Add readout value"""
        t = time.time() if t is None else t
        self.send(3,"i")
        self.send(rid,"q")
        self.send(value,"d")
        self.send(t,"d")

    def send(self,i,tp):
        self.sock.send(struct.pack(tp,i))

    def send_string(self, s):
        self.send(len(s),"N")
        self.sock.send(bytes(s,"UTF-8"))

    def recv_i64(self):
        return struct.unpack("q", self.sock.recv(8))[0]

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Handle commands to logging server (push to stuffer process)"""

    def handle(self):
        print("Starting socket connection.")
        rq = queue.Queue() # responses queue

        while True:
            try: rqtp = struct.unpack("i",self.request.recv(4))[0]
            except: break

            if rqtp == 2: # datapoint ID
                datname = self.recv_string()
                descrip = self.recv_string()
                units = self.recv_string()
                callq.put( (create_readout, (curs, datname, descrip, units), rq) )
                gid = rq.get()
                self.request.sendall(struct.pack("q", gid))

            elif rqtp == 3: # add datapoint
                datid = self.recv_i64()
                val = self.recv_double()
                ts = self.recv_double()
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
                print("Unrecognized request type", rqtp)
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
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

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
        nup = 0
        ncyc = 0
        while True:
            try:
                item = callq.get(True, 0.2)
                item[2].put(item[0](*item[1]))
                callq.task_done()
                nup += 1
                if nup > 10: break
            except queue.Empty:
                ncyc += 1
                if ncyc > 10: break
            except:
                traceback.print_exc()
                sys.stdout.flush()

        conn.commit()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--port", type="int", help="server port")
    parser.add_option("--host", default="localhost", help="server host")
    parser.add_option("--db",   help="path to database")
    parser.add_option("--wall", action="store_true", help="echo warnings to wall")
    options, args = parser.parse_args()

    if not os.path.exists(options.db):
        print("\nLogging database '%s' not found; consider trying:"%options.db)
        print("sqlite3 '%s' < ../db_schema/logger_DB_schema.sql"%options.db)
        exit(1)

    warn_wall = options.wall

    server = ThreadedTCPServer((options.host, options.port), ThreadedTCPRequestHandler)
    with server:

        callq = queue.Queue()
        conn,curs = logdb_cxn(options.db)

        my_id = create_readout(curs, "LogMessengerSocketServer.py", "Log messages database TCP sockets server", None)
        add_message(curs, my_id, "Starting LogMessenger socket server on %s:%i"%(options.host, options.port))
        conn.commit()

        # Start a thread with the server -- that thread will then start one more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        try: DB_stuffer_process()
        except: traceback.print_exc()

        server.shutdown()
        server.server_close()

    add_message(curs, my_id, "Stopping LogMessenger socket server on %s:%i"%(options.host,options.port))
    conn.commit()

