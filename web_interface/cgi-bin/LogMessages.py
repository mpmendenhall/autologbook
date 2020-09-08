#!/usr/bin/python3
## \file LogMessages.py stateless view of recent log messages

from WebpageUtils import *
from AutologbookConfig import *
import xmlrpc.client
import time
import cgi

class LogMessagesDisplay:

    def classify_row(self,r):
        """Determine special marking class for row"""
        if "ERROR" in r[2].upper(): return "error"
        if "WARNING" in r[2].upper() or "on timeout" in r[2]: return "warning"
        return None

    def makeMessageTable(self,groupid=None):
        self.t0 = time.time()
        try:
            s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_DB_host,log_xmlrpc_port), allow_none=True)
            if groupid is None:
                self.messages = s.messages(self.t0 - 48*3600, self.t0 + 1e7, 2000)
                if len(self.messages) < 30: self.messages = s.messages(0, self.t0 + 1e7, 30)
                self.groups = {r[0]: r[1:] for r in s.readtypes()}
            else:
                self.messages = s.messages(self.t0 - 1e7, self.t0 + 1e7, 400, groupid)
                self.groups = {groupid: s.readout_info(groupid)}
        except:
            self.groups = {0: ["Error","Connection error"]}
            self.messages = [[time.time(), 0, "Error: no connection to log data server %s:%i."%(log_DB_host, log_xmlrpc_port)]]

        trows = [makeTable([["time","source","message"]], T="thead"),]

        prevdate = time.strftime("%A, %B %d",time.localtime(time.time()))
        for m in self.messages:
            m[2] = m[2] if m[2] else ""
            newdate = time.strftime("%A, %B %d",time.localtime(m[0]))
            if newdate != prevdate: trows.append([(prevdate,{"class":"listbreak", "colspan":"3"})])
            prevdate = newdate

            slink = makeLink("/cgi-bin/LogMessages.py?groupid=%i"%m[1], self.groups[m[1]][0]) if m[1] is not None else "---"
            row = [time.strftime("%H:%M:%S",time.localtime(m[0])), slink, m[2]]

            rclass = self.classify_row(row)
            if rclass == "squelch": continue
            if rclass: trows.append((row,{"class":rclass}))
            else: trows.append(row)
        return makeTable(trows)

    def makePage(self, groupid=None):
        if groupid is not None: groupid = int(groupid)

        P,b = makePageStructure("Autologbook messages", refresh=300)
        addTag(b,"h1",contents=["Messages as of %s"%time.asctime(), makeLink("/index.html","[Home]")])
        mtable = self.makeMessageTable(groupid)
        if groupid is not None:
            addTag(b,"h2",contents=["from %s: %s"%tuple(self.groups[groupid][:2]), makeLink("/cgi-bin/LogMessages.py","[show all]")])
        b.append(mtable)
        print(docHeaderString())
        print(prettystring(P))

if __name__=="__main__":
    form = cgi.FieldStorage()
    groupid = form.getvalue("groupid", None)
    LogMessagesDisplay().makePage(groupid)
