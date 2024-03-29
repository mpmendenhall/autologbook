#!/usr/bin/python3
## \file SystemLaucher.py Helper for controlling Autologbook ecosystem

from AutologbookConfig import *
import subprocess
import time
from optparse import OptionParser
import shlex

# names of services to launch/monitor
service_names = ["HTTPServer.py", "LogDB_XMLRPC_server.py", "LogMessengerSocketServer.py"]

def remote_cmd(host, cmd, tout = 5):
    """Run command on remote host or localhost"""
    if host in ["localhost", "127.0.0.1", thishost]: os.system(cmd)
    else: subprocess.call(["ssh","-x", host, cmd], timeout = tout)

def tunnel_back(host, port):
    """Set up ssh tunnel from remote back to local for log messenger access"""
    if host in ["localhost", "127.0.0.1", thishost]: return
    cmd = 'nc localhost %i < /dev/null || nohup ssh -4xfN %s -L %i:localhost:%i > /dev/null 2>&1'%(port, thishost, port, port)
    print(' '.join(cmd))
    subprocess.call(["ssh","-x", host, cmd])

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
    for p in ps: os.system("kill "+sig+" %i"%p[1])

    # if "soft kill" requested, do this first, then send hard kill signal
    time.sleep(2.0)
    if ps and sig=="-INT": kill_network_servers("-9", names)
    time.sleep(0.5)

logflags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC

def launch_tcpserver():
    tcpserver_log = os.open('TCPServer_Log.txt', logflags)
    cmd = ["python3", autologbook_dir+"/scripts/LogMessengerSocketServer.py", "--db", logdb_file, "--port", str(log_tcp_port), "--wall"]
    subprocess.Popen(cmd, stdout=tcpserver_log, stderr=tcpserver_log, pass_fds=[tcpserver_log])

def launch_xmlserver():
    xmlserver_log = os.open('XMLRPCServer_Log.txt', logflags)
    cmd = ["python3", autologbook_dir+"/scripts/LogDB_XMLRPC_server.py",
                      "--readport", str(log_xmlrpc_port), "--db", logdb_file]
    if log_xmlrpc_writeport: cmd += ["--writeport", str(log_xmlrpc_writeport)]
    print(' '.join(cmd))
    subprocess.Popen(cmd, stdout=xmlserver_log, stderr=xmlserver_log, pass_fds=[xmlserver_log])

def launch_httpserver():
    httpserver_log = os.open('HTTPServer_Log.txt', logflags)
    cmd = ["python3", autologbook_dir+"/scripts/HTTPServer.py", "--dir", http_datdir, "--host", '0.0.0.0', "--port", str(http_webview_port)]
    if http_login: cmd += ["--pwd", http_login]
    if https_certfile: cmd += ["--cert", https_certfile, "--key", https_keyfile]
    print(' '.join(cmd))
    subprocess.Popen(cmd, stdout=httpserver_log, stderr=httpserver_log, pass_fds=[httpserver_log])

def launch_network_servers():
    """Launch all necessary network services for Autologbook ecosystem"""
    kill_network_servers() # make sure nothing is already running
    if log_tcp_port: launch_tcpserver()
    if thisdomain == log_DB_host: launch_xmlserver()
    launch_httpserver()

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("--start",    action="store_true", help="start Autologbook network services")
    parser.add_option("--stop",     action="store_true", help="stop Autologbook network services")
    parser.add_option("--restart",  action="store_true", help="stop and restart Autologbook network services")
    parser.add_option("--rehttp",   action="store_true", help="(re)launch http server")
    if thisdomain == log_DB_host: parser.add_option("--rexmlrpc", action="store_true", help="(re)launch xmlrpc server")
    options, args = parser.parse_args()

    if https_certfile and not os.path.exists(https_certfile):
        print("Generating self-signed https certificate:")
        cmd = ['openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', https_keyfile, '-out', https_certfile,
               '-days', '365', '-nodes', '-subj', "/C=US/ST=Confusion/L=Mystery/O=The Illuminati/OU=DAQ/CN=%s"%thisdomain]
        print(' '.join(cmd))
        subprocess.call(cmd)

    if thisdomain == log_DB_host and not os.path.exists(logdb_file):
        print("\nLogging database '%s' not found; initializing it.\n"%logdb_file)
        os.system("sqlite3 %s < "%shlex.quote(logdb_file) + autologbook_dir + "/db_schema/logger_DB_schema.sql")

    if options.restart: options.stop = True; options.start = True
    if options.stop: kill_network_servers()
    if options.start: launch_network_servers()
    if options.rehttp: kill_network_servers(names=["HTTPServer.py"]); time.sleep(1); launch_httpserver()
    if thisdomain == log_DB_host:
        if options.rexmlrpc: kill_network_servers(names=["LogDB_XMLRPC_server.py"]); time.sleep(1); launch_xmlserver()
    check_if_running()
    network_config_summary()
