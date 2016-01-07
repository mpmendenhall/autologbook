#!/usr/bin/python3
# stateless display of HV readings for PMT array

from WebpageUtils import *
import xmlrpc.client
import time

class HVArray:
    def __init__(self, nx, ivnames):
        self.nx = nx
        self.ivnames = ivnames
    
    def get_readings(self):
        s = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
        self.readings = s.newest()
    
    def makeHVTable(self):
        t0 = time.time()
        self.get_readings()
        
        nameidx = {}
        for c in self.readings:
            nameidx[c["name"]] = c
        
        trows = []
        n = 0
        for i in self.ivnames:
            vv = nameidx[i[0]]["val"]
            ii = nameidx[i[1]]["val"]
            oo = vv/ii if ii else None
            
            if n == len(self.ivnames)/2:
                trows.append(["\u2014"]*self.nx)
            if not n%self.nx:
                trows.append([])
            n += 1
            
            pcls = "warning"
            if 1200 <= vv <= 1800 and 0.8 <= ii <= 1.0:
                pcls = "good"
            if vv <= 10 and ii <= 0.01:
                pcls = "turnedoff"
            if t0 - nameidx[i[0]]["time"] > 60 or t0 - nameidx[i[1]]["time"] > 60:
                pcls = "unknown"
            trows[-1].append(makeLink("/cgi-bin/plottrace.py?rid=%i"%nameidx[i[0]]["rid"], makeTable([["%i V"%vv],["%.2f mA"%ii],["%i k\u03a9"%oo]], {"class":pcls})))
        
        return makeTable(trows, {"style":"text-align:center"})
        
    def makePage(self):
        tbl = self.makeHVTable()
        print(pageHeader("PMT Array HV", refresh=300))
        print('<h1>PMT HV as of %s</h1>'%time.asctime())
        print(ET.tostring(tbl).decode('ascii')) # print(prettystring(tbl))
        print(pageFooter())
        

if __name__=="__main__":
    H = HVArray(4, [("V_%i"%i, "I_%i"%i) for i in range(32)])
    H.makePage()
