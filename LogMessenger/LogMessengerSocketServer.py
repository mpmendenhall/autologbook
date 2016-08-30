#!/usr/bin/python3
## \file LogMessengerSocketServer.py Daemon accepting socket connections to fill logger DB
# ./LogMessengerSocketServer.py --db test.db --port 9999

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
        
        while True:
            try:
                rqtp = struct.unpack("i",self.request.recv(4))[0]
            except:
                break
            print("request type %i"%rqtp)
            
            if rqtp == 1:
                origin = self.recv_string()
                descrip = self.recv_string()
                print("getting origin '%s' '%s'"%(origin,descrip))
                callq.put( (create_readgroup, (curs, origin, descrip), rq) )
                self.request.sendall(struct.pack("q",rq.get().rid))
                
            elif rqtp == 2:
                gid = self.recv_i64()
                datname = self.recv_string()
                descrip = self.recv_string()
                units = self.recv_string() 
                print("getting datapoint %i:'%s' '%s' [%s]"%(gid,datname,descrip,units))
                callq.put( (create_readout, (curs, gid, datname, descrip, units), rq) )
                self.request.sendall(struct.pack("q", rq.get()))
                
            elif rqtp == 3:
                datid = self.recv_i64()
                val = self.recv_double()
                ts = self.recv_double()
                print("Datapoint %i: %g, %g"%(datid, val, ts))
                callq.put( (add_reading, (curs, datid, val, ts), rq) )
                rq.get()
                
            elif rqtp == 4:
                src = self.recv_i64()
                m = self.recv_string()
                ts = self.recv_double()
                print("Message: "+m)
                callq.put( (add_message, (curs, src, m, ts), rq) )
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

def DB_stuffer_process():
    """Database communication process"""
    while True:
        while True:
            try:
                item = callq.get_nowait()
                item[2].put(item[0](*item[1]))
                callq.task_done()
            except queue.Empty: break
           
        conn.commit()
        time.sleep(0.1)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--port",  dest="port",    action="store", type="int", help="server port")
    parser.add_option("--host",  dest="host",    action="store", type="string", default="localhost", help="server host")
    parser.add_option("--db",    dest="db",      action="store", type="string", help="path to database")
    options, args = parser.parse_args()

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
