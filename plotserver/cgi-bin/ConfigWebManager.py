#!/usr/bin/python

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
        
        self.curs.execute("SELECT DISTINCT family FROM config_set")
        families = [r[0] for r in self.curs.fetchall()]
        fl = makeList([makeLink("/cgi-bin/ConfigWebManager.py?family=%s"%f, f) for f in families])
        
        P,b = makePageStructure("Configuration Families")
        addTag(b,"h1",contents="Configuration set families")
        b.append(fl)
        print(prettystring(P))        

    def make_csets_page(self, f):
        
        selected = self.find_config_at(time.time(), f)
        rows = [(["Name", "Description", "Created"], {"class":"tblhead"}),]
        self.curs.execute("SELECT rowid,name,descrip,time FROM config_set WHERE family = ?", (f,))
        for r in self.curs.fetchall():
            rw = [makeLink("/cgi-bin/ConfigWebManager.py?cset=%i"%r[0], r[1]), r[2], time.ctime(r[3])]
            rows.append((rw,{"class":"good"}) if r[0]==selected else rw)
        
        P,b = makePageStructure("%s Configurations"%f)
        addTag(b,"h1",contents="Configuration sets in %s"%f)
        b.append(makeTable(rows,{"class":"neutral"}))
        print(prettystring(P))        
    
    def make_params_page(self,cset):
        self.curs.execute("SELECT family,name,descrip FROM config_set WHERE rowid = ?", (cset,))
        setname =  self.curs.fetchone()
        applied = self.has_been_applied(cset)
        
        P,b = makePageStructure("%s:%s"%setname[:2])
        addTag(b, "h1", contents="Configuration set %s:%s"%setname[:2])
        addTag(b, "h3", contents='"%s"'%setname[2])
        b.append(self.update_params_form(cset, not (self.readonly or applied)))
        if not applied:
            b.append(self.new_params_form())
        b.append(self.copy_params_form(cset))
        print(prettystring(P)) 

    def update_params_form(self, cset, editable):
        self.curs.execute("SELECT rowid,name,value FROM config_values WHERE csid = ?", (cset,))
        ps = self.curs.fetchall()
        
        if editable:
            setgroups = [makeTable([[makeCheckbox("del_%i"%p[0]), p[1], (p[2],{"class": "good"}), ET.Element('input', {"type":"text", "name":"val_%i"%p[0], "size":"6"})]]) for p in ps]
            
            F =  ET.Element("form", {"action":"/cgi-bin/ConfigWebManager.py", "method":"post"})
            Fs = addTag(F, "fieldset")
            addTag(Fs, "legend", contents="Current parameter values")
            Fs.append(fillTable(setgroups,{"class":"neutral"}))
            addTag(Fs,"input",{"type":"submit","name":"upd_cset","value":"Update"})
            addTag(Fs,"input",{"type":"submit","name":"del_cset","value":"Delete Marked"})
            return F
        else:
            setgroups = [makeTable([[p[1], (p[2],{"class": "good"})]]) for p in ps] 
            return fillTable(setgroups,{"class":"neutral"})
        
    def new_params_form(self):
        F = ET.Element("form", {"action":"/cgi-bin/ConfigWebManager.py"})
        Fs = addTag(F, "fieldset")
        addTag(Fs, "legend", contents="Add new parameters")
        rows = [(["Name", "Value"], {"class":"tblhead"}),] 
        rows += [ [ET.Element('input', {"type":"text", "name":"nm_%i"%i, "size":"6"}), ET.Element('input', {"type":"text", "name":"val_%i"%i, "size":"10"})] for i in range(6)]
        Fs.append(makeTable(rows))
        addTag(Fs,"input",{"type":"submit","name":"adp_cset","value":"Add Parameters"})
        return F
    
    def copy_params_form(self, cset):
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
    
if __name__ == "__main__":
    dbname = "../config_test.db"
    conn = sqlite3.connect(dbname)
    C = ConfigWebManager(conn)
    
    form = cgi.FieldStorage()
    
    print(docHeaderString())
    
    if "cp_cset" in form:
        C.clone_set(form)
        conn.commit()
    elif "family" in form:
        C.make_csets_page(form.getvalue("family"))
    elif "cset" in form:
        cset = int(form.getvalue("cset"))
        C.make_params_page(cset)
    else:
        C.make_families_page()
    