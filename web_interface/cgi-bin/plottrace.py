#!/usr/bin/python3
# stateless plot of one reading recent history

from WebpageUtils import *
from DAQ_Network_Config import *
from PlotUtils import *
import xmlrpc.client
import pickle
import zlib
import cgi
import time
import os

class TracePlotter(PlotMaker):
    def __init__(self, dt = 12):
        PlotMaker.__init__(self)
        self.t0 = time.time()
        self.tm = self.t0 - dt*3600
        self.ids = []
        self.readings = {}
        self.channels = {}
        self.keypos = "top left"
        self.xlabel = 'time from present [hours]'

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

    def makePage(self, img = False):
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

        # common units?
        units = None
        self.ylabel = "readings"
        for c in self.channels.values():
            if units is None: units = c["units"]
            elif units != c["units"]:
                units = None
                break
        if units: self.ylabel = 'value [%s]'%units

        self.datasets = dict([(r, self.readings[r]) for r in self.readings])
        self.renames = dict([(c,self.channels[c]["name"].replace("_"," ")) for c in self.channels])
        for r in self.readings:
            self.plotsty[r] = "with linespoints pt 7 ps 0.4"
            self.x_txs[r] = (lambda x, t0=self.t0: (x-t0)/3600.)
        pstr = self.make_svg(self.ids)

        if img:
            print('Content-Type: image/svg+xml\n')
            print(pstr)
        else:
            P,b = makePageStructure(ptitle, refresh=300)
            addTag(b,"h1",contents=subtitle)
            g = ET.Element('figure', {"style":"display:inline-block"})
            if chn: addTag(g,"figcaption",contents=chn["descrip"])
            if pstr: addTag(g, "div", {"class":"lightbg"}, contents=ET.fromstring(pstr))
            b.append(g)
            print(docHeaderString())
            print(unmangle_xlink_namespace(prettystring(P)))

if __name__=="__main__":

    form = cgi.FieldStorage()
    rid = form.getvalue("rid", None)
    try:
        dt = float(form.getvalue("dt","12"))
        if not dt > 0: dt = 1
        if not dt < 48: dt = 48
    except: dt = 12
    tp = TracePlotter(dt)
    try: tp.ymin = float(form.getvalue("min",None))
    except: pass
    try: tp.ymax = float(form.getvalue("max",None))
    except: pass
    if type(rid) == type([]):
        for r in rid: tp.get_readings(r)
    else: tp.get_readings(rid)
    if "nokey" in form: tp.keypos = None

    tp.makePage(img = "img" in form)
