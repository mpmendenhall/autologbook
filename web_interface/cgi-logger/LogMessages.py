#!/usr/bin/python3
## \file LogMessages.py stateless view of recent log messages

from WebpageUtils import *
import xmlrpc.client
import time
import cgi

class LogMessagesDisplay:

    def classify_row(self,r):
        """Determine special marking class for row"""
        if "ERROR" in r[2]: return "error"
        if "WARNING" in r[2]: return "warning"
        return None

    def makeMessageTable(self,groupid=None):
        self.t0 = time.time()
        s = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
        self.groups = dict([(x[0], (x[1],x[2])) for x in s.readgroups()])
        if groupid is not None:
            self.messages = s.messages(self.t0 - 1e7, self.t0 + 1e7, 400, groupid)
        else:
            self.messages = s.messages(self.t0 - 48*3600, self.t0 + 1e7)

        trows = [(["time","source","message"], {"class":"tblhead"}),]
        for m in self.messages:
            m[2] = m[2] if m[2] else ""
            row = [time.ctime(m[0]), makeLink("/cgi-logger/LogMessages.py?groupid=%i"%m[1], self.groups[m[1]][0]) if m[1] is not None else "---", m[2]]
            rclass = self.classify_row(row)
            if rclass: trows.append((row,{"class":rclass}))
            else: trows.append(row)
        return makeTable(trows)

    def makePage(self, groupid=None):
        P,b = makePageStructure("Autologbook messages", refresh=300)
        addTag(b,"h1",contents="Messages as of %s"%time.asctime())
        mtable = self.makeMessageTable(groupid)
        try: addTag(b,"h2",contents=["from %s: %s"%self.groups[int(groupid)],makeLink("/cgi-logger/LogMessages.py","[show all]")])
        except: pass
        b.append(mtable)
        print(docHeaderString())
        print(prettystring(P))

if __name__=="__main__":
    form = cgi.FieldStorage()
    groupid = form.getvalue("groupid", None)
    LogMessagesDisplay().makePage(groupid)
