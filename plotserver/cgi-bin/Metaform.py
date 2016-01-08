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
    
    
    def separate_objects(self, cfg):
        """Divide configuration data into sub-object inheritances"""
        # sort into sub-objects
        subobjs = { }
        subdat = { }
        for (k,v) in cfg.items():
            if k == 0:
                continue
            if '.' in k:
                kk = k.split('.',1)
                subdat.setdefault(kk[0],{})[kk[1]] = v
            else:
                subobjs[k] = v
        return (subobjs, subdat)
     
    def render_object(self, csid, instinfo = {}, parentids = set()):
        """Return HTML block rendering of specified object with instance data"""
        
        # base values from object
        self.curs.execute("SELECT name,rowid,value FROM config_values WHERE csid = ?", (csid,))
        cfg = dict([(r[0], (r[1],r[2])) for r in self.curs.fetchall()])
        # merge overrides from instance
        cfg.update(instinfo)
        # sort into sub-objects
        (subobjs, subdat) = self.separate_objects(cfg)
        
        rlist = []
        for (k,v) in subobjs.items():
            if type(v[1]) == type("") and v[1][:1] == "@":    # true subclasses
                oid = int(v[1][1:])
                assert oid not in parentids
                rlist.append([k, self.render_object(oid, subdat.get(k,{}), parentids = parentids.union(set((oid,))))])
            else:
                rlist.append([k, (v[1],{"class":"good"})])
        return makeTable(rlist)
    
    def get_instance_info(self, classid, subpath, parentinfo = {}):
        """Reconstruct information for specified instance"""

        # class values
        self.curs.execute("SELECT name,rowid,value FROM config_values WHERE csid = ?", (classid,))
        cfg = [(r[0], (r[1],r[2])) for r in self.curs.fetchall()]
        # filter relevant to subpath
        if subpath:
            subname = ".".join(subpath)
            cfg = [ c for c in cfg if c[0] == 0 or c[0][:len(subname)] == subname or subname[:len(c[0])] == c[0] ]
        cfg = dict(cfg)
        # merge overrides from parent
        cfg.update(parentinfo)
        cfg.setdefault(0,[]).append(classid) # class inheritance chain
        
        if not subpath:
            return cfg
        
        # follow to next item in path
        try:
            stp = cfg[subpath[0]][1]
            if stp[:1] != "@": # not a class specifier
                return None
            cfg.pop(subpath[0])
        except:
            return None

        subcid = int(stp[1:])
        subcfg = {}
        for (k,v) in cfg.items():
            if k == 0:
                subcfg[k] = v
            else:
                subcfg[k.split(".",1)[1]] = v
        return self.get_instance_info(subcid, subpath[1:], subcfg)
    
    
    def edit_object(self, iid):
        """Object editor page, given object type config and instance"""
        
        self.curs.execute("SELECT rowid FROM config_values WHERE csid = ?", (iid[0],))
        baseconfigs = set([r[0] for r in self.curs.fetchall()]) # configuration defined at base class
        
        cfg = self.get_instance_info(iid[0], iid[1])
        assert cfg
        (subobjs, subdat) = self.separate_objects(cfg)
        
        # render sub-objects (non-dotted names):
        # TODO deal with orphaned dotted names
        rlist = []
        nDeleteable = 0
        edname = ".".join([str(iid[0])]+iid[1])
        klist = list(subobjs.keys())
        klist.sort()
        for k in klist:
            v = subobjs[k]
            subedname = (edname + "."+ k)
            isbase = v[0] in baseconfigs
            if type(v[1]) == type(u"") and v[1][:1] == "@":    # true subclasses
                oid = int(v[1][1:])
                assert oid not in self.prevobjs
                self.prevobjs.add(oid)
                edlink = makeLink("/cgi-bin/Metaform.py?edit=%s"%subedname, "Edit")
                rlist.append([(k, {"class":"warning"}) if k in subdat else k, self.render_object(oid, subdat.get(k,{})), edlink])
            else:
                if isbase:
                    updf = ET.Element('input', {"type":"text", "name":"val_%i"%v[0], "size":"20"})
                else:
                    updf = ET.Element('input', {"type":"text", "name":"new_%s"%subedname, "size":"20"})
                rlist.append([(k, {"class":"warning"}) if isbase else k, (v[1],{"class":"good"}), updf])
            if isbase:
                rlist[-1].append(makeCheckbox("del_%i"%v[0]))
                nDeleteable += 1
        
        gp =  ET.Element("g")
        
        F =  ET.Element("form", {"action":"/cgi-bin/Metaform.py", "method":"post"})
        addTag(F, "h2", contents = "class %s:%s"%self.get_setname(cfg[0][-1]))
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
    
    if "edit" in form:
        iid = form.getvalue("edit").split(".")
        iid = (int(iid[0]), iid[1:])
        P,b = makePageStructure("Metaform")
        h1 = addTag(b,"h1", contents = "Editing ")
        vstr = "%i"%iid[0]
        h1.append(makeLink("/cgi-bin/Metaform.py?edit=%s"%vstr, iid[0]))
        for v in iid[1]:
            vstr += ".%s"%v
            h1.append(makeLink("/cgi-bin/Metaform.py?edit=%s"%vstr, "."+v))
        b.append(C.edit_object(iid))
        print(prettystring(P))
    
    