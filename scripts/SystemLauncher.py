#!/usr/bin/python3
## \file SystemLaucher.py Helper for controlling Autologbook ecosystem

from AutologbookConfig import *
import subprocess
import time
from optparse import OptionParser
import shlex

# names of services to launch/monitor
service_names = ["HTTPServer.py", "LogDB_XMLRPC_server.py"] #, "LogMessengerSocketServer.py"]

def remote_cmd(host, cmd, tout = 5):
    """Run command on remote host or localhost"""
    if host in ["localhost", thishost]: os.system(cmd)
    else: subprocess.call(["ssh","-x", host, cmd], timeout = tout)

def tunnel_back(hostname):
    """Set up ssh tunnel from remote back to local for log messenger access"""
    if host in ["localhost", thishost]: return
    subprocess.call(["ssh","-x", hostname, 'nc localhost %i --send-only < /dev/null || nohup ssh -4xfN %s -L %i:localhost:%i > /dev/null 2>&1'%(log_tcp_port, thishost, log_tcp_port, log_tcp_port)])

def check_if_running(names = service_names):
    """Check whether named processes are running, return system PIDs for each available"""
    print()
    ps = str(subprocess.check_output(['ps', '-ax'])).split("\\n")
    prunning = []
    for n in names:
        nrunning = 0
        for p in ps:
            if n in p:
                prunning.append((n, int(p.strip().split(" ")[0])))
                print("%s is running with PID %i"%prunning[-1])
                nrunning += 1
        if not nrunning: print(n,"is not running.")
    return prunning

def kill_network_servers(sig = "-INT", names = service_names):
    """Send signal to kill each DAQ network service"""
    ps = check_if_running(names)
    if not ps: return
    for p in ps:
        if p[0] == "Crunch_Realtime":
            cancel_exfiltrate()
            time.sleep(3)
        os.system("kill "+sig+" %i"%p[1])

    # if "soft kill" requested, do this first, then send hard kill signal
    time.sleep(2.0)
    if ps and sig=="-INT":
        kill_network_servers("-9", names)
    time.sleep(0.5)

logflags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC

def launch_tcpserver():
    tcpserver_log = os.open('TCPServer_Log.txt', logflags)
    subprocess.Popen([autologbook+"/scripts/LogMessengerSocketServer.py", "--db", logdb_file, "--port", str(log_tcp_port), "--wall"],
                     stdout=tcpserver_log, stderr=tcpserver_log, pass_fds=[tcpserver_log])

def launch_xmlserver():
    xmlserver_log = os.open('XMLRPCServer_Log.txt', logflags)
    subprocess.Popen([autologbook+"/scripts/LogDB_XMLRPC_server.py",
                      "--readport", str(log_xmlrpc_port), "--writeport", str(log_xmlrpc_writeport), "--db", logdb_file],
                     stdout=xmlserver_log, stderr=xmlserver_log, pass_fds=[xmlserver_log])

def launch_httpserver():
    if https_certfile and not os.path.exists(https_certfile):
        print("Generating self-signed https certificate:")
        os.system('openssl req -x509 -newkey rsa:4096 -keyout %s -out %s -days 365 -subj "/C=US/ST=Confusion/L=Mystery/O=The Illuminati/OU=DAQ/CN=%s" -nodes'%(https_keyfile, https_certfile, http_host))
    httpserver_log = os.open('HTTPServer_Log.txt', logflags)
    cmd = [autologbook+"/scripts/HTTPServer.py", "--dir", http_datdir, "--host", http_host, "--port", str(http_webview_port)]
    if http_login: cmd += ["--pwd", http_login]
    if https_certfile: cmd += ["--cert", https_certfile, "--key", https_keyfile]
    subprocess.Popen(cmd, stdout=httpserver_log, stderr=httpserver_log, pass_fds=[httpserver_log])

def launch_network_servers():
    """Launch all necessary network services for Autologbook ecosystem"""
    kill_network_servers() # make sure nothing is already running
    #launch_tcpserver()
    launch_xmlserver()
    launch_httpserver()

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("--start",    action="store_true", help="start Autologbook network services")
    parser.add_option("--stop",     action="store_true", help="stop Autologbook network services")
    parser.add_option("--restart",  action="store_true", help="stop and restart Autologbook network services")
    parser.add_option("--rehttp",   action="store_true", help="(re)launch http server")
    parser.add_option("--rexmlrpc", action="store_true", help="(re)launch xmlrpc server")
    options, args = parser.parse_args()

    if not os.path.exists(logdb_file):
        print("\nLogging database '%s' not found; initializing it.\n"%logdb_file)
        os.system("sqlite3 %s < "%shlex.quote(logdb_file) + autologbook + "/db_schema/logger_DB_schema.sql")

    if options.restart: options.stop = True; options.start = True
    if options.stop: kill_network_servers()
    if options.start: launch_network_servers()
    if options.rehttp: kill_network_servers(names=["HTTPServer.py"]); time.sleep(1); launch_httpserver()
    if options.rexmlrpc: kill_network_servers(names=["LogDB_XMLRPC_server.py"]); time.sleep(1); launch_xmlserver()
    check_if_running()
    network_config_summary()
