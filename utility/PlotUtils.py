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

keypos_opts = ["top left", "top right", "bottom left", "bottom right"]

class PlotMaker:
    """Wrapper for gnuplot control"""

    def __init__(self):
        self.renames = {}       # graph title re-naming
        self.datasets = {}      # availabale datasets, dictionary of ((x,y),...) points
        self.x_txs = {}         # plot transform functions on x axis
        self.y_txs = {}         # plot transform functions on y axis
        self.plotsty = {}       # plot style commands for each trace

        self.title = None       # top-of-graph title
        self.xlabel = None      # x axis label
        self.xtic = "auto"      # x axis tick settings
        self.ylabel = None      # y axis label
        self.ytic = "auto"      # y axis tick settings
        self.ymin = None        # y axis minimum; None to autoscale
        self.ymax = None        # y axis maximum; None to autoscale
        self.keypos = None      # whether to generate graph key, and where e.g. "left top"
        self.xtime = None       # format x axis as time
        self.smooth = None

        self.gpt = None

    def gwrite(self, s):
        """write string to gnuplot input"""
        self.gpt.stdin.write(bytes(s, 'UTF-8'))

    def pass_gnuplot_data(self,k):
        """Pass data to gnuplot for keys in k"""
        k = [p for p in k if self.datasets.get(p,None)]
        if not len(k):
            self.gwrite('plot 0 title "no data"\n')
            time.sleep(0.01)
            return False

        self.gwrite("plot")
        pstr = ', '.join(['"-" using 1:2 title "" %s'%self.plotsty.get(p,'') for p in k])
        if self.keypos in keypos_opts:
            pstr = ', '.join(['"-" using 1:2 title "%s: %g" %s'%(self.renames.get(p,p), self.datasets[p][-1][1], self.plotsty.get(p,'')) for p in k])
        self.gwrite(pstr+'\n')
        time.sleep(0.01)

        for p in k:
            xtx = self.x_txs.get(p,(lambda x: x))
            ytx = self.y_txs.get(p,(lambda y: y))

            ys = np.array([d[1] for d in self.datasets[p]])
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

    def setup_axes(self):
        """Axis set-up commands"""
        self.gwrite("set autoscale\n")
        if self.ymin is not None or self.ymax is not None:
            self.gwrite("set yrange [%s:%s]\n"%(str(self.ymin) if self.ymin is not None else "", str(self.ymax) if self.ymax is not None else ""))
        self.gwrite("set xtic %s\n"%self.xtic)
        self.gwrite("set ytic %s\n"%self.ytic)
        self.gwrite("unset label\n")
        if self.title: self.gwrite('set title "%s"\n'%self.title)
        self.gwrite('set xlabel "%s"\n'%(self.xlabel if self.xlabel else ''))
        self.gwrite('set ylabel "%s"\n'%(self.ylabel if self.ylabel else ''))
        if self.xtime:
            self.gwrite('set xdata time\n')
            self.gwrite('set timefmt "%s"\n')
            self.gwrite('set format x "%s"\n'%self.xtime)
        if self.keypos in keypos_opts: self.gwrite("set key on %s\n"%self.keypos)

    def make_txt(self, ds=None):
        """Text table dump"""
        if not ds: ds = self.datasets.keys()
        k = [p for p in ds if self.datasets.get(p,None)]

        s = ""
        for p in k:
            s += "# '%s'\t'%s'\n"%(self.xlabel if self.xlabel else 'x', self.renames.get(p,p))
            xtx = self.x_txs.get(p,(lambda x: x))
            ytx = self.y_txs.get(p,(lambda y: y))
            for d in self.datasets[p]:
                x,y = xtx(d[0]), ytx(d[1])
                if x is not None and y is not None: s += "%f\t%f\n"%(xtx(d[0]), ytx(d[1]))
            s += "\n"
        return s

    def _make_x(self, terminal, ds=None, xcmds=""):
        """Generate and return plot data for given terminal command"""
        with Popen(["gnuplot", ],  stdin=PIPE, stdout=PIPE, stderr=STDOUT) as self.gpt:
            self.gwrite(terminal + "\n")
            self.setup_axes()
            self.gwrite(xcmds)

            self.pass_gnuplot_data(ds)
            return self.gpt.communicate()[0]

    def make_svg(self, ds=None, xcmds=""):
        """Generate and return SVG plot"""
        pstr = self._make_x("set terminal svg enhanced", ds, xcmds).decode("utf-8")
        pstr = pstr.replace("\n",'').replace('\t','') # strip internal whitespace
        pstr = pstr[pstr.find("<"):] # skip to start of XML, in case of junk warnings
        return mangle_xlink_namespace(pstr).replace('Ω',"&#937;").replace('μ',"&#956;")

    def make_pdf(self, ds=None, xcmds=""):
        """Generate and return PDF binary data"""
        return self._make_x("set terminal pdf enhanced size 5in,4in", ds, xcmds)

    def make_png(self, ds=None, xcmds=""):
        """Generate and return .png bitmap"""
        return self._make_x("set terminal png transparent enhanced", ds, xcmds)

    def make_gif(self, ds=None, xcmds=""):
        """Generate and return .png bitmap"""
        return self._make_x("set terminal gif transparent enhanced", ds, xcmds)

    def make_dump(self, fmt="svg", ds=None, xcmds="", headers=True):
        """Dump with headers to stdout for HTTP requests"""
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
