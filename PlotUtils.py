#!/usr/bin/python3

# gpt: gnuplot pipe
# plots: dictionary of x,y points

import time
from subprocess import *

def pwrite(p,s):
    """encode string as bytes for write to pipe"""
    p.stdin.write(bytes(s, 'UTF-8'))
    
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
        self.keypos = None      # whether to generate graph key, and where e.g. "left top"
        
    def pass_gnuplot_data(self,k,gpt):
        """Pass data to gnuplot for keys in k"""
        k = [p for p in k if self.datasets.get(p,None)]
        if not len(k):
            print("No data to plot!")
            return False
        pwrite(gpt,"plot")
        pstr = ', '.join(['"-" title "" %s'%self.plotsty.get(p,'') for p in k])
        if self.keypos:
            pstr = ', '.join(['"-" title "%s: %g" %s'%(self.renames.get(p,p), self.datasets[p][-1][1], self.plotsty.get(p,'')) for p in k])
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
        pwrite(gpt,"set xtic %s\n"%self.xtic)
        pwrite(gpt,"set ytic %s\n"%self.ytic)
        pwrite(gpt,"unset label\n")
        if self.title: pwrite(gpt,'set title "%s"\n'%self.title)
        pwrite(gpt,'set xlabel "%s"\n'%(self.xlabel if self.xlabel else ''))
        pwrite(gpt,'set ylabel "%s"\n'%(self.ylabel if self.ylabel else ''))
        if self.keypos: pwrite(gpt,"set key on %s\n"%self.keypos)
  
    def make_svg(self,ds=None,xcmds=""):
        """Generate and return SVG plot"""
        if not ds: ds = self.datasets.keys()
        
        with Popen(["gnuplot", ],  stdin=PIPE, stdout=PIPE, stderr=STDOUT) as gpt:
            pwrite(gpt,"set terminal svg enhanced background rgb 'white'\n")
            self.setup_axes(gpt)
            pwrite(gpt,xcmds)
            
            for k in ds: self.pass_gnuplot_data(["trace"], gpt)
            
            pstr = gpt.communicate()[0].decode("utf-8").replace("\n",'').replace('\t','') # strip internal whitespace
            pstr = pstr[pstr.find("<"):] # skip to start of XML, in case of junk warnings
            return mangle_xlink_namespace(pstr)
                
def mangle_xlink_namespace(s):
    """Necessary at one point... maybe not now"""
    return s
    #return s.replace("xmlns:","xFOO").replace("xlink:","xBAZ")

def unmangle_xlink_namespace(s):
    """Necessary at one point... maybe not now"""
    return s
    #return s.replace("xFOO","xmlns:").replace("xBAZ","xlink:")
