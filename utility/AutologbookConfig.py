#!/usr/bin/python3
## \file AutologbookConfig.py Network configuration for Autologbook functions

import os
import platform

# location of autologbook repository
autologbook = os.environ["APP_DIR"]+"/autologbook"
# location of logging DB
logdb_file = os.environ["HOME"]+"/autologbook_db.sql"
# chat log DB file; set None to disable
chatlog_db = os.environ["HOME"]+"/chatlog_db.sql"

# node this script is being run from
thishost = platform.node()

# TCP socket logging DB server host (ssh tunneled from remote machined)
sock_loghost = "localhost"
# logging DB TCP sockets server port
log_tcp_port = 50001

# host for log DB XMLRPC server (provides data for web views)
log_xmlrpc_host = "localhost"
# port number for log DB XMLRPC (read)server
log_xmlrpc_port = 50002
# port number for log DB write access XMLRPC server; 0 to disable
log_xmlrpc_writeport = 50003

# host for web view HTTP server; set to "localhost" for local only
http_host = thishost
# port number for web view server
http_webview_port = 50000
# directory served
http_datdir = autologbook + "/web_interface/"
# simple login password
http_login = "autologbook:seethedata"
# certificate, key file for https web view (auto-generated if nonexistent)
https_certfile = os.environ["PWD"]+"/https_cert.pem"
https_keyfile = os.environ["PWD"]+"/https_key.pem"
if http_host == "localhost": https_certfile = https_keyfile = http_login = None

########################################
########################################

def network_config_summary():
    """Print summary of configuration parameters"""
    print()
    print("This computer is", thishost)
    print("TCP sockets data server on", sock_loghost, ":", log_tcp_port)
    print("XMLRPC data server on ", log_xmlrpc_host, ":", log_xmlrpc_port)
    if log_xmlrpc_writeport: print("\twith write access on", log_xmlrpc_host, ":", log_xmlrpc_writeport)
    print("Web view at https://%s:%i"%(http_host, http_webview_port), "login", http_login)
    print()
