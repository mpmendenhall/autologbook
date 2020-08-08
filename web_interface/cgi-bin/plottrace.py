#!/bin/env python3

from WebpageUtils import *
from AutologbookConfig import *
from PlotUtils import *
import xmlrpc.client
import pickle
import zlib
import cgi
import time
import os
from datetime import datetime

class TracePlotter(PlotMaker):
    def __init__(self, dt = 12, dt0 = 0, xt = False):
        PlotMaker.__init__(self)
        self.dt0 = dt0*3600
        self.t0 = time.time() - dt0*3600
        self.tm = self.t0 - dt*3600
        self.ids = []
        self.readings = {}
        self.channels = {}
        self.keypos = "top left"
        self.tscale = 3600.
        if xt:
             self.xtime = "%H:%M"
             self.xlabel = 'time'
        else: self.xlabel = 'time from present [hours]'
        if dt > 48:
            self.tscale = 24*3600.
            if xt: self.xtime = "%d) %I%p"
            else: self.xlabel = 'time from present [days]'

    def get_readings(self, rid):
        try: rid = int(rid)
        except: return
        if rid in self.readings: return
        s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host,log_xmlrpc_port), allow_none=True)
        ri = s.readout_info(rid)
        if ri:
            self.channels[rid] = ri
            self.readings[rid] = pickle.loads(zlib.decompress(s.datapoints_compressed(rid, self.tm, self.t0, 100).data))[::-1]
            self.ids.append(rid)

    def makePage(self, img = None):
        if not self.readings:
            if img:
                print('Content-Type: text/plain\n')
                print('no plots found!')
                return
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

        self.renames = dict([(c,self.channels[c]["name"].replace("_"," ")) for c in self.channels])

        # common units?
        units = None
        self.ylabel = "readings"
        for (n,c) in self.channels.items():
            if c["units"]: self.renames[n] += " ["+c["units"]+"]"
            if units is None: units = c["units"]
            elif units != c["units"]:
                units = None
                break
        if units: self.ylabel = 'value [%s]'%units

        self.datasets = dict([(r, self.readings[r]) for r in self.readings])
        for r in self.readings:
            self.plotsty[r] = "with linespoints pt 7 ps 0.4"
            if not self.xtime: self.x_txs[r] = (lambda x, t0=self.t0+self.dt0: (x-t0)/self.tscale)
            else: self.x_txs[r] = (lambda x, dx=(datetime.now()-datetime.utcnow()).total_seconds(): x+dx)

        if img:
            if img not in ["pdf","svg","txt"]: img = "svg"
            self.make_dump(img, self.ids, "set xtics rotate by 35 right offset 0,-0.2\n" if self.xtime else "")
        else:
            pstr = self.make_svg(self.ids, "set xtics rotate by 35 right offset 0,-0.2\n" if self.xtime else "")
            P,b = makePageStructure(ptitle, refresh=300)
            addTag(b,"h1",contents=[subtitle, makeLink("/index.html","[Home]")])
            g = ET.Element('figure', {"style":"display:inline-block"})
            if chn: addTag(g,"figcaption",contents=chn["descrip"])
            if pstr: addTag(g, "div", {"class":"lightbg"}, contents=ET.fromstring(pstr))
            b.append(g)
            print(docHeaderString())
            print(unmangle_xlink_namespace(prettystring(P)))

if __name__=="__main__":

    form = cgi.FieldStorage()
    try:
        dt = abs(float(form.getvalue("dt","12")))
        if not dt < 31*24: dt = 31*24
    except: dt = 12
    try: dt0 = abs(float(form.getvalue("t0","0")))
    except: dt0 = 0
    tp = TracePlotter(dt, dt0, "xtime" in form)
    try: tp.ymin = float(form.getvalue("min",None))
    except: pass
    try: tp.ymax = float(form.getvalue("max",None))
    except: pass
    for r in form.getlist("rid"): tp.get_readings(r)
    tp.keypos = form.getvalue("key","top left")

    tp.makePage(img = form.getvalue("img",None))
