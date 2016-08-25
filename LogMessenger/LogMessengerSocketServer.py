#!/usr/bin/python3

import socket
import threading
import socketserver
import time
import struct

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("Starting socket connection.")
        
        while True:
            try:
                rqtp = struct.unpack("i",self.request.recv(4))[0]
            except:
                break
            print("request type %i"%rqtp)
            
            if rqtp == 1:
                origin = self.recv_string()
                print("getting origin '%s'"%origin)
                self.request.sendall(struct.pack("q",999))
                
            elif rqtp == 2:
                datname = self.recv_string()
                print("getting datapoint '%s'"%origin)
                self.request.sendall(struct.pack("q",888))
                
            elif rqtp == 3:
                datid = self.recv_i64()
                val = self.recv_double()
                ts = self.recv_double()
                print("Datapoint %i: %g, %g"%(datid, val, ts))
                
            elif rqtp == 4:
                m = self.recv_string()
                print("Message: "+m)
                
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

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    while 1:
        time.sleep(1)
        
    server.shutdown()
    server.server_close()
