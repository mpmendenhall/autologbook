#!/bin/env python3

from optparse import OptionParser
import ctypes
import shlex
import subprocess
import os
import urllib.request
import socket
import time
from email.message import EmailMessage
import smtplib
import getpass

def is_web_connected(server="www.example.com"):
    """Check if web connection is up to 'reliable' server"""
    try:
        host = socket.gethostbyname(server)
        s = socket.create_connection((host, 80), 2)
        return True
    except: return False

class Barker:
    """Notifications from watchdog"""
    def __init__(self):
        self.mailto = None
        self.mailfrom = None
        self.popup = True
        self.smtp = None
        self.smtpu = None
        self.smpt_passwd = None

    def bark(self, title, text):
        """Alert to message"""
        print("###",title,"###\n")
        print(text)

        if self.smtp and self.mailto:
            if not self.mailfrom: self.mailfrom = self.mailto

            M = EmailMessage()
            M.set_content(text)
            M['Subject'] = title
            M['To'] = self.mailto
            M['From'] = self.mailfrom

            try:
                s = smtplib.SMTP(self.smtp)
                s.starttls()
                s.login(self.smtpu if self.smtpu else self.mailfrom, self.smpt_passwd)
                s.send_message(M)
                s.quit()
                print("Email alert sent!")
                return
            except:
                print("Failed to send email alert.")
                self.popup = True

        if self.popup:
            try: # Linux via zenity
                    res = subprocess.Popen(['zenity','--warning','--text', text, '--title', title, '--width=800'], stdout=subprocess.PIPE)
                    res.communicate()
            except:
                try: # MacOS vi AppleScript
                    res = subprocess.Popen(['osascript','-e', 'tell app "Finder" to display dialog "%s"'%shlex.quote(text)])
                except: # Windows
                    MessageBox = ctypes.windll.user32.MessageBoxW
                    MessageBox(None, text, title, 0)


class Webdog(Barker):
    """Watchdog retrieving webpage"""
    def __init__(self, url=None):
        super().__init__()
        self.url = url
        self.lastup = None
        self.B = Barker()

    def config(self, opts):
        """Configure from OptParse options"""
        self.url = opts.url
        self.lastup = opts.lastup
        self.mailto = opts.mailto
        self.mailfrom = opts.mailfrom
        self.smtp = opts.smtp
        self.smtpu = opts.smtpu
        self.smpt_passwd = opts.smtp_pwd

    def check(self):
        """Load and check watchdog page"""
        try:
            headers = { }
            if self.lastup is not None:
                headers['If-Modified-Since'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()-self.lastup))
            req = urllib.request.Request(self.url, None, headers)
            with urllib.request.urlopen(req) as response:
                page = response.read()
                self._check(page.decode("utf-8"))
        except urllib.error.URLError as e:
            if e.reason == 'Not Modified':
                self.bark('Watchdog is asleep!', "Watchdog webpage '%s' has not been modified within the last %g minutes."%(self.url,self.lastup/60.))
                return
            if is_web_connected(): self.bark('Watchdog is dead!', "Unable to connect to watchdog webpage '%s': %s"%(self.url, str(e.reason)))
            else: print("Web Watchdog has no network connection.")

    def _check(self, p):
        print("\n---- Watchdog report ----")
        print(p)

        es = []
        for l in p.split('\n'):
            if "ERROR" in l.upper(): es.append(l)

        if es: self.bark('Watchdog alert!', '\n'.join(es[:10]))

# ./Watchdog.py --url http://www.example.com/ --lastup 600 --mailto "foo@example.com" --smtp "smtp.example.com:587"

def wdParser():
    parser = OptionParser()
    parser.add_option("--url",      help="page url")
    parser.add_option("--lastup",   type=float, help="check time since last page updage [seconds]")
    parser.add_option("--mailto",   help="email notifications to this address")
    parser.add_option("--mailfrom", help="email notifications from this address")
    parser.add_option("--loop",     type=float, help="repeat checks every [n] minutes")
    parser.add_option("--smtp",     help="email smtp server address")
    parser.add_option("--smtpu",    help="smtp server username")
    return parser

if __name__=="__main__":
    parser = wdParser()
    options, args = parser.parse_args()
    options.smtp_pwd = None
    if options.smtp: options.smtp_pwd = getpass.getpass("Password for '%s': "%options.smtp)

    if options.url:
        wd = Webdog()
        wd.config(options)
        wd.check()
        while options.loop:
            time.sleep(60*options.loop)
            wd.check()
