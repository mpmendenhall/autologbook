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
        self.ids = []
        self.readings = {}
        self.channels = {}

    def get_readings(self, rid):
        try: rid = int(rid)
        except: return
        if rid in self.readings: return
        s = xmlrpc.client.ServerProxy('http://localhost:8002', allow_none=True)
        ri = s.readout_info(rid)
        if ri:
            self.channels[rid] = ri
            self.readings[rid] = s.datapoints(rid, self.tm, self.t0)[::-1]
            self.ids.append(rid)

    def makePage(self):
        if not self.readings:
            P,b = makePageStructure("plotter fail!")
            addTag(b,"h1",contents="no plots found!")
            print(docHeaderString())
            print(prettystring(P))
            return

        # single or multiple plots?
        ptitle = "plottrace"
        subtitle = "readings as of %s"%time.asctime()
        chn = None
        if len(self.readings) == 1:
            chn = self.channels[self.ids[0]]
            ptitle = "%s plot"%chn["name"]
            subtitle = "%s %s"%(chn["name"], subtitle)

        # common units?
        units = None
        ylabel = "readings"
        for c in self.channels.values():
            if units is None: units = c["units"]
            elif units != c["units"]:
                units = None
                break
        if units: ylabel = 'value [%s]'%units

        P,b = makePageStructure(ptitle, refresh=300)
        addTag(b,"h1",contents=subtitle)
        if chn: addTag(b,"h2",contents=chn["descrip"])

        PM = PlotMaker()
        PM.datasets = dict([(r, self.readings[r]) for r in self.readings])
        PM.ylabel = ylabel
        PM.xlabel = 'time from present [hours]'
        PM.renames = dict([(c,self.channels[c]["name"].replace("_"," ")) for c in self.channels])
        PM.keypos = "left top"
        for r in self.readings:
            PM.plotsty[r] = "with linespoints pt 7 ps 0.4"
            PM.x_txs[r] = (lambda x, t0=self.t0: (x-t0)/3600.)
        pstr = PM.make_svg(self.ids)
        if pstr: b.append(ET.fromstring(pstr))

        print(docHeaderString())
        print(unmangle_xlink_namespace(prettystring(P)))


if __name__=="__main__":
    tp = TracePlotter()

    form = cgi.FieldStorage()
    rid = form.getvalue("rid", None)
    if type(rid) == type([]):
        for r in rid: tp.get_readings(r)
    else: tp.get_readings(rid)

    tp.makePage()
