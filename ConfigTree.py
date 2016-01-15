#!/usr/bin/python3

from configDBcontrol import *

class ConfigTree(ConfigDB):
    """Tree structure parser for configuration database"""
    
    def __init__(self, conn = None):
        ConfigDB.__init__(self,conn)
        self.namecache = {}     # cache of object identifiers
        self.dbcache = {}       # cache of top-level DB entries

    def iid_fromstr(self, s):
        """Resolve string into instance identifier; None if not resolvable"""
        iid = s.split(".")

        if iid[0].isdigit():
            iid[0] = int(iid[0])
        else:
            f,n = iid[0].split(":",1) if ":" in iid[0] else (None, iid[0])
            if (n,f) in self.namecache:
                iid[0] = self.namecache[(n,f)]
            else:
                iid[0] = self.find_configset(n,f)
                self.namecache[(n,f)] = iid[0]

        return tuple(iid) if iid[0] is not None else None
    
    def load_toplevel(self, csid):
        """Get top-level config information from DB; format into context data"""
        
        if csid in self.dbcache: # check in-memory cache to decrease DB hits
                return self.dbcache[csid]
        
        self.curs.execute("SELECT name,rowid,value FROM config_values WHERE csid = ?", (csid,))
        d = dict([((csid,) + (tuple([i for i in r[0].split('.')]) if r[0] is not None else tuple()), (r[1], r[2])) for r in self.curs.fetchall()])
        
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
    
    def traverse_context(self, context, find = None, cyccheck = None, wildcard = True, ppath = tuple()):
        """Expand context into tree, including links; return target context or whole expanded tree."""
        
        if cyccheck is None: # initialize cyclical references check
            cyccheck = set() #{find} if find is not None else set()
        
        #####################################################################
        # check if top level is link; expand context with link contents if so
        thiso = context.get(tuple(), (None,None)) # "this" value for top-level object in traversal, including link expansion
        islink = None # filled in with link information
        lpath = None # link path
        if thiso[1] == '@': # special case link-to-NULL
            context.pop(tuple())
            islink = thiso # mark as link
        elif isinstance(thiso[1],str) and thiso[1][:1] == '@':
            if thiso[1][1:2] in ["~","$"]: # relative link expansion
                lparts = thiso[1][2:].split(".")
                n = int(lparts[0]) if lparts[0].isdigit() else 0
                ltext = ".".join([str(p) for p in ppath][:-n if n else 1000000] + lparts[1:])
                if thiso[1][1:2] == "$": # relative link text
                    context[tuple()] = (thiso[0], ltext)
                    islink = thiso
                    thiso = None
                else:
                    thiso = (thiso[0], "@"+ltext) if ltext else None
                    #Sprint("<!-- Expanding rel link", thiso, "-->")
                    
            lpath = self.iid_fromstr(thiso[1][1:]) if thiso is not None else None
            if lpath is not None:
                #print("<!-- following link", thiso, cyccheck, "-->")
                if thiso not in cyccheck:
                    ldata = self.traverse_context(self.load_toplevel(lpath[0]), lpath, cyccheck.union({thiso}))
                    context.pop(tuple()) # remove origin link
                    ldata.update(context) # over-write linked data
                    context = ldata # modified data is new context
                    islink = thiso # save link information
                    #print("<!-- link info", thiso, context, "-->")
                else:
                    #print("<!-- CYCLIC LINK on lpath", lpath, thiso, "-->")
                    context[tuple()] = (thiso[0], "CYCLIC"+thiso[1])
        
        if find == tuple(): # context at end of find mode... before wildcard expansion
            if islink is not None:
                context[0] = islink # special marker for linked objects
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

        
        subdat = self.subdivide_context(context, find)
        # follow search path
        if find is not None:
            return self.traverse_context(subdat.get(find[0],{}), find[1:],
                                         cyccheck.union({islink}) if islink else cyccheck,
                                         ppath = ppath + (find[0],))
        # expand all branches
        expanded = {}
        if tuple() in context:
            expanded[None] = context[tuple()]
        if 0 in context:
            expanded[0] = context[0]
        if islink is not None:
            expanded[0] = islink # special marker for linked objects
        for k in subdat:
            v = subdat[k]
            expanded[k] = self.traverse_context(v, None,
                                                cyccheck.union({islink}) if islink else cyccheck,
                                                ppath = ppath + (k,))
        return expanded
