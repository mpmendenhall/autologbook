#!/usr/bin/python3

# cgi web-printable tracebacks
import cgitb
cgitb.enable()
import xml.etree.ElementTree as ET

def makeLink(href, content, xargs = {}):
    xargs["href"] = href
    a = ET.Element('a', xargs)
    if ET.iselement(content):
        a.append(content)
    else:
        a.text = str(content)
    return a

def makeCheckbox(name,value,label="",checked=False,radio=False):
    """HTML for checkbox control"""
    itype = "radio"
    if not radio:
        itype = "checkbox"
    checkstr = ""
    if checked:
        checkstr = "checked"
    htmlstr = '<input type="%s" name="%s" value="%s" %s/>%s'%(itype,name,value,checkstr,label)
    return htmlstr

def makeTable(rows, xargs={}):
    """HTML table from array of lists or {"class":c "data":d}"""
    T = ET.Element('table', xargs)
    
    for r in rows:
        if ET.iselement(r):
           T.append(r)
           continue
       
        if type(r) == type({}):
            rdat = r["data"]
            rw = ET.SubElement(T, 'tr', {"class":r["class"]})
        else:
            rdat = r
            rw = ET.SubElement(T, 'tr')
            
        for c in rdat:
            td = ET.SubElement(rw, 'td')
            if ET.iselement(c):
                td.append(c)
            else:
                td.text = str(c)
    
    return T

def fillTable(itms,cols=4):
    """Flow items into table with specified number of columns"""
    
    # transpose order to fill in by column
    nbt = len(itms)
    cols = int(cols)
    nrows = nbt/cols+(nbt%cols>0)
    lastrow = (nbt-1)%cols+1
    bcols = [[] for c in range(cols)]

    cn = 0
    rn = 0
    for (n,b) in enumerate(itms):
        if rn >= nrows-(cn>=lastrow):
            rn = 0
            cn += 1
        bcols[cn].append(b)
        rn += 1
    
    # fill table data
    tdat = []
    for r in range(nrows):
        tdat.append([])
        for c in range(cols):
            if r >= len(bcols[c]):
                continue
            tdat[-1].append(bcols[c][r])
        
    return makeTable(tdat)

def pageHeader(title="",refresh=None):
    """Generic page header"""
    htmlstr = 'Content-Type: text/html\n\n'
    htmlstr += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n\n'
    htmlstr += '<html lang="en-US" xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml">\n\n'
    htmlstr += '<head>\n'
    if title:
        htmlstr += '\t<title>%s</title>\n'%title
    htmlstr += '\t<link rel="stylesheet" href="../sitestyle.css">\n'
    if refresh:
        htmlstr += '\t<meta http-equiv="refresh" content="%i">\n'%refresh
    htmlstr += '</head>\n'
    htmlstr += '<body>\n'
    return htmlstr
  
def pageFooter():
    """Generic page footer"""
    return '</body>\n</html>\n'

def timeWriter(t):
    """Convert time in seconds to string with units"""
    if abs(t) < 60:
        return "%i seconds"%t
    if abs(t) < 3600:
        return "%.1f minutes"%(t/60.0)
    if abs(t) < 3600*24:
        return "%.1f hours"%(t/3600.0)
    return "%.1f days"%(t/3600.0/3600.0)
