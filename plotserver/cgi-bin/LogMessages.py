#!/usr/bin/python3
# stateless view of recent log messages

from WebpageUtils import *
import xmlrpc.client
import time
import cgi

class LogMessagesDisplay:

    def makeMessageTable(self):
        s = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
        self.t0 = time.time()
        self.messages = s.messages(self.t0 - 24*3600, self.t0 + 1e7)

        trows = [{"class":"tblhead", "data":["time","source","message"]},]
        for m in self.messages:
            m[1] = cgi.escape(m[1]) if m[1] else ""
            m[2] = cgi.escape(m[2]) if m[2] else ""
            trows.append([time.ctime(m[0]), "[%s]"%m[1], m[2]])
        return makeTable(trows)
        
    def makePage(self):
        tbl = self.makeMessageTable()
        print(pageHeader("Autologbook messages", refresh=300))
        print('<h1>Messages as of %s</h1>'%time.ctime(self.t0))
        print(tbl)
        print(pageFooter())
        
if __name__=="__main__":
    LogMessagesDisplay().makePage()
