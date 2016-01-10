#!/usr/bin/python3

from WebpageUtils import *
from configDBcontrol import *
import time
import cgi


class Metaform(ConfigDB):
    """Form-generating web form"""
    
    def __init__(self, conn = None):
        ConfigDB.__init__(self,conn)
        self.readonly = False
        self.prevobjs = set()   # previously-seen objects to avoid circularity
        self.dbcache = {}		# cache of top-level DB entries

    def load_toplevel(self, csid):
        """Get top-level config information from DB; format into context data"""
        
        if csid in self.dbcache: # check in-memory cache to decrease DB hits
        	return self.dbcache[csid]
        
        self.curs.execute("SELECT name,rowid,value FROM config_values WHERE csid = ?", (csid,))
        d = dict([((csid,) + tuple(r[0].split('.')), (r[1], r[2])) for r in self.curs.fetchall()])
        self.dbcache[csid] = d
        return d
    
    def reconstruct_instance(self, path, context = {}, cyccheck = None):
        """Reconstruct information for specified instance"""
        #print("<!-- searching", path, "in", context, "-->")
        
        if not path: # end of reconstruction
            #print("<!-- found", context, "-->")
            return context
        
        if cyccheck is None: # initialize cyclical references check
            cyccheck = {path}

        if type(path[0]) == type(1): # top-level specifier; need to load path data
            context = self.load_toplevel(path[0])
            #print("<!-- found top-level data", context, "-->")

        # filter out relevant info from larger context
        subcontext = dict([ (k[1:],v) for (k,v) in context.items() if k[:len(path)] == path[:len(k)] ])
        #print("<!-- filtered to", subcontext, "-->")
        if not subcontext: # terminate search if no remaining relevant data
        	return {}

        # check for and expand link
        thiso = subcontext.get(tuple(), None)
        if thiso and type(thiso[1])==type('') and thiso[1][0] == '@':
            #print("<!-- found link", subcontext[tuple()], "-->")
            lpath = thiso[1][1:].split(".")
            #try:
            if True:
                lpath[0] = int(lpath[0])
                lpath = tuple(lpath)
                if lpath not in cyccheck:
                    ldata = self.reconstruct_instance(lpath, {}, cyccheck.union({lpath}))
                    subcontext.pop(tuple())
                    ldata.update(subcontext)
                    subcontext = ldata
                else:
                    subcontext[tuple()] = (subcontext[tuple()][0], "CYCLIC"+subcontext[tuple()][1])
                    #print("<!-- Not following cyclic link! -->")
            #except:
                pass
        
        # expand * wildcards TODO

        # continue search down path
        return self.reconstruct_instance(path[1:], subcontext, cyccheck)
    
    @staticmethod
    def subdivide_context(d):
        """Divide context dictionary into sub-branches"""
        subdat = { }
        for (k,v) in d.items():
            if not len(k):
            	continue
            subdat.setdefault(k[0],{})[k[1:]] = v
        return subdat
    
    def traverse_context(self, context, cyccheck = None):
        """Traverse to fully expand tree defined by context"""
        #print("<!-- traversing", context, "-->")
        
        if cyccheck is None: # initialize cyclical references check
            cyccheck = set()
        
        # check if top level is link; expand context with link contents if so
        thiso = context.get(tuple(), (None,None))
        islink = None
        if type(thiso[1]) == type("") and thiso[1][0] == '@':
            #print("<!-- found link", thiso, "-->")
            lpath = thiso[1][1:].split(".")
            try:
                lpath[0] = int(lpath[0])
                lpath = tuple(lpath)
                if lpath not in cyccheck:
                    ldata = self.reconstruct_instance(lpath, {}, cyccheck.union({lpath}))
                    context.pop(tuple())
                    ldata.update(context)
                    islink = thiso
                    context = ldata
                else:
                    context[tuple()] = (thiso[0], "CYCLIC"+thiso[1])
                    #print("<!-- Not following cyclic link! -->")
            except:
                pass
            thiso = context.get(tuple(), (None, None))

        subdat = self.subdivide_context(context)

        expanded = {'': thiso} if thiso is not None else {}
        if islink is not None:
            expanded[None] = islink
        for k in subdat:
            v = subdat[k]
            expanded[k] = self.traverse_context(v, cyccheck)
        return expanded
    
    
    def displayform(self, obj):
        """Display form of object tree"""
        
        #########################
        # special case processing
        specialkeys = set((None, "!xml"))
        wraptag = None
        
        # xml tags
        if "!xml" in obj:
            xargs = {}
            for k in [k for k in obj if type(k)==type("") and k[:1]=='$']:
                specialkeys.add(k)
                xargs[k[1:]] = obj[k][''][1]
            wraptag = ET.Element(obj["!xml"][''][1], xargs)
        
        # list-like objects
        itmtag = obj.get("!list",{'':(None,None)})[''][1]
        if itmtag:
            L = wraptag if wraptag is not None else ET.Element("ul")
            klist = [ k for k in obj.keys() if k and k[:1]=="#"]
            klist.sort()
            for k in klist:
                addTag(L, itmtag, contents=self.displayform(obj[k]))
            return L
        
        # fix sort order by variable name
        rlist = []
        klist = [ k for k in obj.keys() if k not in specialkeys]
        klist.sort()
        
        for k in klist:
            if itmtag and k[:1] != "#":
                continue
            v = obj[k]
            if k == '':
                if v[1]:
                    rlist.append(["(this)", (v[1],{"class":"good"})])
            elif tuple(v.keys()) == ('',):
                rlist.append([k, (v[''][1],{"class":"good"})])
            else:
                rlist.append([k, self.displayform(v)])

        if len(rlist) == 1:
            r = rlist[0]
            wraptag = wraptag if wraptag else ET.Element("g")
            wraptag.text = r[0]
            if ET.iselement(r[1]):
                wraptag.append(r[1])
            else:
                el = ET.Element("g", r[1][1])
                el.text = r[1][0]
                wraptag.append(el)
            return wraptag

        tbl = makeTable(rlist)
        if wraptag is not None:
            wraptag.append(tbl)
        return wraptag if wraptag is not None else tbl





    def edit_object(self, iid):
        """Object editor page, given object type config and instance"""
        
        topdat = set([v[0] for v in self.load_toplevel(iid[0]).values()])
        ic = self.reconstruct_instance(iid)
        obj = self.traverse_context(ic,None)
        print("<!--", obj, "-->")
        
        # fix sort order by variable name
        rlist = []
        klist = [ k for k in obj.keys() if k is not None]
        klist.sort()
        
        nDeleteable = 0
        edname = ".".join((str(iid[0]),)+iid[1:])
        for k in klist:
            v = obj[k]
            islink = None in v
            basenum = None
            subedname = (edname+"."+k)
            
            if k == '': # final node value... sometimes need to edit in compound classes
                if v[1]:
                    basenum = v[0] if v[0] in topdat else None
                    rlist.append([("(this)", {"class":"warning"}) if basenum else "(this)", (v[1],{"class":"good"})])
                    if basenum:
                        rlist[-1].append(ET.Element('input', {"type":"text", "name":"val_%i"%v[0], "size":"20"}))
        
            elif tuple(v.keys()) == ('',): # simple final node value
                vv = v['']
                if vv[1]:
                    basenum = vv[0] if vv[0] in topdat else None
                    if basenum:
                        updf = ET.Element('input', {"type":"text", "name":"val_%i"%vv[0], "size":"20"})
                    else:
                        updf = ET.Element('input', {"type":"text", "name":"new_%s"%subedname, "size":"20"})
                    rlist.append([(k, {"class":"warning"}) if basenum else k, (vv[1],{"class":"good"}), updf])
            
            else: # more complex objects...
                if '' in v:
                    basenum = v[''][0] if v[''][0] in topdat else None
                if islink:
                    basenum = v[None][0] if v[None][0] in topdat else None
                edlink = makeLink("/cgi-bin/Metaform.py?edit=%s"%subedname, "Edit")
                kname = makeLink("/cgi-bin/Metaform.py?edit=%s"%v[None][1][1:], "("+k+")") if islink else k
                rlist.append([(kname, {"class":"warning"}) if basenum else kname, self.displayform(v), edlink])
            
            if basenum is not None:
                rlist[-1].append(makeCheckbox("del_%i"%basenum))
                nDeleteable += 1
    
        gp =  ET.Element("g")
   
        
        F =  ET.Element("form", {"action":"/cgi-bin/Metaform.py", "method":"post"})
        Fs = addTag(F, "fieldset")
        addTag(Fs, "legend", contents="Modify parameters")
        Fs.append(makeTable(rlist))
        addTag(Fs,"input",{"type":"hidden","name":"edit","value":edname}) # returns to this edit page after form actions
        addTag(Fs,"input",{"type":"submit","name":"update","value":"Update"})
        if nDeleteable:
            addTag(Fs,"input",{"type":"submit","name":"delete","value":"Delete Marked"})

        gp.append(F)
        
        Fp = ET.Element("form", {"action":"/cgi-bin/Metaform.py"})
        Fsp = addTag(F, "fieldset")
        addTag(Fsp, "legend", contents="Add new parameter")
        rows = [(["Name", "Value"], {"class":"tblhead"}),]
        addTag(Fsp,"input", {"type":"text", "name":"newnm", "size":"6"})
        addTag(Fsp,"input", {"type":"text", "name":"newval", "size":"20"})
        #addTag(Fsp,"input",{"type":"hidden","name":"edit","value":edname}) # returns to this edit page after form actions
        addTag(Fsp,"input",{"type":"submit","name":"addparam","value":"Add Parameter"})
        
        gp.append(Fp)
        return gp
        

    
    
if __name__ == "__main__":
    dbname = "../config_test.db"
    conn = sqlite3.connect(dbname)
    C = Metaform(conn)
    
    form = cgi.FieldStorage()
    
    print(docHeaderString())
    
    if "delete" in form:
        for d in [v[4:] for v in form if v[:4]=="del_"]:
            try:
                C.delete_if_not_applied(int(d))
            except:
                pass
        conn.commit()
    
    if "update" in form:
        for d in [v[4:] for v in form if v[:4]=="val_"]:
            try:
                C.set_if_not_applied(int(d), form.getvalue("val_"+d))
            except:
                pass
        for d in [v[4:] for v in form if v[:4]=="new_"]:
            try:
                itm = d.split(".",1)
                csid = int(itm[0])
                if not C.has_been_applied(csid):
                    C.set_config_value(csid, itm[1], form.getvalue("new_"+d))
            except:
                pass
        conn.commit()
        
    if "addparam" in form and "edit" in form and "newnm" in form and "newval" in form:
        try:
            edpath = form.getvalue("edit").split(".")
            csid = int(edpath[0])
            if not C.has_been_applied(csid):
                C.set_config_value(csid, ".".join(edpath[1:]+[form.getvalue("newnm")]), form.getvalue("newval"))
        except:
            pass
        conn.commit()
    
    if "view" in form:
        iid = form.getvalue("view").split(".")
        iid = (int(iid[0]),) + tuple(iid[1:])
        P,b = makePageStructure("Metaform")
        h1 = addTag(b,"h1", contents = "Viewing ")
        vstr = "%i"%iid[0]
        prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%vstr, "%s:%s"%C.get_setname(iid[0]))
        h1.append(prev)
        for v in iid[1:]:
            vstr += ".%s"%v
            prev.tail = "."
            prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%vstr, v)
            h1.append(prev)
        ic = C.reconstruct_instance(iid)
        obj = C.traverse_context(ic,None)
        b.append(C.displayform(obj))
        print(prettystring(P))

    elif "edit" in form:
        iid = form.getvalue("edit").split(".")
        iid = (int(iid[0]),) + tuple(iid[1:])
        P,b = makePageStructure("Metaform")
        h1 = addTag(b,"h1", contents = "Editing ")
        vstr = "%i"%iid[0]
        prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%vstr, "%s:%s"%C.get_setname(iid[0]))
        h1.append(prev)
        for v in iid[1:]:
            vstr += ".%s"%v
            prev.tail = "."
            prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%vstr, v)
            h1.append(prev)
        b.append(C.edit_object(iid))
        print(prettystring(P))
    
    