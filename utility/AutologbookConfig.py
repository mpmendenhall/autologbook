#!/usr/bin/python3
## \file AutologbookConfig.py Network configuration for Autologbook functions

import os
import platform

# location of autologbook code repository
autologbook = os.path.dirname(os.path.realpath(__file__))+"/../"
# location of logging DB
logdb_file = os.environ["HOME"]+"/autologbook_db.sql"
# chat log DB file; set None to disable
chatlog_db = os.environ["HOME"]+"/chatlog_db.sql"

# node this script is being run from
thishost = platform.node()
# host for logging, chat DB
log_DB_host = os.environ.get("AUTOLOGBOOK_DB_HOST", thishost)

# port number for log DB XMLRPC (read)server
log_xmlrpc_port = 50002
# port number for log DB write access XMLRPC server; 0 to disable
log_xmlrpc_writeport = 50003

# host for web view HTTP server
http_host = thishost
# port number for web view server
http_webview_port = 50000
# directory served
http_datdir = os.environ.get("AUTOLOGBOOK_WEBDATA", autologbook + "/web_interface/")
# simple login password
http_login = os.environ.get("AUTOLOGBOOK_WEBAUTH", "autologbook:seethedata")
# certificate, key file for https web view (auto-generated if nonexistent)
https_certfile = os.environ["PWD"]+"/https_cert.pem"
https_keyfile = os.environ["PWD"]+"/https_key.pem"
if http_host == "localhost": https_certfile = https_keyfile = http_login = None

########################################
########################################

def network_config_summary():
    """Print summary of configuration parameters"""
    print()
    print("This computer is", thishost, "and database is on", log_DB_host)
    print("XMLRPC data on port", log_xmlrpc_port)
    if log_xmlrpc_writeport: print("\twith write access on port", log_xmlrpc_writeport)
    print("Web view at https://%s:%i"%(http_host, http_webview_port), "login", http_login)
    print()
