#!/usr/bin/python3

from ConfigTree import *
from WebpageUtils import *
import time
import cgi
import urllib.parse as urlp

class Metaform(ConfigTree):
    """Web forms interface to ConfigTree, allowing web form generation"""
    
    def __init__(self, conn = None):
        ConfigTree.__init__(self,conn)
        self.readonly = False

    @staticmethod
    def aselement(clist, dflt="div"):
        """contents list to single element"""
        if len(clist)==1 and ET.iselement(clist[0]):
            return clist[0]
        return addTag(None, dflt, contents = clist)
    
    @staticmethod
    def asstring(clist):
        """flatten display list to string"""
        s = ""
        for c in clist:
            if ET.iselement(c):
                s += ET.tostring(c).decode('utf-8')
            elif c:
                s += str(c)
        return s
    
    def displayform(self, obj):
        """Display form of object tree: returns tuple of mixed text/tag objects"""
        
        # remove extra link information unused by display
        islink = None
        if 0 in obj:
            islink = obj[0]
            obj.pop(0)
        
        # create xml tag if specified; delete link information
        wraptag = None
        if "!xml" in obj and None in obj["!xml"] and obj["!xml"][None][1]:
            xargs = {}
            for k in [k for k in obj["!xml"] if type(k)==type("") and k[:1]=='#']:
                xargs[k[1:]] = self.asstring(self.displayform(obj["!xml"][k]))
            wraptag = ET.Element(obj["!xml"][None][1], xargs)
            obj.pop("!xml")
            
        # simple single-value objects
        if len(obj)==1 and None in obj:
            o = obj[None][1]
            if wraptag is not None:
                wraptag.text = o
                return (wraptag,)
            return (o,) if o is not None else tuple()

        # list-like objects
        itmtag = None
        if "!list" in obj:
            klist = [ k for k in obj.keys() if k and k[:1]=="#" and k[-1:] != '*']
            klist.sort()
        
            itms = [self.displayform(obj[k]) for k in klist]
            itmtag = obj.get("!list", {None: (None,None)})[None][1]
            if itmtag:
                itms = [addTag(None, itmtag, contents = i) for i in itms]
            else: # "glom mode"
                itms = [i for itm in itms for i in itm]
            
            if wraptag is None:
                return tuple(itms)
            
            mergecontents(wraptag, itms)
            return (wraptag,)
        
        # "displayable" objects ordered by name
        rlist = []
        klist = [ k for k in obj.keys() if  k is not None and k[-1:] != '*']
        klist.sort()
        if None in obj:
            klist = [None,] + klist
            
        # simple leaf nodes
        if klist == [None,]:
            v = obj[None][1]
            if wraptag is not None:
                wraptag.text = v #"NULL" if v is None else v
                return (wraptag,)

        # table form display entities for each non-"special" object
        for k in klist:
            v = obj[k]
            if k == None:
                if v[1]:
                    rlist.append(["(this)", (v[1],{"class":"good"})])
            elif tuple(v.keys()) == (None,):
                rlist.append([k, (v[None][1],{"class":"good"})])
            else:
                rlist.append([k, self.aselement(self.displayform(v))])

        if not rlist:
            return (wraptag,) if wraptag is not None else tuple()
            
        tbl = makeTable(rlist)
        if wraptag is not None:
            wraptag.append(tbl)
            return (wraptag,)
        return (tbl,)

    def edit_object(self, iid):
        """Object editor page, given object type config and instance"""
        
        idat = self.load_toplevel(iid[0])
        topkeys = set([v[0] for v in idat.values()])
        obj = self.traverse_context(idat, iid)
        obj = self.traverse_context(obj, wildcard = False, ppath=iid)
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
                basenum = v[0] if v[0] in topkeys else None
                rlist.append([("(this)", {"class":"warning"}) if basenum else "(this)", (v[1] if v[1] is not None else "None", {"class":"good"})])
                if basenum:
                    rlist[-1].append(ET.Element('input', {"type":"text", "name":"val_%i"%v[0], "size":"20"}))
                        
            elif tuple(v.keys()) == (None,): # simple editable final node value
                vv = v[None]
                if type(vv) == type(tuple()):
                    basenum = vv[0] if vv[0] in topkeys else None
                    if basenum:
                        updf = ET.Element('input', {"type":"text", "name":"val_%i"%vv[0], "size":"20"})
                    else:
                        updf = ET.Element('input', {"type":"text", "name":"new_%s"%subedname, "size":"20"})
                    rlist.append([(k, {"class":"warning"}) if basenum else k, (vv[1] if vv[1] is not None else "None",{"class":"good"}), updf])
            
            else: # more complex objects...
                if None in v:
                    basenum = v[None][0] if v[None][0] in topkeys else None
                if islink:
                    basenum = v[0][0] if v[0][0] in topkeys else None
                edlink = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(subedname), "Edit")
                kname = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(v[0][1][1:]), "("+k+")") if islink else "None" if k is None else "''" if not k else k
                rlist.append([(kname, {"class":"warning"}) if basenum else kname, self.aselement(self.displayform(v)), (edlink, {"style":"text-align:center"})])
                # TODO more compact form accepting display form lists
            
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
        
    def linkedname(self, iid, toptag):
        """Object name with links to editor"""
        vstr = "%i"%iid[0]
        prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(vstr), "%s:%s"%self.get_setname(iid[0]))
        toptag.append(prev)
        for v in iid[1:]:
            vstr += ".%s"%v
            prev.tail = "."
            prev = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(vstr), v)
            toptag.append(prev)

# TODO
# editing target of links within object

    
if __name__ == "__main__":
    dbname = "../config_test.db"
    conn = sqlite3.connect(dbname)
    C = Metaform(conn)
    
    form = cgi.FieldStorage()
    print(docHeaderString())
    Page = None
    
    if "delete" in form:
        for d in [v[4:] for v in form if v[:4]=="del_"]:
            try:
                C.delete_if_not_applied(int(d))
            except:
                pass
        conn.commit()
    
    if "update" in form:
        # value update entries, specified by pre-existing ID
        for d in [v[4:] for v in form if v[:4]=="val_"]:
            try:
                v = form.getvalue("val_"+d)
                if v == "@":
                    v = None
                C.set_if_not_applied(int(d), v)
            except:
                pass
        # new or overrwrite entries
        for d in [v[4:] for v in form if v[:4]=="new_"]:
            try:
                itm = d.split(".",1)
                csid = int(itm[0])
                if not C.has_been_applied(csid):
                    v = form.getvalue("new_"+d)
                    if v == "@":
                        v = None
                    C.set_config_value(csid, itm[1], v)
            except:
                pass
        conn.commit()
        
    if "addparam" in form and "edit" in form and "newnm" in form and "newval" in form:
        iid = C.iid_fromstr(form.getvalue("edit"))
        if iid is not None:
            newval = form.getvalue("newval")
            newval = None if newval == "@" else newval
            if not C.has_been_applied(iid[0]):
                C.set_config_value(iid[0], ".".join(iid[1:]+[form.getvalue("newnm")]), newval)
                conn.commit()
    
    if "view" in form:
        iid = C.iid_fromstr(form.getvalue("view"))
        if iid is not None:
            Page,b = makePageStructure("Metaform")
            h1 = addTag(b,"h1", contents = "Viewing ")
            C.linkedname(iid,h1)
            obj = C.traverse_context(C.load_toplevel(iid[0]), iid)
            obj = C.traverse_context(obj, ppath=iid)
            b.append(C.aselement(C.displayform(obj)))

    elif "edit" in form:
        iid = C.iid_fromstr(form.getvalue("edit"))
        if iid is not None:
            Page,b = makePageStructure("Metaform")
            h1 = addTag(b,"h1", contents = "Editing ")
            C.linkedname(iid ,h1)
            b.append(C.edit_object(iid))
    
    if Page:
        print(prettystring(Page))
    