#!/bin/env python3
## \file HTTPServer.py CGI server for autologbook web interfaces

import http.server
import os
from optparse import OptionParser
import ssl

class LoggerCGIHander(http.server.CGIHTTPRequestHandler):
    cgi_directories = ['/cgi-logger']

class ConfigCGIHandler(http.server.CGIHTTPRequestHandler):
    cgi_directories = ['/cgi-config', '/cgi-logger']

parser = OptionParser()
parser.add_option("--port", type="int", default = 8005, help="server port")
parser.add_option("--host", default="localhost", help="server host")
parser.add_option("--mode", default="logger", help="server mode: logger or config")
parser.add_option("--db",   help="path to database")
parser.add_option("--dir",  help="base directory for served content")
parser.add_option("--cert", help="https certificate .pem file")
parser.add_option("--key",  help="https certifical key file")
options, args = parser.parse_args()

if options.dir: os.chdir(options.dir)

if options.db: os.environ["CONFIGWEBMANAGER_DB"] = options.db

if  options.mode == "config":
    print("Webserver for autologbook Configuration DB")
    httpd = http.server.HTTPServer((options.host, options.port), ConfigCGIHandler)
else:
    print("Webserver for autologbook Logger DB")
    httpd = http.server.HTTPServer((options.host, options.port), LoggerCGIHander)

# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -subj "/C=US/ST=California/L=Livermore/O=Company Name/OU=Org/CN=www.example.com" -nodes
if options.cert:
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=options.cert, keyfile=options.key, server_side=True)
    http.server.CGIHTTPRequestHandler.have_fork = False # Force the use of a subprocess ... otherwise get SSL_ERROR_RX_RECORD_TOO_LONG

print("serving from '%s' on %s:%i"%(os.getcwd(), options.host, options.port))
httpd.serve_forever()

