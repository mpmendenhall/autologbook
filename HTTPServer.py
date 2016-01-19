#!/usr/bin/python3

import http.server
import socketserver

class LoggerCGIHander(http.server.CGIHTTPRequestHandler):
    cgi_directories = ['/cgi-logger']
    def __init__(self, request, client_address, server):
        http.server.CGIHTTPRequestHandler.__init__(self, request, client_address, server)

PORT = 8005
httpd = http.server.HTTPServer(("localhost", PORT), LoggerCGIHander)

print("serving at port", PORT)
httpd.serve_forever()
