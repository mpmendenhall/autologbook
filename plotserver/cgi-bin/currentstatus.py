#!/usr/bin/python3
# stateless view of current reading values

from WebpageUtils import *
import xmlrpc.client
import time
import cgi

class WebChecklist:
    
    def get_readings(self):
        s = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
        self.readings = s.newest()
    
    def makeChecklistTable(self):
        t0 = time.time()
        trows = [{"class":"tblhead", "data":["Device","Value","Unit","Last updated"]},]
        
        rlist = [(r["name"], r) for r in self.readings]
        rlist.sort()
        for r in [x[1] for x in rlist]:
            rdat = [cgi.escape(r["name"]),
                    r["val"],
                    r["units"],
                    "---", makeLink("/cgi-bin/plottrace.py?rid=%i"%r["rid"], "plot")]
            cls = "good"
            vt = r["time"]
            if vt is not None:
                dt = t0-vt
                rdat[3] = timeWriter(dt)+" ago"
                if dt > 120:
                   cls = "unknown" 
            else:
                cls = "unknown"
            trows.append({"class":cls, "data":rdat})

        return makeTable(trows)
        
    def makePage(self):
        self.get_readings()
        tbl = self.makeChecklistTable()
                    
        print(pageHeader("Readings Monitor", refresh=300))
        print('<h1>Readings as of %s</h1>'%time.asctime())
        print(ET.tostring(tbl).decode('ascii'))
        print(pageFooter())
        

if __name__=="__main__":
    WC = WebChecklist()
    WC.makePage()    
