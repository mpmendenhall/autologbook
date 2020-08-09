#!/bin/env python3
## \file autogallery.py Generate static HTML browsable gallery from files hieararchy

from WebpageUtils import *
import os
import glob
import sys
from optparse import OptionParser
import datetime

def pdfs_to_svgs(basedir, do_gzip = True):
    for f in glob.glob(basedir+"/*.pdf"):
        fsvg = f[:-3]+"svg"
        fsvgz = fsvg+('z' if do_gzip else '')
        makesvg = not os.path.exists(fsvgz)
        if not makesvg: makesvg = os.stat(fsvgz).st_mtime < os.stat(f).st_mtime
        if makesvg:
            os.system("pdf2svg %s %s"%(f,fsvg))
            if do_gzip: os.system("gzip %s; mv %s.gz %sz"%(fsvg,fsvg,fsvg))

def makegallery(basedir, css=None, logo=None):
    if css: os.system("cp "+css+" "+basedir+"/sitestyle.css")
    if logo: os.system("cp %s %s/logo.%s"%(logo,basedir,logo.split('.')[-1]))

    for path, ds, fs in os.walk(basedir):
        pdfs_to_svgs(path)

    for path, ds, fs in os.walk(basedir):
        pname = path.strip("/").split("/")[-1]
        Page,b = makePageStructure(pname, css="/sitestyle.css")
        h1 = addTag(b,"h1",{},pname)
        if path != basedir: addTag(h1,"a",{"href":"../index.html"},"[Up]")
        addTag(h1,"a",{"href":"/index.html"},"[Home]")

        linklist = []
        ds.sort()
        for d in ds:
            li = ET.Element("li")
            addTag(li, "a", {"href":"%s/index.html"%d},d)
            linklist.append(li)

        fs.sort()
        for f in fs:
            sfx = f.split(".")[-1]
            pfx = f[:-len(sfx)-1]
            if pfx == "logo": continue
            if sfx in ["svg", "svgz"]:
                fg = addTag(b,"figure", {"style":"display:inline-block"})
                addTag(fg,"img", {"src":f, "class":"lightbg"})
                cc = []
                if os.path.exists(path+"/"+pfx+".pdf"):
                    cc.append(makeLink(pfx+".pdf", pfx+".pdf"))
                else: cc.append(f+" ")
                cc.append("generated "+datetime.datetime.fromtimestamp(os.stat(path+"/"+f).st_mtime).strftime('%a, %b %-d %-H:%M:%S'))
                addTag(fg,"figcaption",{},cc)
            if sfx in ["pdf", "txt", "tsv"]:
                if sfx == "pdf" and os.path.exists(path+"/"+pfx+".svgz"): continue
                li = ET.Element("li")
                addTag(li,"a", {"href":f}, f+", generated "+datetime.datetime.fromtimestamp(os.stat(path+"/"+f).st_mtime).strftime('%a, %b %-d %-H:%M:%S'))
                linklist.append(li)

        if linklist: addTag(b, "ul", {}, linklist)


        open(path+"/index.html","w").write("<!DOCTYPE html>\n"+prettystring(Page))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--dir",  help="base content directory")
    parser.add_option("--css",  default="web_interface/sitestyle.css", help="css file to copy to base")
    parser.add_option("--logo", help="logo.svg file to copy to base")
    options, args = parser.parse_args()

    if options.dir: makegallery(options.dir, options.css, options.logo)
