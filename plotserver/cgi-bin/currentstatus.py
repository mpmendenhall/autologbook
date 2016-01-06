#!/usr/bin/python3
# stateless view of current reading values

from WebpageUtils import *
import xmlrpc.client
import time

class WebChecklist:
    
    def get_readings(self):
        s = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
        self.readings = s.newest()
    
    def makeChecklistTable(self):
        t0 = time.time()
        trows = [{"class":"tblhead", "data":["Device","Value","Unit","Last updated"]},]

        rlist = list(self.readings.keys())
        rlist.sort()
        for i in rlist:
            rdat = [ self.readings[i]["name"], self.readings[i]["val"], self.readings[i]["units"], "---", '<a href="/cgi-bin/plottrace.py?rid=%s">plot</a>'%i]
            cls = "good"
            vt = self.readings[i]["time"]
            if vt is not None:
                rdat[3] = timeWriter(t0-vt)+" ago"
            else:
                cls = "unknown"
            trows.append({"class":cls, "data":rdat})

        return makeTable(trows)
        
    def makePage(self):
        self.get_readings()
        tbl = self.makeChecklistTable()
                    
        print(pageHeader("Readings Monitor", refresh=300))
        print('<h1>Readings as of %s</h1>'%time.asctime())
        print(tbl)
        print(pageFooter())
        

if __name__=="__main__":
    WC = WebChecklist()
    WC.makePage()    
