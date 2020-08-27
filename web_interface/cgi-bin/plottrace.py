#!/bin/env python3

from WebpageUtils import *
from AutologbookConfig import log_DB_host,log_xmlrpc_port
from PlotUtils import *
import xmlrpc.client
import pickle
import zlib
import cgi
import time
from datetime import datetime
import os
import sys

from sensor_defs.humidity import *
from sensor_defs.AQI import *

class TFahren:
    def __init__(self):
        self.rids = [1]
        self.name = "T"
        self.descrip = "indoor temperature"
        self.units = "deg F"
    def f(self, p):
        return 9*p/5 + 32

class AbsHum:
    def __init__(self):
        self.rids = [46,47]
        self.name = "H_abs"
        self.descrip = "absolute humidity"
        self.units = "g/m^3"

    def f(self, p):
        return RH_to_Abs_Humidity(p[1], p[0])

class Dewpt:
    def __init__(self):
        self.rids = [46,47]
        self.name = "T_d"
        self.descrip = "dewpoint"
        self.units = "deg. C"

    def f(self, p): return dewpoint(p[0], p[1])

class AQIcalc:
    def __init__(self):
        self.rids = [43,44]
        self.name = "AQI"
        self.descrip = "Air Quality Index estimate from PM2.5"
        self.units = None

    def f(self, p): return PM25_to_AQI(p[0] + p[1])

calcmodules = {"degF": TFahren, "absH": AbsHum, "dewpt": Dewpt, "AQI": AQIcalc}

class TracePlotter(PlotMaker):
    def __init__(self, dt = 12, dt0 = 0, xt = False):
        PlotMaker.__init__(self)
        self.dt0 = dt0*3600
        self.t0 = time.time() - dt0*3600
        self.tm = self.t0 - dt*3600
        self.ids = []
        self.channels = {}
        self.keypos = "top left"
        self.tscale = 3600.
        self.maxpts = 150
        if xt:
             self.xtime = "%H:%M"
             self.xAx.label = 'time'
        else: self.xAx.label = 'time from present [hours]'
        if dt >= 48:
            self.tscale = 24*3600.
            if xt: self.xtime = "%d) %I%p"
            else: self.xlabel = 'time from present [days]'

    def _get_readings(self, rids):
        """Load non-calculated readings"""
        s = None
        for rid in rids:
            if rid in self.datasets: continue
            if s is None: s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_DB_host,log_xmlrpc_port), allow_none=True)
            ri = s.readout_info(rid)
            if ri:
                self.channels[rid] = {"name": ri[0], "descrip": ri[1], "units": ri[2]}
                self.datasets[rid] = np.array(pickle.loads(zlib.decompress(s.datapoints_compressed(rid, self.tm, self.t0, self.maxpts).data))[::-1])

    def get_readings(self, rids):
        """Get readings, including interpreting calculated values"""
        xrids = []
        mods = {}
        for rid in rids:
            try:
                xrids.append(int(rid))
                self.ids.append(int(rid))
            except:
                if rid in calcmodules:
                    mods[rid] = calcmodules[rid]()
                    xrids += mods[rid].rids
        self._get_readings(xrids)

        for n,m in mods.items():
            self.channels[n] = {"name": m.name, "descrip": m.descrip, "units": m.units}
            self.ids.append(n)
            self.synth_data(n, m.rids, m.f)

    def dumpImage(self, img):
        """Generate response page"""

        # no data to plot?
        if not self.datasets:
            sys.stdout.buffer.write(b'Content-Type: image/svg+xml\nContent-Encoding: gzip\n\n')
            sys.stdout.buffer.write(open("logo.svgz", "rb").read())
            return

        # channel renaming with units
        for c in self.channels.values():
            c["rename"] = c["name"].replace("_"," ")
            if c["units"]: c["rename"] += " ["+c["units"]+"]"

        # identify common units between entries; label and assign axes
        units = tuple(set([self.channels[i]["units"] for i in self.ids]))
        self.yAx.label = "readings"
        if len(units) in (1,2) and units[0]:
            self.yAx.label = 'value [%s]'%units[0]
        if len(units) == 2:
            self.yAx2.label = 'value [%s]'%units[1] if units[1] else 'readings'
            for c in self.channels.values():
                if c["units"] == units[1]: c["yax"] = 2

        for r in self.ids:
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
    addTag(f, 'img', {"class":"lightbg", "width":"750", "height":"600", "src":"/cgi-bin/plottrace.py?" + args + "&img=y"})
    addTag(f, 'figcaption', {}, [subtitle,
                                 makeLink("/cgi-bin/plottrace.py?" + args + "&img=pdf", "[PDF]"),
                                 makeLink("/cgi-bin/plottrace.py?" + args + "&img=txt", "[txt]")])
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
    try: tp.yAx.amin = float(form.getvalue("min",None))
    except: pass
    try: tp.yAx.amax = float(form.getvalue("max",None))
    except: pass
    try: tp.yAx2.amin = float(form.getvalue("min2",None))
    except: pass
    try: tp.yAx2.amax = float(form.getvalue("max2",None))
    except: pass

    try:
        tp.smooth = float(form.getvalue("smooth",None))
        tp.smooth = min(max(tp.smooth, 1), 20)
    except: pass
    try:
        tp.maxpts = int(form.getvalue("nmax",None))
        tp.maxpts = min(500, tp.maxpts)
    except: pass
    tp.get_readings(form.getlist("rid"))
    tp.keypos = form.getvalue("key","top left")
    tp.dumpImage(img)
