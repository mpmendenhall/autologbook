#!/usr/bin/python3
# stateless plot of one reading recent history

from WebpageUtils import *
from PlotUtils import *
import xmlrpc.client
import cgi
import time
import os
    
class TracePlotter:
    def __init__(self):
        self.t0 = time.time()
        self.tm = self.t0 - 12*3600
        self.readings = {}
        self.channels = {}
    
    def get_readings(self, rid):
        s = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
        ri = s.readout_info(rid)
        if ri:
            self.channels[rid] = ri
            self.readings[rid] = s.datapoints(rid, self.tm, self.t0)
    
    def makePage(self, rid):
        self.get_readings(rid)
        
        if rid not in self.channels:
            P,b = makePageStructure("plotter fail!")
            addTag(b,"h1",contents="dataset %i not found!"%rid)
            print(docHeaderString())
            print(prettystring(P))
            return
        
        chn = self.channels[rid]
        cname = chn["name"]
        
        P,b = makePageStructure("%s plot"%cname, refresh=300)
        addTag(b,"h1",contents="%s as of %s"%(cname, time.asctime()))
    
        PM = PlotMaker()
        PM.datasets = {"trace":self.readings[rid]}
        if chn["units"]: PM.ylabel = 'reading [%s]'%chn["units"]
        PM.xlabel = 'time from present [hours]'
        PM.plotsty["trace"] = "with linespoints pt 7 ps 0.4"
        PM.x_txs["trace"] = (lambda x, t0=self.t0: (x-t0)/3600.)
        pstr = PM.make_svg()
        if pstr: b.append(ET.fromstring(pstr))

        print(docHeaderString())
        print(unmangle_xlink_namespace(prettystring(P)))
        
        
if __name__=="__main__":
    tp = TracePlotter()
    
    form = cgi.FieldStorage()
    rid = form.getvalue("rid", None)
    if rid is not None:
        tp.makePage(int(rid))
