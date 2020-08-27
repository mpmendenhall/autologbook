#!/usr/bin/python3
## \file PlotUtils.py Utility wrapper to gnuplot

import sys
import time
import gzip
from io import BytesIO
from subprocess import Popen, PIPE, STDOUT
import traceback
import numpy as np
from scipy import signal
from bisect import bisect_left

keypos_opts = ["top left", "top right", "bottom left", "bottom right"]

def lin_interp(X, Y, x):
    if x <= X[0]: return Y[0]
    if x >= X[-1]: return Y[-1]
    i = bisect_left(X, x)
    l = (x-X[i-1])/(X[i] - X[i-1])
    return Y[i-1]*(1-l) + Y[i]*l

class AxisInfo:
    def __init__(self, ax):
        self.ax  = ax
        self.tic = "auto"   # axis ticks settings
        self.label = None   # axis label
        self.amin = None    # axis min; None to autoscale
        self.amax = None    # axis max; None to autoscale


class PlotMaker:
    """Wrapper for gnuplot control"""

    def __init__(self):
        self.datasets = {}      # availabale datasets, dictionary of arrays [[x,y], ...]
        self.x_txs = {}         # plot transform functions on x axis
        self.y_txs = {}         # plot transform functions on y axis
        self.plotsty = {}       # plot style commands for each trace

        self.xAx = AxisInfo("x")
        self.yAx = AxisInfo("y")
        self.yAx2 = AxisInfo("y2")

        self.title = None       # top-of-graph title
        self.keypos = None      # whether to generate graph key, and where e.g. "left top"
        self.xtime = None       # format x axis as time
        self.smooth = None

        self.gpt = None


    def resample_matched(self, xs, rids):
        """Re-sampled datasets matching xs array -> [[y0,y1,y2], ...] """
        a = np.empty((len(xs), len(rids)))
        for i,r in enumerate(rids):
            X = self.datasets[r][:,0]
            Y = self.datasets[r][:,1]
            a[:,i] = [lin_interp(X,Y,x) for x in xs]
        return a

    def synth_data(self, r, rids, f):
        """Synthesize data r from f(resampled rids data)"""
        if len(rids) == 1:
            self.datasets[r] = np.array([[p[0], f(p[1])] for p in self.datasets[rids[0]]])
        else:
            xs = self.datasets[rids[0]][:,0]
            m = self.resample_matched(xs, rids)
            self.datasets[r] = np.array([[xs[n], f(p)] for (n,p) in enumerate(m)])

    def gwrite(self, s):
        """write string to gnuplot input"""
        self.gpt.stdin.write(bytes(s, 'UTF-8'))

    def pass_gnuplot_data(self,k):
        """Pass data to gnuplot for keys in k"""
        k = [p for p in k if p in self.datasets]
        if not len(k):
            self.gwrite('plot 0 title "no data"\n')
            time.sleep(0.01)
            return False

        self.gwrite("plot")

        pstr = []
        for p in k:
            pstr.append('"-" using 1:2 title "%s: %g" %s'%(self.channels[p]["rename"], self.datasets[p][-1][1], self.plotsty.get(p,'')))
            if self.channels[p].get("yax", 1) == 2: pstr[-1] += " axes x1y2"
        self.gwrite(', '.join(pstr)+'\n')
        time.sleep(0.01)

        for p in k:
            xtx = self.x_txs.get(p,(lambda x: x))
            ytx = self.y_txs.get(p,(lambda y: y))

            ys = self.datasets[p][:,1]
            if self.smooth and self.smooth > 1:
                b, a = signal.butter(1, 1./self.smooth)
                ys = signal.filtfilt(b, a, ys)

            for n,d in enumerate(self.datasets[p]):
                x,y = xtx(d[0]), ytx(ys[n])
                if x is not None and y is not None: self.gwrite("%f\t%f\n"%(x,y))
            self.gwrite("e\n")
            self.gpt.stdin.flush()
            time.sleep(0.01)
        self.gpt.stdin.flush()
        time.sleep(0.1)

        return True

    def set_axis(self, ax):
        if ax.amin is not None or ax.amax is not None:
            self.gwrite("set %srange [%s:%s]\n"%(ax.ax,
                                                 str(ax.amin) if ax.amin is not None else "",
                                                 str(ax.amax) if ax.amax is not None else ""))
        self.gwrite("set %stic %s\n"%(ax.ax, ax.tic))
        self.gwrite('set %slabel "%s"\n'%(ax.ax, ax.label if ax.label else ''))

    def setup_axes(self):
        """Axis set-up commands"""

        self.gwrite("set autoscale\n")
        self.gwrite("unset label\n")

        self.set_axis(self.xAx)
        self.set_axis(self.yAx)
        if self.yAx2.label: self.set_axis(self.yAx2)

        if self.title: self.gwrite('set title "%s"\n'%self.title)
        if self.xtime:
            self.gwrite('set xdata time\n')
            self.gwrite('set timefmt "%s"\n')
            self.gwrite('set format x "%s"\n'%self.xtime)
        if self.keypos in keypos_opts: self.gwrite("set key on %s\n"%self.keypos)

    def make_txt(self, ds):
        """Text table dump"""
        print(ds)
        s = ""
        for p in ds:
            s += "# '%s'\t'%s'\n"%(self.xAx.label if self.xAx.label else 'x', self.channels[p]["rename"])
            if p not in self.datasets:
                s += "\n"
                continue
            xtx = self.x_txs.get(p,(lambda x: x))
            ytx = self.y_txs.get(p,(lambda y: y))
            for d in self.datasets[p]:
                x,y = xtx(d[0]), ytx(d[1])
                if x is not None and y is not None: s += "%f\t%f\n"%(xtx(d[0]), ytx(d[1]))
            s += "\n"
        return s

    def _make_x(self, terminal, ds, xcmds=""):
        """Generate and return plot data for given terminal command"""
        with Popen(["gnuplot", ],  stdin=PIPE, stdout=PIPE, stderr=STDOUT) as self.gpt:
            self.gwrite(terminal + "\n")
            self.setup_axes()
            self.gwrite(xcmds)

            self.pass_gnuplot_data(ds)
            return self.gpt.communicate()[0]

    def make_svg(self, ds, xcmds=""):
        """Generate and return SVG plot"""
        pstr = self._make_x("set terminal svg enhanced", ds, xcmds).decode("utf-8")
        pstr = pstr.replace("\n",'').replace('\t','') # strip internal whitespace
        pstr = pstr[pstr.find("<"):] # skip to start of XML, in case of junk warnings
        return mangle_xlink_namespace(pstr).replace('Ω',"&#937;").replace('μ',"&#956;")

    def make_pdf(self, ds, xcmds=""):
        """Generate and return PDF binary data"""
        return self._make_x("set terminal pdf enhanced size 5in,4in", ds, xcmds)

    def make_png(self, ds, xcmds=""):
        """Generate and return .png bitmap"""
        return self._make_x("set terminal png transparent enhanced", ds, xcmds)

    def make_gif(self, ds, xcmds=""):
        """Generate and return .png bitmap"""
        return self._make_x("set terminal gif transparent enhanced", ds, xcmds)

    def make_dump(self, fmt="svg", ds=None, xcmds="", headers=True):
        """Dump with headers to stdout for HTTP requests"""
        if ds is None: ds = self.datasets.keys()

        if fmt == "txt":
            if headers: sys.stdout.buffer.write(b'Content-Type: text/plain;charset=UTF-8\n\n')
            sys.stdout.buffer.write(self.make_txt(ds).encode("utf-8"))
        elif fmt == "pdf":
            if headers: sys.stdout.buffer.write(b"Content-Type: application/pdf\n\n")
            sys.stdout.buffer.write(self.make_pdf(ds, xcmds))
        elif fmt == "png":
            if headers: sys.stdout.buffer.write(b'Content-Type: image/png\n\n')
            sys.stdout.buffer.write(self.make_png(ds, xcmds))
        elif fmt == "gif":
            if headers: sys.stdout.buffer.write(b'Content-Type: image/gif\n\n')
            sys.stdout.buffer.write(self.make_gif(ds, xcmds))
        elif fmt == "svgz":
            if headers: sys.stdout.buffer.write(b'Content-Type: image/svg+xml\nContent-Encoding: gzip\n\n')
            with gzip.GzipFile(filename="plot.svgz", mode='wb', fileobj=sys.stdout.buffer) as gzip_obj:
                gzip_obj.write(self.make_svg(ds, xcmds).encode())
        else:
            if headers: print('Content-Type: image/svg+xml\n')
            print(self.make_svg(ds, xcmds))


def mangle_xlink_namespace(s):
    """Necessary at one point... maybe not now"""
    return s
    #return s.replace("xmlns:","xFOO").replace("xlink:","xBAZ")

def unmangle_xlink_namespace(s):
    """Necessary at one point... maybe not now"""
    return s
    #return s.replace("xFOO","xmlns:").replace("xBAZ","xlink:")
