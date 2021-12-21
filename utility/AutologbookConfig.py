#!/usr/bin/python3
## \file AutologbookConfig.py Network configuration for Autologbook functions

import os
import platform
import socket
from pathlib import Path

# location of autologbook code repository
autologbook_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# location of logging DB
logdb_file = str(Path.home())+"/autologbook_db.sql"
# chat log DB file; set None to disable
chatlog_db = str(Path.home())+"/chatlog_db.sql"

# node this script is being run from, e.g. "pitorius4"
thishost = platform.node()
# full domain name, e.g. "pitorius4.lan"
thisdomain = socket.getfqdn()
# host for logging, chat DB
log_DB_host = os.environ.get("AUTOLOGBOOK_DB_HOST", thisdomain)

# port number for log DB XMLRPC (read)server
log_xmlrpc_port = 50002
# port number for log DB write access XMLRPC server; 0 to disable
log_xmlrpc_writeport = 0 #50003
# port number for TCP logbook write access; 0 to disable
log_tcp_port = 50004
# ... avoid deadlock caused by both at once!
assert not (log_xmlrpc_writeport and log_tcp_port)

# host for web view HTTP server
http_host = thisdomain
# port number for web view server;
# 443 is default for HTTPS requires extra permissions:
#   sudo ufw allow 443
#   sudo setcap CAP_NET_BIND_SERVICE=+eip /usr/bin/python3.7
http_webview_port = 50000
# directory served
http_datdir = os.environ.get("AUTOLOGBOOK_WEBDATA", autologbook_dir + "/web_interface/")
# simple login password
http_login = os.environ.get("AUTOLOGBOOK_WEBAUTH", "autologbook:seethedata")
# certificate, key file for https web view (auto-generated if nonexistent)
https_certfile = autologbook_dir + "/scripts/https_cert.pem"
https_keyfile = autologbook_dir + "/scripts/https_key.pem"
if http_host == "localhost": https_certfile = https_keyfile = http_login = None

########################################
########################################

def network_config_summary():
    """Print summary of configuration parameters"""
    print()
    print("This computer is host", thishost, "domain", thisdomain, "and database is on", log_DB_host)
    print("XMLRPC data on port", log_xmlrpc_port)
    if log_xmlrpc_writeport: print("\twith write access on port", log_xmlrpc_writeport)
    if log_tcp_port: print("\tTCP access at port", log_tcp_port);
    print("Web view at https://%s:%i"%(http_host, http_webview_port), "login", http_login)
    print()
