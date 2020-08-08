#!/usr/bin/python3
# stateless view of current reading values

from WebpageUtils import *
from AutologbookConfig import *
import xmlrpc.client
import time
import cgi

class WebChecklist:
    def __init__(self,grpid=None):
        self.grpid = grpid
        self.rtypes = {}
        self.readgroups = {}
        self.readings = {}

    def get_readings(self):
        s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host,log_xmlrpc_port), allow_none=True)
        self.rtypes = {r[0]: r[1:] for r in s.readtypes(self.grpid)}
        self.readgroups = {r[0]: tuple(r[1:]) for r in s.readgroups()}
        self.readings = {r[0]: r[1:] for r in s.newest([t for t in self.rtypes]) if r}

    def makeChecklistTable(self):
        t0 = time.time()
        trows = [makeTable([["Readout","Value","Unit","Last updated"]], T="thead"),]

        rlist = [((self.rtypes[r][0], None if self.grpid else self.readgroups[self.rtypes[r][-1]][0]), (r,self.rtypes[r])) for r in self.rtypes]
        rlist.sort()
        for r in [x[1] for x in rlist]:
            tv = self.readings.get(r[0], [None, "???"])
            try: tv[1] = "%.4g"%tv[1]
            except: pass

            varname = r[1][0]
            if self.grpid is None:
                gid = r[1][-1]
                varname = [makeLink("/cgi-bin/currentstatus.py?groupid=%i"%gid, self.readgroups[gid][0]+":"),varname]

            rdat = [varname, tv[1], r[1][2], "---",
                    makeLink("/cgi-bin/plottrace.py?rid=%i"%r[0], "plot")]
            cls = "good"
            if tv[0] is not None:
                dt = t0-tv[0]
                rdat[3] = timeWriter(dt)+" ago"
                if dt > 120:
                   cls = "unknown"
            else:
                cls = "unknown"
            trows.append((rdat,{"class":cls}))

        return makeTable(trows)

    def makePage(self):
        self.get_readings()

        P,b = makePageStructure("Readings Monitor", refresh=300)
        addTag(b,"h1",contents=["Readings as of %s"%time.asctime(), makeLink("/index.html","[Home]")])

        if self.grpid is not None:
            addTag(b,"h2",contents=["from %s: %s"%self.readgroups.get(self.grpid, ("?","?")), makeLink("/cgi-bin/currentstatus.py","[show all]")])

        b.append(self.makeChecklistTable())

        print(docHeaderString())
        print(prettystring(P))

if __name__=="__main__":
    form = cgi.FieldStorage()
    try: groupid = int(form.getvalue("groupid", None))
    except: groupid = None
    WC = WebChecklist(groupid)
    WC.makePage()
