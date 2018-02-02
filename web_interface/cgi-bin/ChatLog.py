#!/usr/bin/python3
## \file ChatLog.py Chat log utility page

from WebpageUtils import *
import time
import sqlite3
import cgi
import os

def asciistrip(s): return ''.join([x for x in s if ord(x) < 128] if s else s

class ChatMessagesDisplay:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.curs = self.conn.cursor()
        self.src = self.name = None

    def addMessage(self, msg):
        self.curs.execute("INSERT INTO messages(time,src,name,msg) VALUES (?,?,?,?)", (time.time(), self.src, self.name[:25], msg[:10000]))
        self.conn.commit()

    def delMessage(self, tmax = 3600):
        self.curs.execute("SELECT rowid FROM messages WHERE src = ? AND time > ? ORDER BY -time LIMIT 1", (self.src, time.time()-tmax))
        res = self.curs.fetchall()
        if res:
            self.curs.execute("DELETE FROM messages WHERE rowid = ?", (res[0][0],))
            self.conn.commit()

    def makeMessageTable(self,groupid=None):
        self.curs.execute("SELECT time,src,name,msg FROM messages ORDER BY -time LIMIT 100")

        trows = [(["time","ip","name","message"], {"class":"tblhead"}),]
        trows += [ [(time.ctime(m[0]), {"class":"neutral"}), (m[1] if m[1] else "???", {"align":"right", "style":"font-weight:bold"}), m[2] if m[2] else "???", (asciistrip(m[3]),{"class":"neutral" if m[2]==self.name else "good"})] for m in self.curs.fetchall() ]
        return makeTable(trows)

    def makePage(self, groupid=None):
        P,b = makePageStructure("Chat log", refresh=300)
        addTag(b,"h1",contents=["Operators' chat log as of %s"%time.asctime(), makeLink("/index.html","[Home]")])

        F = ET.Element("form", {"action":"/cgi-bin/ChatLog.py", "method":"POST"})
        addTag(F,"label",{"for":"name"},"Name:")
        if self.name: addTag(F,"input", {"type":"text", "name":"name", "id":"name", "size":"10", "value":self.name})
        else: addTag(F,"input", {"type":"text", "name":"name", "id":"name", "size":"10"})
        addTag(F,"label",{"for":"msg"},"Message:")
        addTag(F,"input", {"type":"text", "name":"msg", "id":"msg", "size":"100"})
        addTag(F,"br")
        addTag(F,"input",{"type":"submit","name":"submit","value":"Post"})
        addTag(F,"input",{"type":"submit","name":"refresh","value":"Refresh"})
        addTag(F,"input",{"type":"submit","name":"delete","value":"Delete"})
        b.append(F)

        b.append(self.makeMessageTable(groupid))
        print(docHeaderString())
        print(prettystring(P))

if __name__=="__main__":
    db = "ChatDB.sql"
    #if not os.path.exists(db): os.system("sqlite3 %s < $APP_DIR/autologbook/chat_DB_schema.sql"%db)

    form = cgi.FieldStorage()
    CMD = ChatMessagesDisplay(db)
    CMD.name = asciistrip(form.getvalue("name", None))
    CMD.src = os.environ.get("REMOTE_ADDR", None)
    if "delete" in form: CMD.delMessage()
    if CMD.name and "msg" in form and "submit" in form: CMD.addMessage(form.getvalue("msg"))
    CMD.makePage()
