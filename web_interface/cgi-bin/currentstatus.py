#!/usr/bin/python3
# stateless view of current reading values

from WebpageUtils import *
from AutologbookConfig import *
import xmlrpc.client
import time
import cgi

class WebChecklist:
    def __init__(self, grp = None):
        self.grp = grp
        self.rtypes = {} # id: (name, descrip, units)
        self.readings = {}

    def get_readings(self):
        """Load newest readings for all items"""
        s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_DB_host, log_xmlrpc_port), allow_none=True)
        self.rtypes = {r[0]: r[1:] for r in s.readtypes(self.grp)}
        self.readings = {r[0]: r[1:] for r in s.newest([t for t,v in self.rtypes.items() if '/' in v[0]])}

    def makeChecklistTable(self):
        """Generate display table of readings"""
        t0 = time.time()
        trows = [makeTable([["Readout","Value","Unit","Last updated"]], T="thead"),]

        rlist = [(v, r) for r,v in self.rtypes.items() if '/' in v[0]] # ((name,descrip,units), id)
        rlist.sort() # sort by name

        for rinfo,rid in rlist:
            tv = self.readings.get(rid, [None, "???"])
            try: tv[1] = "%.4g"%tv[1]
            except: pass

            varname = rinfo[0]
            #if self.grp is None:
            #    gid = r[1][-1]
            #    varname = [makeLink("/cgi-bin/currentstatus.py?groupid=%i"%gid, self.readgroups[gid][0]+":"),varname]

            rdat = [varname, tv[1], rinfo[2], "---", makeLink("/cgi-bin/plottrace.py?rid=%i"%rid, "plot")]
            cls = "good"
            if tv[0] is not None:
                dt = t0-tv[0]
                rdat[3] = timeWriter(dt)+" ago"
                if dt > 120: cls = "unknown"
            else: cls = "unknown"
            trows.append((rdat,{"class":cls}))

        return makeTable(trows)

    def makePage(self):
        self.get_readings()

        P,b = makePageStructure("Readings Monitor", refresh=300)
        addTag(b,"h1",contents=["Readings as of %s"%time.asctime(), makeLink("/index.html","[Home]")])

        #if self.grpid is not None:
        #    addTag(b,"h2",contents=["from %s: %s"%self.readgroups.get(self.grpid, ("?","?")), makeLink("/cgi-bin/currentstatus.py","[show all]")])

        b.append(self.makeChecklistTable())

        print(docHeaderString())
        print(prettystring(P))

if __name__=="__main__":
    form = cgi.FieldStorage()
    try: group = int(form.getvalue("group", None))
    except: group = None
    WC = WebChecklist(group)
    WC.makePage()
