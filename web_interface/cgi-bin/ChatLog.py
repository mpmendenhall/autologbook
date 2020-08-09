#!/usr/bin/python3
## \file ChatLog.py Chat log utility page

from WebpageUtils import *
from AutologbookConfig import *
import time
import sqlite3
import cgi
import os
import shlex

def asciistrip(s): return ''.join([x for x in s if ord(x) < 128]) if s else s

class ChatMessagesDisplay:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.curs = self.conn.cursor()
        self.src = self.name = None

    def addMessage(self, msg):
        self.curs.execute("INSERT INTO messages(time,src,name,msg,state) VALUES (?,?,?,?,1)", (time.time(), self.src, self.name, msg[:10000]))
        self.conn.commit()

    def delMessage(self, tmax = 3600):
        self.curs.execute("SELECT rowid FROM messages WHERE src = ? AND state = 1 AND time > ? ORDER BY -time LIMIT 1", (self.src, time.time()-tmax))
        res = self.curs.fetchall()
        if res:
            self.curs.execute("UPDATE messages SET state = 0 WHERE rowid = ?", (res[0][0],))
            self.conn.commit()

    def makeMessageTable(self,groupid=None):
        self.curs.execute("SELECT time,name,src,msg FROM messages WHERE state > 0 ORDER BY -time LIMIT 100")


        csty = ET.Element("colgroup")
        addTag(csty,"col",{"class":"neutral"})
        trows = [makeTable([["time","name","message", "IP address"]], T="thead"), csty]

        prevdate = time.strftime("%A, %B %d",time.localtime(time.time()))
        for m in  self.curs.fetchall():
            newdate = time.strftime("%A, %B %d",time.localtime(m[0]))
            if newdate != prevdate:
                trows.append([(prevdate,{"class":"listbreak", "colspan":"4"})])
            prevdate = newdate
            trows.append([time.strftime("%H:%M:%S",time.localtime(m[0])),
                    ((m[1] if m[1] else "???")+":",{"class":"boldright"}),
                    (asciistrip(m[3]),{"class":"neutral" if m[1]==self.name else "good"}),
                    m[2] if m[2] else "???"])
        return makeTable(trows)

    def makePage(self, groupid=None):
        P,b = makePageStructure("Operator Messages", refresh=1800)
        addTag(b,"h1",contents=["Operators' message log as of %s"%time.asctime(), makeLink("/index.html","[Home]")])

        F = addTag(b, "form", {"action":"/cgi-bin/ChatLog.py", "method":"POST"})
        addTag(F,"label",{"for":"name"},"Name:")
        if self.name: addTag(F,"input", {"type":"text", "name":"name", "id":"name", "size":"10", "value":self.name})
        else: addTag(F,"input", {"type":"text", "name":"name", "id":"name", "size":"10"})
        addTag(F,"label",{"for":"msg"},"Message:")
        addTag(F,"input", {"type":"text", "name":"msg", "id":"msg", "size":"100"})
        addTag(F,"br")
        addTag(F,"input",{"type":"submit","name":"submit","value":"Post"})
        addTag(F,"input",{"type":"submit","name":"refresh","value":"Refresh"})
        addTag(F,"input",{"type":"submit","name":"delete","value":"Delete"})

        b.append(self.makeMessageTable(groupid))
        print(docHeaderString())
        print(prettystring(P))

if __name__=="__main__":
    form = cgi.FieldStorage()

    #"REMOTE_ADDR" not in os.environ and
    # initialization
    if not os.path.exists(chatlog_db):
        cmd = "sqlite3 %s < "%shlex.quote(chatlog_db) + autologbook + "/db_schema/chat_DB_schema.sql"
        os.system(cmd)

    CMD = ChatMessagesDisplay(chatlog_db)
    CMD.name = asciistrip(form.getvalue("name", "")).strip()[:25]
    CMD.src = os.environ.get("REMOTE_ADDR", None)
    if "delete" in form: CMD.delMessage()
    if CMD.name and "msg" in form and "submit" in form: CMD.addMessage(form.getvalue("msg"))
    CMD.makePage()
