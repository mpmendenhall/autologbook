#!/usr/bin/python3

from WebpageUtils import *
from configDBcontrol import *
import time
import cgi

class ConfigWebManager(ConfigDB):
    """Web interface for managing configuration DB"""
    
    def __init__(self, conn = None):
        ConfigDB.__init__(self,conn)
        self.readonly = False
        
    def make_families_page(self):
        """Page for browsing/creating configuration set families"""
        self.curs.execute("SELECT DISTINCT family FROM config_set")
        families = [r[0] for r in self.curs.fetchall()]
        fl = makeList([makeLink("/cgi-bin/ConfigWebManager.py?family=%s"%f, f) for f in families])
        
        P,b = makePageStructure("Configuration Families")
        addTag(b,"h1",contents="Configuration set families")
        b.append(fl)
        
        if not self.readonly:
            F = ET.Element("form", {"action":"/cgi-bin/ConfigWebManager.py"})
            Fs = addTag(F, "fieldset")
            addTag(Fs, "legend", contents="Make new configuration set family")
            addTag(Fs, 'input', {"type":"text", "name":"famname", "size":"10"})
            addTag(Fs,"input",{"type":"submit","name":"newfamily","value":"New family"})
            b.append(F)
        
        print(prettystring(P))

    def make_csets_page(self, f):
        """Page for browsing configuration sets within a family"""
        selected = self.find_config_at(time.time(), f)
        rows = [(["", "Name", "Description", "Created"], {"class":"tblhead"}),]
        self.curs.execute("SELECT rowid,name,descrip,time FROM config_set WHERE family = ?", (f,))
        ndeleteable = 0
        for r in self.curs.fetchall():
            isdeleteable = not self.has_been_applied(r[0])
            ndeleteable += isdeleteable
            rw = [makeCheckbox("rmr_%i"%r[0]) if isdeleteable else "",
                  makeLink("/cgi-bin/ConfigWebManager.py?cset=%i"%r[0], r[1]), r[2], time.ctime(r[3])]
            rows.append((rw,{"class":"good"}) if r[0]==selected else rw)
        if len(rows) == 1:
            return self.make_families_page()
        tbl = makeTable(rows,{"class":"neutral"})
        
        P,b = makePageStructure("%s Configurations"%f)
        h1 = addTag(b,"h1")
        clnk = makeLink("/cgi-bin/ConfigWebManager.py", "Configuration sets")
        clnk.tail = "in %s"%f
        h1.append(clnk)
        if ndeleteable:
            F = addTag(b, "form", {"action":"/cgi-bin/ConfigWebManager.py"})
            F.append(tbl)
            addTag(F,"input",{"type":"hidden","name":"family","value":f})
            addTag(F,"input",{"type":"submit","name":"del_csets","value":"Delete Marked"})
        else:
            b.append(tbl)
        print(prettystring(P))
    
    def make_params_page(self,cset,ncols=4):
        """Page for viewing/modifying parameters in a configuration set"""
        self.curs.execute("SELECT family,name,descrip FROM config_set WHERE rowid = ?", (cset,))
        setname =  self.curs.fetchone()
        applied = self.has_been_applied(cset)
        
        P,b = makePageStructure("%s:%s"%setname[:2])
        h1 = addTag(b, "h1", contents="Configuration set ")
        flnk = makeLink("/cgi-bin/ConfigWebManager.py?family=%s"%setname[0], setname[0])
        flnk.tail = " : %s"%setname[1]
        h1.append(flnk)
        h3 = addTag(b, "h3", contents='"%s"'%setname[2])
        h3.append(makeLink("/cgi-bin/ConfigWebManager.py?dump=%i"%cset, "(text dump)"))
        h3.append(makeLink("/cgi-bin/Metaform.py?view=%i"%cset, "(tree view)"))
        b.append(self.update_params_form(cset, not (self.readonly or applied), ncols))
        if not applied:
            b.append(self.new_params_form(cset))
        b.append(self.copy_params_form(cset))
        print(prettystring(P)) 

    def update_params_form(self, cset, editable, ncols = 4):
        """Form for updating parameters"""
        self.curs.execute("SELECT rowid,name,value FROM config_values WHERE csid = ?", (cset,))
        ps = self.curs.fetchall()
        
        varname = (lambda n: "(None)" if n is None else n)
        
        if editable:
            setgroups = [[makeCheckbox("del_%i"%p[0]), varname(p[1]), (str(p[2]),{"class": "good"}), ET.Element('input', {"type":"text", "name":"val_%i"%p[0], "size":"6"})] for p in ps]
            setgroups = fillColumns(setgroups, ncols)
            setgroups = [ [x for l in g for x in l] for g in setgroups]
            
            F =  ET.Element("form", {"action":"/cgi-bin/ConfigWebManager.py", "method":"post"})
            Fs = addTag(F, "fieldset")
            addTag(Fs, "legend", contents="Current parameter values")
            Fs.append(makeTable(setgroups,{"class":"neutral"}))
            addTag(Fs,"input",{"type":"hidden","name":"cset","value":"%i"%cset})
            addTag(Fs,"input",{"type":"hidden","name":"ncols","value":"%i"%ncols})
            addTag(Fs,"input",{"type":"submit","name":"upd_params","value":"Update"})
            addTag(Fs,"input",{"type":"submit","name":"del_params","value":"Delete Marked"})
            return F
        else:
            setgroups = [[varname(p[1]), (p[2],{"class": "good"})] for p in ps]
            setgroups = fillColumns(setgroups, ncols)
            setgroups = [ [x for l in g for x in l] for g in setgroups]
            return makeTable(setgroups,{"class":"neutral"})
        
    def new_params_form(self,cset):
        """Form for new parameters"""
        F = ET.Element("form", {"action":"/cgi-bin/ConfigWebManager.py"})
        Fs = addTag(F, "fieldset")
        addTag(Fs, "legend", contents="Add new parameters")
        rows = [(["Name", "Value"], {"class":"tblhead"}),] 
        rows += [ [ET.Element('input', {"type":"text", "name":"nm_%i"%i, "size":"6"}), ET.Element('input', {"type":"text", "name":"val_%i"%i, "size":"10"})] for i in range(6)]
        Fs.append(makeTable(rows))
        addTag(Fs,"input",{"type":"hidden","name":"cset","value":"%i"%cset})
        addTag(Fs,"input",{"type":"submit","name":"add_params","value":"Add Parameters"})
        return F
    
    def copy_params_form(self, cset):
        """Form to copy a configuration set"""
        F = ET.Element("form", {"action":"/cgi-bin/ConfigWebManager.py"})
        Fs = addTag(F, "fieldset")
        addTag(Fs, "legend", contents="Copy to new configuration set")
        rows = [(["set name", "description"], {"class":"tblhead"}),] 
        rows.append( [ET.Element('input', {"type":"text", "name":"setname", "size":"10"}), ET.Element('input', {"type":"text", "name":"descrip", "size":"50"})] )
        Fs.append(makeTable(rows))
        addTag(Fs,"input",{"type":"hidden","name":"cset","value":"%i"%cset})
        addTag(Fs,"input",{"type":"submit","name":"cp_cset","value":"New copy"})
        return F
    
    def clone_set(self, form):
        """Process form for parameters copy"""
        cset0 = int(form.getvalue("cset",0))
        if self.readonly or not cset0:
            return self.make_families_page()
        
        newname = form.getvalue("setname")
        descrip = form.getvalue("descrip")
        if not (newname and descrip):
            return self.make_params_page(cset0)
        
        cset = self.clone_config(cset0, newname, descrip)
        return self.make_params_page(cset) if cset else self.make_families_page()
    
    def delete_marked_params(self,form):
        """Remove parameters marked for deletion"""
        cset = int(form.getvalue("cset",0))
        if self.readonly or not cset or self.has_been_applied(cset):
            return
        for k in form:
             if k[:4] == "del_":
                try:
                    self.curs.execute("DELETE FROM config_values WHERE rowid = ? AND csid = ?", (int(k[4:]),cset))
                except:
                    continue
    
    def delete_marked_csets(self,form):
        """Remove parameters marked for deletion"""
        if self.readonly:
            return self.make_families_page()
        for k in form:
             if k[:4] == "rmr_":
                try:
                    cset = int(k[4:])
                    if self.has_been_applied(cset):
                        continue
                    self.curs.execute("DELETE FROM config_values WHERE csid = ?", (cset,))
                    self.curs.execute("DELETE FROM config_set WHERE rowid = ?", (cset,))
                except:
                    continue
        if "family" in form:
            return self.make_csets_page(form.getvalue("family"))
        return self.make_families_page()
    
    def update_params(self,form):
        """Update specified parameter values"""
        cset = int(form.getvalue("cset",0))
        if self.readonly or not cset or self.has_been_applied(cset):
            return
        for k in form:
             if k[:4] == "val_" and form.getvalue(k):
                try:
                    self.curs.execute("UPDATE config_values SET value = ? WHERE rowid = ? AND csid = ?", (form.getvalue(k), int(k[4:]), cset))
                except:
                    continue
    
    def add_params(self,form):
        """Add new parameters"""
        cset = int(form.getvalue("cset",0))
        if self.readonly or not cset or self.has_been_applied(cset):
            return
        for k in form:
             if k[:3] == "nm_":
                name = form.getvalue(k)
                pval = form.getvalue("val_"+k[3:])
                if not (name and pval):
                    continue
                try:
                    self.curs.execute("INSERT INTO config_values(csid,name,value) VALUES(?,?,?)", (cset, name, pval))
                except:
                    continue
    
    def make_new_family(self,form):
        """Add placeholder element for new family"""
        fname = form.getvalue("famname",None)
        if fname and not self.readonly:
            try:
                self.make_configset("placeholder", fname, "placeholder for family '%s'"%fname)
            except:
                pass
        return self.make_families_page()
    
    
    
    
    
if __name__ == "__main__":
    dbname = "../config_test.db"
    conn = sqlite3.connect(dbname)
    C = ConfigWebManager(conn)
    
    form = cgi.FieldStorage()
    
    if "dump" in form:
        print("Content-Type: text/plain\n")
        try:
            cset = int(form.getvalue("dump"))
            C.curs.execute("SELECT family,name,descrip FROM config_set WHERE rowid = ?", (cset,))
            for r in C.curs.fetchall():
                print("%s:%s\t%s\n"%r)
            C.curs.execute("SELECT name,value FROM config_values WHERE csid = ?", (cset,))
            for r in C.curs.fetchall():
                print("%s\t%s"%(r[0], str(r[1])))
        except:
            pass
        import sys
        sys.exit()
    
    print(docHeaderString())
    
    if "upd_params" in form:
        C.update_params(form)
        conn.commit()
    elif "add_params" in form:
        C.add_params(form)
        conn.commit()
    elif "del_params" in form:
        C.delete_marked_params(form)
        conn.commit()
        
    if "cp_cset" in form:
        C.clone_set(form)
        conn.commit()
    elif "del_csets" in form:
        C.delete_marked_csets(form)
        conn.commit()
    elif "newfamily" in form:
        C.make_new_family(form)
        conn.commit()
    elif "family" in form:
        C.make_csets_page(form.getvalue("family"))
    elif "cset" in form:
        cset = int(form.getvalue("cset"))
        ncols = form.getvalue("ncols", None)
        ncols = 3 if ncols is None or not ncols.isdigit() or not 1 <= int(ncols) <= 6 else int(ncols)
        C.make_params_page(cset,ncols)
    else:
        C.make_families_page()
