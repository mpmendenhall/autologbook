#!/bin/env python3

from WebpageUtils import *
from AutologbookConfig import log_DB_host,log_xmlrpc_port
from PlotUtils import PlotMaker, unmangle_xlink_namespace
import xmlrpc.client
import pickle
import zlib
import cgi
import time
from datetime import datetime
import os
import sys

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
        if dt >= 48:
            self.tscale = 24*3600.
            if xt: self.xtime = "%d) %I%p"
            else: self.xlabel = 'time from present [days]'

    def get_readings(self, rids):
        s = None
        for rid in rids:
            try: rid = int(rid)
            except: continue
            if rid in self.readings: return
            if s is None: s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_DB_host,log_xmlrpc_port), allow_none=True)
            ri = s.readout_info(rid)
            if ri:
                self.channels[rid] = {"name": ri[0], "descrip": ri[1], "units": ri[2]}
                self.readings[rid] = pickle.loads(zlib.decompress(s.datapoints_compressed(rid, self.tm, self.t0, 150).data))[::-1]
                self.ids.append(rid)

    def dumpImage(self, img):
        """Generate response page"""

        # no data to plot?
        if not self.readings:
            sys.stdout.buffer.write(b'Content-Type: image/svg+xml\nContent-Encoding: gzip\n\n')
            sys.stdout.buffer.write(open("logo.svgz", "rb").read())
            return

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

        if img not in ["pdf","svg","txt","png","gif","svg"]: img = "svgz"
        self.make_dump(img, self.ids, "set xtics rotate by 35 right offset 0,-0.2\n" if self.xtime else "")

def makePage(form):
    """Single-plot webpage"""

    # scan readouts metadata
    s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_DB_host,log_xmlrpc_port), allow_none=True)
    channels = set()
    for rid in form.getlist("rid"):
        try: rid = int(rid)
        except: continue
        if rid in channels: return
        ri = s.readout_info(rid)
        if ri:
            ptitle = ri[0]+" plot"
            pheader = ri[0] + " readings as of %s"%time.asctime()
            subtitle = ri[0] + ": " + ri[1]
            channels.add(rid)

    # multi-trace plots
    if len(channels) != 1:
        ptitle = "plottrace"
        pheader = "Readings as of %s"%time.asctime()
        subtitle = ""

    args = os.environ.get('QUERY_STRING', '')

    P,b = makePageStructure(ptitle, refresh=300)
    addTag(b,"h1",contents=[pheader, makeLink("/index.html","[Home]")])
    f = addTag(b, 'figure', {"style":"display:inline-block"})
    addTag(f, 'img', {"class":"lightbg", "width":"600", "height":"480", "src":"/cgi-bin/plottrace.py?" + args + "&img=y"})
    addTag(f, 'figcaption', {}, [subtitle, makeLink("/cgi-bin/plottrace.py?" + args + "&img=pdf", "[PDF]")])
    print(docHeaderString(), unmangle_xlink_namespace(prettystring(P)))

if __name__=="__main__":

    form = cgi.FieldStorage()
    img = form.getvalue("img",None)
    if not img:
        makePage(form)
        exit(0)

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
    tp.get_readings(form.getlist("rid"))
    tp.keypos = form.getvalue("key","top left")
    tp.dumpImage(img)
