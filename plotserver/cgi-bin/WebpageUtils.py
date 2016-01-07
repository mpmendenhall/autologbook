#!/usr/bin/python3

# cgi web-printable tracebacks
import cgitb
cgitb.enable()
import xml.etree.ElementTree as ET
from xml.dom import minidom

def makeLink(href, content, xargs = {}):
    xargs["href"] = href
    a = ET.Element('a', xargs)
    if ET.iselement(content):
        a.append(content)
    else:
        a.text = str(content)
    return a

def addTag(parent, tag, xargs = {}, contents = None):
    e = ET.SubElement(parent, tag, xargs)
    if ET.iselement(contents):
        e.append(contents)
    elif contents:
        e.text = str(contents)
    return e

def makeCheckbox(name, value, checked=False, radio=False, xargs={}):
    """HTML for checkbox control"""
    xargs["name"] = name
    xargs["value"] = value
    xargs["type"] = "radio" if radio else "checkbox"
    if checked:
        xargs["checked"] = ""
    return ET.Element('input', xargs)

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
            addTag(rw, 'td', contents = c)
    
    return T

def prettystring(elem):
    """ElementTree element to indented string"""
    reparsed = minidom.parseString(ET.tostring(elem, 'utf-8'))
    return reparsed.toprettyxml().split('<?xml version="1.0" ?>\n')[-1]

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

def makePageStructure(title="", refresh=None):
    """Generic page skeleton"""
    P = ET.Element('html', {"lang":"en-US", "xml:lang":"en-US", "xmlns":"http://www.w3.org/1999/xhtml"})
    
    hd = ET.SubElement(P, 'head')
    if title:
        ttl = ET.SubElement(hd, 'title')
        ttl.text = title
    ET.SubElement(hd, 'link', {"rel":"stylesheet", "href":"../sitestyle.css"})
    if refresh:
        ET.SubElement(hd, 'meta', {"http-equiv":"refresh", "content":"%i"%refresh})
    
    b = ET.SubElement(P, "body")
    return (P,b)

def docHeaderString():
    return 'Content-Type: application/xhtml+xml\n\n<!DOCTYPE html>\n'

def pageHeader(title="",refresh=None):
    """Generic page header"""
    htmlstr = docHeaderString()
    htmlstr += '<html lang="en-US" xml:lang="en-US" xmlns="http://www.w3.org/1999/xhtml">\n\n'
    htmlstr += '<head>\n'
    if title:
        htmlstr += '\t<title>%s</title>\n'%title
    htmlstr += '\t<link rel="stylesheet" href="../sitestyle.css"/>\n'
    if refresh:
        htmlstr += '\t<meta http-equiv="refresh" content="%i"/>\n'%refresh
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
