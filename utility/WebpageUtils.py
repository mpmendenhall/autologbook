#!/bin/env python3

# cgi web-printable tracebacks
import cgitb
cgitb.enable()
import xml.etree.ElementTree as ET
from xml.dom import minidom

def makeLink(href, content, xargs = {}):
    """Make <a href=...>contents</a> link tag"""
    xargs["href"] = href
    a = ET.Element('a', xargs)
    if ET.iselement(content): a.append(content)
    else: a.text = str(content)
    return a

def isattrtuple(e): return isinstance(e, tuple) and len(e)==2 and isinstance(e[1],dict)

def mergecontents(e, contents, prevel = None):
    """Recursively merge mixed text/tag contents into e"""
    if ET.iselement(contents):
        e.append(contents)
        prevel = contents
    elif isinstance(contents, tuple) or isinstance(contents, list):
        for c in contents:
            if ET.iselement(c):
                e.append(c)
                prevel = c
            elif c is not None:
                mergecontents(e, c, prevel)
    elif contents is not None:
        cs = str(contents)
        if prevel is not None:
            prevel.tail = prevel.tail + cs if prevel.tail else cs
        else:
            e.text = e.text + cs if e.text else cs

def addTag(parent, tag, xargs = {}, contents = None):
    e = ET.SubElement(parent, tag, xargs) if parent is not None else ET.Element(tag, xargs)
    mergecontents(e,contents)
    return e

def makeCheckbox(name, value="y", checked=False, radio=False, xargs={}):
    """HTML for checkbox control"""
    xargs["name"] = name
    xargs["value"] = value
    xargs["type"] = "radio" if radio else "checkbox"
    if checked: xargs["checked"] = ""
    return ET.Element('input', xargs)

def makeList(items, xargs={}, toptag='ul', itmtag='li'):
    """HTML list"""

    L = ET.Element(toptag, xargs)

    for i in items:
        if isattrtuple(i): addTag(L, itmtag, xargs=i[1], contents = i[0])
        else: addTag(L, itmtag, contents = i)

    return L

def makeTable(rows, xargs={}, T = None):
    """HTML table from [r,r,...]; r = elem | [c,c,...] | ([c,c,...], {rowattrs}); c = elem | text | (text,{colattrs})"""

    if isinstance(T,str): T = ET.Element(T, xargs)
    if T is None: T = ET.Element('table', xargs)

    for r in rows:
        if ET.iselement(r): T.append(r)
        elif isattrtuple(r): T.append(makeList(r[0], xargs=r[1], toptag='tr', itmtag='td'))
        else: T.append(makeList(r, toptag='tr', itmtag='td'))

    return T



def prettystring(elem, oneline = False):
    """ElementTree element to indented string"""
    if oneline: s = ET.tostring(elem).decode('utf-8')
    else:
        #s = ET.tostring(elem).decode('utf-8')
        reparsed = minidom.parseString(ET.tostring(elem).decode('utf-8'))
        s = reparsed.toprettyxml().split('<?xml version="1.0" ?>\n')[-1]
    return s.replace('Ω',"&#937;").replace('μ',"&#956;")


def fillColumns(itms, cols):
    """Transpose collection into columns; return rows"""
    nbt = len(itms)
    cols = int(cols)
    nrows = nbt//cols+(nbt%cols>0)
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

    return tdat

def fillTable(itms,xargs={},cols=4):
    """Flow items into table with specified number of columns"""
    return makeTable(fillColumns(itms,cols),xargs)


def docHeaderString():
    """XHTML5 MIME type header string"""
    #return 'Content-Type: application/xhtml+xml\n\n<!DOCTYPE html>\n'
    return 'Content-Type: application/xhtml+xml\n\n' # no DOCTYPE with this header

def makePageStructure(title="", refresh=None, css="../sitestyle.css"):
    """Generic page skeleton"""
    P = ET.Element('html', {"lang":"en-US", "xml:lang":"en-US", "xmlns":"http://www.w3.org/1999/xhtml"})

    hd = ET.SubElement(P, 'head')
    if title:
        ttl = ET.SubElement(hd, 'title')
        ttl.text = title
    ET.SubElement(hd, 'link', {"rel":"stylesheet", "href":css})
    ET.SubElement(hd, 'link', {"rel":"icon", "type":"image/png", "sizes":"32x32", "href":"/icons/favicon-32x32.png"})
    ET.SubElement(hd, 'meta', {"charset":"utf-8"})
    if refresh:
        ET.SubElement(hd, 'meta', {"http-equiv":"refresh", "content":"%i"%refresh})

    b = ET.SubElement(P, "body")
    return (P,b)

def timeWriter(t):
    """Convert time in seconds to string with units"""
    if abs(t) < 60:
        return "%i seconds"%t
    if abs(t) < 3600:
        return "%.1f minutes"%(t/60.0)
    if abs(t) < 3600*24:
        return "%.1f hours"%(t/3600.0)
    return "%.1f days"%(t/(24*3600.0))
