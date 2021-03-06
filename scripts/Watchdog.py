#!/usr/bin/python3
## \file Watchdog.py Watchdog utility for monitoring other processes

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
        self.popup = True       # True to always pop; False to pop if email fails; None to never pop
        self.smtp = None
        self.smtpu = None
        self.smpt_passwd = None
        self.memory = ".lastbark"   # name of file recording most recent bark emitted
        self.tquiet = 3600          # suppress repeated warnings for this interval

    def config(self, opts):
        """Configure from OptParse options"""
        self.mailto = opts.mailto
        self.mailfrom = opts.mailfrom
        self.smtp = opts.smtp
        self.smtpu = opts.smtpu
        self.smpt_passwd = opts.smtp_pwd
        if opts.tquiet is not None: self.tquiet = 60*opts.tquiet
        if options.nopop: self.popup = None

    def bark(self, title, text):
        """Alert to message"""
        print("###",title,"###\n")
        print(text)

        # check bark suppression file
        if os.path.exists(self.memory):
            dt = time.time() - os.stat(self.memory).st_mtime
            if dt < self.tquiet: return

        open(self.memory,'w').write(title+'\n\n'+text)

        mailgood = True
        if self.smtp and self.mailto:
            if not self.mailfrom:
                self.mailfrom = self.mailto.split(',')[0].strip()

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
            except:
                mailgood = False
                print("Failed to send email alert.")
                if self.popup is not None: self.popup = True

        if self.popup or (self.popup is not None and not mailgood):
            text = text[:1000]

            try: # Linux via zenity
                    res = subprocess.Popen(['zenity','--warning','--no-markup','--text', text, '--title', title, '--width=800'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    res.communicate()
            except:
                try: # MacOS via AppleScript
                    mtxt = lambda x: '"'+x.replace("\\",'\\\\').replace('"','\\"')+'"'
                    s = 'display dialog %s with title %s buttons {"fooey"} default button 1'%(mtxt(text), mtxt(title))
                    res = subprocess.Popen(['osascript','-e', s], stdout=subprocess.PIPE)
                    res.communicate()
                except: # Windows via why why why?
                    MessageBox = ctypes.windll.user32.MessageBoxW
                    MessageBox(None, text, title, 0)


class Watchdog(Barker):
    """Watchdog base class"""

    def __init__(self):
        super().__init__()
        self.checkin = False


    def config(self, opts):
        """Configure from OptParse options"""
        super().config(opts)
        self.checkin = opts.checkin

    def _check(self, p):
        """Parse watchdog file and report errors"""
        print("\n---- Watchdog report ----")
        print(p)

        es = []
        for l in p.split('\n'):
            if "ERROR" in l.upper(): es.append(l)

        if es:
            self.bark('Watchdog alert!', "Watchdog errors from '%s':\n\n"%self.url + '\n'.join(es[:10]))
            return False

        if self.checkin: self.bark("Watchdog check-in OK", p)
        if os.path.exists(self.memory): os.remove(self.memory)
        return True

class Webdog(Watchdog):
    """Watchdog retrieving webpage"""

    def __init__(self, url=None):
        super().__init__()
        self.url = url
        self.lastup = 600

    def config(self, opts):
        """Configure from OptParse options"""
        super().config(opts)
        self.url = opts.url
        if opts.lastup is not None: self.lastup = opts.lastup

    def check(self):
        """Load and check watchdog page"""
        try:
            headers = { }
            if self.lastup is not None:
                headers['If-Modified-Since'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()-self.lastup))
            req = urllib.request.Request(self.url, None, headers)
            with urllib.request.urlopen(req) as response:
                page = response.read().decode("utf-8")
                if not self._check(page): return

        except urllib.error.URLError as e:

            if e.reason == 'Not Modified': # HTTP 304 response
                self.bark('Watchdog is asleep!', "Watchdog webpage '%s' has not been modified within the last %g minutes."%(self.url,self.lastup/60.))
                return

            if is_web_connected(): self.bark('Watchdog is dead!', "Unable to connect to watchdog webpage '%s': %s"%(self.url, str(e.reason)))
            else:
                msg = "Web Watchdog has no network connection."
                if self.checkin: self.bark("Webdog check-in FAIL!", msg)
                else: print(msg)

def wdParser():
    parser = OptionParser()
    parser.add_option("--url",      help="page url")
    parser.add_option("--checkin",  action="store_true", help="send report whether or not there are errors")
    parser.add_option("--lastup",   type=float, help="check time since last page updage [seconds]")
    parser.add_option("--mailto",   help="email notifications to this address")
    parser.add_option("--mailfrom", help="email notifications from this address")
    parser.add_option("--loop",     type=float, help="repeat checks every [n] minutes")
    parser.add_option("--smtp",     help="email smtp server address")
    parser.add_option("--smtpu",    help="smtp server username")
    parser.add_option("--nopop",    action="store_true", help="never use pop-up dialog (headless emailer)")
    parser.add_option("--tquiet",   type=float, help="suppress repeated warnings for [n] minutes")
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
