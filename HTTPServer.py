#!/usr/bin/python3

import http.server
from optparse import OptionParser

class LoggerCGIHander(http.server.CGIHTTPRequestHandler):
    cgi_directories = ['/cgi-logger']

class ConfigCGIHandler(http.server.CGIHTTPRequestHandler):
    cgi_directories = ['/cgi-config', '/cgi-logger']

parser = OptionParser()
parser.add_option("--port",  dest="port",    action="store", type="int", default = 8005, help="server port")
parser.add_option("--host",  dest="host",    action="store", type="string", default="localhost", help="server host")
parser.add_option("--mode",  dest="mode",    action="store", type="string", default="logger", help="server mode: logger or config")
options, args = parser.parse_args()

if  options.mode == "config":
    print("Webserver for autologbook Configuration DB")
    httpd = http.server.HTTPServer((options.host, options.port), ConfigCGIHandler)
else:
    print("Webserver for autologbook Logger DB")
    httpd = http.server.HTTPServer((options.host, options.port), LoggerCGIHander)

print("serving from %s:%i"%(options.host, options.port))
httpd.serve_forever()
