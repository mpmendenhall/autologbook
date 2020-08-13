#!/usr/bin/python3

# gpt: gnuplot pipe
# plots: dictionary of x,y points

import time
from subprocess import Popen, PIPE, STDOUT
import sys
from io import BytesIO
import gzip

def pwrite(p,s):
    """encode string as bytes for write to pipe"""
    p.stdin.write(bytes(s, 'UTF-8'))

keypos_opts = ["top left", "top right", "bottom left", "bottom right"]

class PlotMaker:
    """Wrapper for gnuplot control"""

    def __init__(self):
        self.renames = {}       # graph title re-naming
        self.datasets = {}      # availabale datasets
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

    def pass_gnuplot_data(self,k,gpt):
        """Pass data to gnuplot for keys in k"""
        k = [p for p in k if self.datasets.get(p,None)]
        if not len(k):
            pwrite(gpt,'plot 0 title "no data"\n')
            time.sleep(0.01)
            return False
        pwrite(gpt,"plot")
        pstr = ', '.join(['"-" using 1:2 title "" %s'%self.plotsty.get(p,'') for p in k])
        if self.keypos in keypos_opts:
            pstr = ', '.join(['"-" using 1:2 title "%s: %g" %s'%(self.renames.get(p,p), self.datasets[p][-1][1], self.plotsty.get(p,'')) for p in k])
        pwrite(gpt,pstr+'\n')
        time.sleep(0.01)

        for p in k:
            xtx = self.x_txs.get(p,(lambda x: x))
            ytx = self.y_txs.get(p,(lambda y: y))
            for d in self.datasets[p]:
                x,y = xtx(d[0]), ytx(d[1])
                if x is not None and y is not None: pwrite(gpt,"%f\t%f\n"%(xtx(d[0]), ytx(d[1])))
            pwrite(gpt,"e\n")
            gpt.stdin.flush()
            time.sleep(0.01)
        gpt.stdin.flush()
        time.sleep(0.1)

        return True

    def setup_axes(self,gpt):
        """Axis set-up commands"""
        pwrite(gpt,"set autoscale\n")
        if self.ymin is not None or self.ymax is not None:
            pwrite(gpt,"set yrange [%s:%s]\n"%(str(self.ymin) if self.ymin is not None else "", str(self.ymax) if self.ymax is not None else ""))
        pwrite(gpt,"set xtic %s\n"%self.xtic)
        pwrite(gpt,"set ytic %s\n"%self.ytic)
        pwrite(gpt,"unset label\n")
        if self.title: pwrite(gpt,'set title "%s"\n'%self.title)
        pwrite(gpt,'set xlabel "%s"\n'%(self.xlabel if self.xlabel else ''))
        pwrite(gpt,'set ylabel "%s"\n'%(self.ylabel if self.ylabel else ''))
        if self.xtime:
            pwrite(gpt,'set xdata time\n')
            pwrite(gpt,'set timefmt "%s"\n')
            pwrite(gpt,'set format x "%s"\n'%self.xtime)
        if self.keypos in keypos_opts: pwrite(gpt,"set key on %s\n"%self.keypos)

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
        with Popen(["gnuplot", ],  stdin=PIPE, stdout=PIPE, stderr=STDOUT) as gpt:
            pwrite(gpt, terminal + "\n")
            self.setup_axes(gpt)
            pwrite(gpt,xcmds)

            self.pass_gnuplot_data(ds, gpt)
            return gpt.communicate()[0]

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
            if headers: print('Content-Type: text/plain\n')
            print(self.make_txt(ds))
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
