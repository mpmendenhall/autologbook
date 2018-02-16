#!/usr/bin/python3

from WebpageUtils import *
import cgi
from DAQ_Network_Config import *
import xmlrpc.client

if __name__=="__main__":

    form = cgi.FieldStorage()
    splots = []
    for p in form.getlist("rid"):
        try: splots.append(int(p))
        except: pass

    urlargs = ["rid=%i"%p for p in splots]
    for a in ["min","max","t0","dt"]:
        try: urlargs.append(a+"=%g"%float(form.getvalue(a)))
        except: pass
    if "xtime" in form: urlargs.append("xtime=y")
    if "nokey" in form: urlargs.append("nokey=y")
    urlargs = "&".join(urlargs)

    P,b = makePageStructure("DAQ Plot Builder")
    addTag(b, "h1", contents=["Plot Builder", makeLink("/index.html","[Home]")])
    g = addTag(b, 'figure', {"style":"display:inline-block"})
    addTag(g, "img", {"class":"lightbg", "width":"600", "height":"480", "src":"/cgi-bin/plottrace.py?img=y&"+urlargs, "alt":"PROSPECT data plot"})
    addTag(g, "figcaption", {}, makeLink("/cgi-bin/plottrace.py?"+urlargs, "customized plot link"))
    F = addTag(b, 'form', {"action":"/cgi-bin/plotbuilder.py", "method":"POST"})

    sp = addTag(F, 'select', {"name":"rid", "size":"20", "multiple":''})
    try:
        s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_xmlrpc_host,log_xmlrpc_port), allow_none=True)
        rtypes = {r[0]: r[1:] for r in s.readtypes()}
        readgroups = {r[0]: tuple(r[1:]) for r in s.readgroups()}
        rlist = [((rtypes[r][0], readgroups[rtypes[r][-1]][0]), (r, rtypes[r])) for r in rtypes]
        rlist.sort()
        for r in rlist:
            attrs = {"value":str(r[1][0])}
            if r[1][0] in splots: attrs["selected"]=""
            addTag(sp, 'option', attrs, r[0][1]+": "+r[1][1][0])
    except: pass

    FS1 = addTag(F, 'fieldset', {"style":"display:inline-block;vertical-align:top;text-align:right"})

    addTag(FS1,"label",{"for":"dt"},"t range [h]:")
    addTag(FS1,"input",{"name":"dt", "size":"5", "id":"dt", "value":form.getvalue("dt","12")})
    addTag(FS1,"br")
    addTag(FS1,"label",{"for":"t0"},"t offset [h]:")
    addTag(FS1,"input",{"name":"t0", "size":"5", "id":"t0", "value":form.getvalue("t0","")})
    addTag(FS1,"br")

    addTag(FS1,"label",{"for":"min"},"y min:")
    addTag(FS1,"input",{"name":"min", "size":"5", "id":"min", "value":form.getvalue("min","")})
    addTag(FS1,"br")
    addTag(FS1,"label",{"for":"max"},"y max:")
    addTag(FS1,"input",{"name":"max", "size":"5", "id":"max", "value":form.getvalue("max","")})
    addTag(FS1,"br")

    attrs = {"type":"checkbox", "name":"nokey", "id":"nokey", "value":"nokey"}
    if "nokey" in form: attrs["checked"]=""
    addTag(FS1,"label",{"for":"nokey"}, "suppress legend")
    addTag(FS1,"input",attrs)
    addTag(FS1,"br")

    attrs = {"type":"checkbox", "name":"xtime", "id":"xtime", "value":"xtime"}
    if "xtime" in form: attrs["checked"]=""
    addTag(FS1,"label",{"for":"xtime"}, "absolute time axis")
    addTag(FS1,"input",attrs)
    addTag(FS1,"br")

    addTag(FS1,"input",{"type":"submit","name":"submit","value":"Update Plots"})

    print(docHeaderString())
    print(prettystring(P))
