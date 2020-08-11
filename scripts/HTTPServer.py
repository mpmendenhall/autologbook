#!/bin/env python3
## \file HTTPServer.py HTTP(S) + CGI server for autologbook web interfaces

import http.server
import os
from optparse import OptionParser
import ssl
import base64

class PWAuthHandler(http.server.CGIHTTPRequestHandler):

    def checkAuthentication(self):
        if self.server.auth is None: return True
        auth = self.headers.get('Authorization')
        if auth != "Basic %s" % self.server.auth:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="autologbook"')
            self.end_headers();
            return False
        return True

    def do_HEAD(self):
        if not self.checkAuthentication(): return
        super().do_HEAD()

    def do_GET(self):
        if not self.checkAuthentication(): return
        if self.reset_dir: os.chdir(self.reset_dir) # follow moving symbolic link
        super().do_GET()

    def do_POST(self):
        if not self.checkAuthentication(): return
        super().do_POST()

parser = OptionParser()
parser.add_option("--port", type="int", default = 8005, help="server port")
parser.add_option("--host", default="localhost", help="server host")
parser.add_option("--mode", help="server mode: 'cgi' to enable cgi-bin/")
parser.add_option("--dir",  help="base directory for served content")
parser.add_option("--pwd",  help="user:password HTTP Basic Authentication")
parser.add_option("--cert", help="https certificate .pem file")
parser.add_option("--key",  help="https certifical key file")
options, args = parser.parse_args()

if options.pwd: handler = PWAuthHandler
else: handler = http.server.CGIHTTPRequestHandler
# hack to include proper Content-encoding header for .svgz files
handler.extensions_map['.svgz'] = "image/svg+xml\r\nContent-encoding: gzip"

if options.dir:
    os.chdir(options.dir)
    handler.reset_dir = options.dir

if  options.mode == "cgi":
    print("enabling cgi mode")
    handler.cgi_directories = ['/cgi-bin']

httpd = http.server.HTTPServer((options.host, options.port), handler)
if options.pwd: httpd.auth = base64.b64encode(options.pwd.encode()).decode()

# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -subj "/C=US/ST=California/L=Livermore/O=Company Name/OU=Org/CN=www.example.com" -nodes
if options.cert:
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(options.cert, options.key)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    http.server.CGIHTTPRequestHandler.have_fork = False # Force the use of a subprocess ... otherwise get SSL_ERROR_RX_RECORD_TOO_LONG

print("serving from '%s' on %s:%i"%(os.getcwd(), options.host, options.port))
httpd.serve_forever()

