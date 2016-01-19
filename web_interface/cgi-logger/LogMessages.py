#!/usr/bin/python3
# stateless view of recent log messages

from WebpageUtils import *
import xmlrpc.client
import time
import cgi

class LogMessagesDisplay:

    def makeMessageTable(self):
        s = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
        self.t0 = time.time()
        self.messages = s.messages(self.t0 - 48*3600, self.t0 + 1e7)

        trows = [(["time","source","message"], {"class":"tblhead"}),]
        for m in self.messages:
            m[1] = m[1] if m[1] else ""
            m[2] = m[2] if m[2] else ""
            trows.append([time.ctime(m[0]), "[%s]"%m[1], m[2]])
        return makeTable(trows)
        
    def makePage(self):
        P,b = makePageStructure("Autologbook messages", refresh=300)
        addTag(b,"h1",contents="Messages as of %s"%time.asctime())
        b.append(self.makeMessageTable())
        print(docHeaderString())
        print(prettystring(P))
        
if __name__=="__main__":
    LogMessagesDisplay().makePage()
