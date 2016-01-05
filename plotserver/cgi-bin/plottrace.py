#!/usr/bin/python3
# stateless view of current reading values

from WebpageUtils import *
from PlotUtils import *
import xmlrpc.client
import cgi
import time
import os
from subprocess import *
    
class TracePlotter:
    def __init__(self):
        self.t0 = time.time()
        self.tm = self.t0 - 2*3600
        self.readings = {}
        
    def get_readings(self, rid):
        s = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)
        self.readings[rid] = s.datapoints(rid, self.tm, self.t0)
    
    def makePage(self, rid):
        self.get_readings(rid)
                    
        print(pageHeader("Plot of channel %i"%rid, refresh=300))
        print('<h1>Readings as of %s</h1>'%time.asctime())
        
        with Popen(["gnuplot", ],  stdin=PIPE, stdout=PIPE, stderr=STDOUT) as gpt:
        #if 1:
            gpt = Popen(["gnuplot", ],  stdin=PIPE, stdout=PIPE, stderr=STDOUT)

            pwrite(gpt,"set autoscale\n")
            pwrite(gpt,"set xtic auto\n")
            pwrite(gpt,"set ytic auto\n")
            pwrite(gpt,"unset label\n")
            pwrite(gpt,'set title "live monitor"\n')
            pwrite(gpt,'set ylabel ""\n')
            pwrite(gpt,'set xlabel "time [hours]"\n')
            pwrite(gpt,"set key on left top\n")
            pwrite(gpt,"set terminal svg enhanced background rgb 'white'\n")
        
            PM = PlotMaker()
            PM.datasets = {"trace":self.readings[rid]}
            PM.x_txs["trace"] = (lambda x, t0=self.t0: (x-t0)/3600.)
            PM.pass_gnuplot_data(["trace"], gpt)
            
            s = gpt.communicate()[0].decode("utf-8")
            s = "\n".join(s.split("\n")[3:])
            print(s)
        
        print(pageFooter())
        
        

if __name__=="__main__":
    tp = TracePlotter()
    
    form = cgi.FieldStorage()
    rid = form.getvalue("rid", None)
    if rid is not None:
        tp.makePage(int(rid))
