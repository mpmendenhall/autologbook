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
        #print("<!-- found context", obj, "-->")
        obj = self.traverse_context(obj, wildcard = False, ppath=iid)
        #print("<!-- edit expanded", obj, "-->")
        
        # fix sort order by variable name, with "(this)" at top
        rlist = []
        klist = [ k for k in obj.keys() if k not in (None, 0)]
        klist.sort()
        klist = [None,] + klist
            
        nDeleteable = 0
        edname = ".".join((str(iid[0]),)+iid[1:])
        for k in klist:
            v = obj.get(k, {})
            islink = v.get(0,None) if k is not None else obj.get(0,None)
            kname = "(this)" if k is None else "''" if not k else k # display name for key
            kname = (kname,makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(islink[1][1:]), islink[1])) if islink else kname
            subedname = (edname+"."+k) if k is not None else edname
            basenum = None      # entry ID for this object, if belonging to top object (TODO problematic with internal links)
            updf = None         # update/create field for (this)
            edlink = None       # link to object editor page
            
            if k is None:
                basenum = v[0] if None in obj and v[0] in topkeys else None
                if islink:
                    basenum = islink[0] if islink[0] in topkeys else None
                newrow = [(kname, {"class":"warning"}) if basenum else kname, (v[1] if v[1] is not None else "None", {"class":"good"}) if None in obj else None]
                    
            elif tuple(v.keys()) == (None,): # simple editable final node value
                vv = v[None]
                if type(vv) == type(tuple()):
                    basenum = vv[0] if vv[0] in topkeys else None
                    newrow = [(kname, {"class":"warning"}) if basenum else kname, (vv[1] if vv[1] is not None else "None",{"class":"good"})]
            
            else: # more complex objects...
                if None in v: # object's "this" defined
                    basenum = v[None][0] if v[None][0] in topkeys else None
                if islink:
                    basenum = islink[0] if islink[0] in topkeys else None
                edlink = makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(subedname), "Edit")
                newrow = [(kname, {"class":"warning"}) if basenum else kname, self.aselement(self.displayform(v))]            
            
            if basenum:
                updf = ET.Element('input', {"type":"text", "name":"val_%i"%basenum, "size":"20"})
            elif subedname:
                updf = (ET.Element('input', {"type":"text", "name":"new_%s"%subedname, "size":"20"}), {"class":"warning"})
                
            newrow += [updf, (edlink, {"style":"text-align:center"}) if edlink is not None else None]
            
            # object (self) defined here and deletable
            if basenum is not None:
                newrow.append(makeCheckbox("del_%i"%basenum))
                nDeleteable += 1
            
            rlist.append(newrow)
       
        tbl = ET.Element('table')
        #cs = addTag(tbl, "colgroup")
        #for i in range(5):
        #    c = addTag(cs, "col", {"class":"neutral"} if i == 2 else {})
        makeTable(rlist, T = tbl)
        
        gp =  ET.Element("g")
   
        
        F =  ET.Element("form", {"action":"/cgi-bin/Metaform.py", "method":"post"})
        Fs = addTag(F, "fieldset")
        addTag(Fs, "legend", contents="Modify parameters")
        Fs.append(tbl)
        addTag(Fs,"input",{"type":"hidden","name":"edit","value":edname}) # returns to this edit page after form actions
        addTag(Fs,"input",{"type":"submit","name":"update","value":"Update"})
        if nDeleteable:
            addTag(Fs,"input",{"type":"submit","name":"delete","value":"Delete Marked"})

        gp.append(F)
        
        Fp = ET.Element("form", {"action":"/cgi-bin/Metaform.py"})
        Fsp = addTag(F, "fieldset")
        addTag(Fsp, "legend", contents="Add new parameter")
        rows = [(["Name", "Value"], {"class":"tblhead"}),]
        addTag(Fsp,"input", {"type":"text", "name":"newnm", "size":"20"})
        addTag(Fsp,"input", {"type":"text", "name":"newval", "size":"20"})
        #addTag(Fsp,"input",{"type":"hidden","name":"edit","value":edname}) # returns to this edit page after form actions... duplicated above
        addTag(Fsp,"input",{"type":"submit","name":"addparam","value":"Add Parameter"})
        
        gp.append(Fp)
        return gp
        
    def linkedname(self, iid, toptag, mode = "edit"):
        """Object name with links to editor"""
        vstr = "%i"%iid[0]
        prev = makeLink("/cgi-bin/Metaform.py?%s=%s"%(mode, urlp.quote(vstr)), "%s:%s"%self.get_setname(iid[0]))
        toptag.append(prev)
        for v in iid[1:]:
            vstr += ".%s"%v
            prev.tail = "."
            prev = makeLink("/cgi-bin/Metaform.py?%s=%s"%(mode, urlp.quote(vstr)), v)
            toptag.append(prev)

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
                    C.set_config_value(csid, itm[1] if len(itm)==2 else None, v)
            except:
                pass
        conn.commit()
        
    if "addparam" in form and "edit" in form and "newnm" in form and "newval" in form:
        iid = C.iid_fromstr(form.getvalue("edit"))
        if iid is not None:
            newval = form.getvalue("newval")
            newval = None if newval == "@" else newval
            if not C.has_been_applied(iid[0]):
                C.set_config_value(iid[0], ".".join(iid[1:]+(form.getvalue("newnm"),)), newval)
                conn.commit()
    
    if "edit" in form:
        vstr = form.getvalue("edit")
        iid = C.iid_fromstr(vstr)
        if iid is not None:
            Page,b = makePageStructure("Metaform")
            h1 = addTag(b,"h1", contents = "Editing ")
            C.linkedname(iid ,h1)
            h1.append(makeLink("/cgi-bin/Metaform.py?view=%s"%urlp.quote(vstr), "(view)"))
            h1.append(makeLink("/cgi-bin/ConfigWebManager.py?cset=%i&ncols=2"%iid[0], "(flat)"))
            b.append(C.edit_object(iid))
    
    elif "view" in form:
        vstr = form.getvalue("view")
        iid = C.iid_fromstr(vstr)
        if iid is not None:
            Page,b = makePageStructure("Metaform")
            h1 = addTag(b,"h1", contents = "Viewing ")
            C.linkedname(iid,h1,mode="view")
            h1.append(makeLink("/cgi-bin/Metaform.py?edit=%s"%urlp.quote(vstr), "(edit)"))
            obj = C.traverse_context(C.load_toplevel(iid[0]), iid)
            obj = C.traverse_context(obj, ppath=iid)
            b.append(C.aselement(C.displayform(obj)))

    
    if Page:
        print(prettystring(Page))
    