#!/usr/bin/python3

from WebpageUtils import *
from configDBcontrol import *
import time
import cgi
import urllib.parse as urlp


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
        # note: drop empty items between multiple dots... treats multiple dots as one
        #d = dict([((csid,) + tuple([i for i in r[0].split('.') if i]), (r[1], r[2])) for r in self.curs.fetchall()])

        d = dict([((csid,) + tuple([i for i in r[0].split('.')]), (r[1], r[2])) for r in self.curs.fetchall()])
        
        self.dbcache[csid] = d
        return d
    
    @staticmethod
    def subdivide_context(d, find = None):
        """Divide context dictionary into sub-context branches, optionally keeping for only one specific branch"""
        subdat = { }
        for (k,v) in d.items():
            if not k or not len(k):
                continue
            if find is not None and k[:len(find)] != find[:len(k)]:
                continue
            subdat.setdefault(k[0],{})[k[1:]] = v
        return subdat
    
    # context: { (x,y,z) : (ID, value), (): (ID,value) }
    #   can be merged/updated with other contexts
    #
    # expanded: { x : { y: { z : { None:(ID,value) } }, None:(ID,value) }
    
    def traverse_context(self, context, find = None, cyccheck = None, wildcard = True):
        """Expand context into tree, including links; return target context or whole expanded tree."""
        
        if cyccheck is None: # initialize cyclical references check
            cyccheck = set()
        
        # check if top level is link; expand context with link contents if so
        thiso = context.get(tuple(), (None,None)) # "this" value for top-level object in traversal, including link expansion
        islink = None # filled in with link information
        if isinstance(thiso[1],str) and thiso[1][:1] == '@':
            #print("<!-- found link", thiso, "-->")
            lpath = thiso[1][1:].split(".")
            lpath[0] = int(lpath[0])
            lpath = tuple(lpath)
            if lpath not in cyccheck:
                ldata = self.traverse_context(self.load_toplevel(lpath[0]), lpath, cyccheck.union({lpath}))
                context.pop(tuple()) # remove origin link
                ldata.update(context) # over-write linked data
                context = ldata # modified data is new context
                islink = thiso # save link information
            else:
                context[tuple()] = (thiso[0], "CYCLIC"+thiso[1])
                #print("<!-- Not following cyclic link! -->")
        
        if find == tuple(): # context at end of find mode... before wildcard expansion
            return context
        
        # expand wildcard items
        if wildcard:
            kset = [k for k in context.keys() if k and isinstance(k[0], str)]
            kset.sort() # standardize application order
            for c in [k for k in kset if k[0][-1:] == '*']:
                cc = c[0][:-1]
                for c2 in kset:
                    if c2 and c2[0][-1] != '*' and c2[0][:len(cc)] == cc:
                        creplace  = (c2[0],) + c[1:]
                        context[creplace] = context[c]

        # consider each sub-branch
        subdat = self.subdivide_context(context, find)
        expanded = {None: context[tuple()]} if tuple() in context else {}
        if islink is not None:
            expanded[0] = islink # special marker for linked objects
        for k in subdat:
            v = subdat[k]
            expanded[k] = self.traverse_context(v, find[1:] if find else None, cyccheck)

        return expanded[find[0]] if find is not None else expanded
    
    
    def displayform(self, obj):
        """Display form of object tree"""
        
        #########################
        # special case processing
        
        # remove extra link information
        islink = None
        if 0 in obj:
            islink = obj[0]
            obj.pop(0)
        
        # special simple-object case
        if len(obj)==1 and None in obj:
            return addTag(None,"g", {"class":"good"}, obj[None][1])

        wraptag = None
        
        # xml tags
        if "!xml" in obj:
            xargs = {}
            for k in [k for k in obj["!xml"] if type(k)==type("") and k[:1]=='#']:
                xargs[k[1:]] = obj["!xml"][k][None][1]
            wraptag = ET.Element(obj["!xml"][None][1], xargs)
            obj.pop("!xml")

        # list-like objects
        itmtag = obj.get("!list", {None: (None,None)})[None][1]
        if itmtag:
            L = wraptag if wraptag is not None else ET.Element("ul")
            klist = [ k for k in obj.keys() if k and k[:1]=="#" and k[-1:] != '*']
            klist.sort()
            for k in klist:
                addTag(L, itmtag, contents = self.displayform(obj[k]))
            return L
        
        # fix sort order by variable name
        rlist = []
        klist = [ k for k in obj.keys() if  k is not None and k[-1:] != '*']
        klist.sort()
        if None in obj:
            klist = [None,] + klist

        # display entities for each non-"special" object
        for k in klist:
            if itmtag and (k is not None and k[:1] != "#"):
                continue
            v = obj[k]
            if k == None:
                if v[1]:
                    rlist.append(["(this)", (v[1],{"class":"good"})])
            elif tuple(v.keys()) == (None,):
                rlist.append([k, (v[None][1],{"class":"good"})])
            else:
                rlist.append([k, self.displayform(v)])

        if len(rlist) == 1 and False: #TODO breaks on deeply-embedded and complex objects
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
        
        idat = self.load_toplevel(iid[0])
        topkeys = set([v[0] for v in idat.values()])
        obj = self.traverse_context(idat, iid)
        obj = self.traverse_context(obj, wildcard = False)
        print("<!-- edit_object", obj, "-->")
        
        # fix sort order by variable name
        rlist = []
        klist = [ k for k in obj.keys() if k not in (None, 0)]
        klist.sort()
        if None in obj:
            klist = [None,] + klist
            
        nDeleteable = 0
        edname = ".".join((str(iid[0]),)+iid[1:])
        for k in klist:
            v = obj[k]
            islink = 0 in v
            basenum = None
            subedname = (edname+"."+k) if k is not None else None
            
            if k == None: # final node value... sometimes need to edit in compound classes
                if v[1]:
                    basenum = v[0] if v[0] in topkeys else None
                    rlist.append([("(this)", {"class":"warning"}) if basenum else "(this)", (v[1],{"class":"good"})])
                    if basenum:
                        rlist[-1].append(ET.Element('input', {"type":"text", "name":"val_%i"%v[0], "size":"20"}))
                        
            elif tuple(v.keys()) == (None,): # simple editable final node value
                vv = v[None]
                if type(vv) == type(tuple()) and vv[1]:
                    basenum = vv[0] if vv[0] in topkeys else None
                    if basenum:
                        updf = ET.Element('input', {"type":"text", "name":"val_%i"%vv[0], "size":"20"})
                    else:
                        updf = ET.Element('input', {"type":"text", "name":"new_%s"%subedname, "size":"20"})
                    rlist.append([(k, {"class":"warning"}) if basenum else k, (vv[1],{"class":"good"}), updf])
            
            else: # more complex objects...
                if None in v:
                    basenum = v[None][0] if v[None][0] in topkeys else None
                if islink:
                    basenum = v[0][0] if v[0][0] in topkeys else None
                edlink = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(subedname), "Edit")
                kname = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(v[0][1][1:]), "("+k+")") if islink else "None" if k is None else "''" if not k else k
                rlist.append([(kname, {"class":"warning"}) if basenum else kname, self.displayform(v), (edlink, {"style":"text-align:center"})])
            
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
        
def linkedname(iid, toptag):
    """Object name with links to editor"""
    iid = iid.split(".")
    iid = (int(iid[0]),) + tuple(iid[1:])
    vstr = "%i"%iid[0]
    prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(vstr), "%s:%s"%C.get_setname(iid[0]))
    toptag.append(prev)
    for v in iid[1:]:
        vstr += ".%s"%v
        prev.tail = "."
        prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(vstr), v)
        toptag.append(prev)
    return iid

# TODO
# editing target of links within object

    
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
        P,b = makePageStructure("Metaform")
        h1 = addTag(b,"h1", contents = "Viewing ")
        iid = linkedname(form.getvalue("view"),h1)
        obj = C.traverse_context(C.load_toplevel(iid[0]), iid)
        obj = C.traverse_context(obj)
        print("<!-- view", obj, "-->")
        b.append(C.displayform(obj))
        print(prettystring(P))

    elif "edit" in form:
        P,b = makePageStructure("Metaform")
        h1 = addTag(b,"h1", contents = "Editing ")
        iid = linkedname(form.getvalue("edit") ,h1)
        b.append(C.edit_object(iid))
        print(prettystring(P))
    
    