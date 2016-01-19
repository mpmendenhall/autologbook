#!/usr/bin/python3

# gpt: gnuplot pipe
# plots: dictionary of x,y points

import time

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
        self.with_key = False	# whether to generate graph key
        self.plotsty = {}       # plot style commands for each trace
    
    def pass_gnuplot_data(self,k,gpt):
        """Pass data to gnuplot for keys in k"""
        k = [p for p in k if self.datasets.get(p,None)]
        if not len(k):
                print("No data to plot!")
                return False
        pwrite(gpt,"plot")
        pstr = ', '.join(['"-" title "" %s'%self.plotsty.get(p,'') for p in k])
        if self.with_key:
            pstr = ', '.join(['"-" title "%s: %g" %s'%(self.renames.get(p,p), self.datasets[p][-1][1], self.plotsty.get(p,'')) for p in k])
        pwrite(gpt,pstr+'\n')
        time.sleep(0.01)
        
        for p in k:
                xtx = self.x_txs.get(p,(lambda x: x))
                ytx = self.y_txs.get(p,(lambda y: y))
                for d in self.datasets[p]:
                        pwrite(gpt,"%f\t%f\n"%(xtx(d[0]), ytx(d[1])))
                pwrite(gpt,"e\n")
                gpt.stdin.flush()
                time.sleep(0.01)
        gpt.stdin.flush()
        time.sleep(0.1)
        
        return True

def mangle_xlink_namespace(s):
    return s.replace("xmlns:","xFOO").replace("xmlns","xBAR").replace("xlink:","xBAZ")
def unmangle_xlink_namespace(s):
    return s.replace("xFOO","xmlns:").replace("xBAR","xmlns").replace("xBAZ","xlink:")
