#!/bin/env python3

from WebpageUtils import *
import os
import glob
import sys
from optparse import OptionParser
import datetime

def pdfs_to_svgs(basedir, do_gzip = True):
    for f in glob.glob(basedir+"/*.pdf"):
        fsvg = f[:-3]+"svg"
        if not os.path.exists(fsvg+('z' if do_gzip else '')): os.system("pdf2svg %s %s"%(f,fsvg))
        if do_gzip: os.system("gzip %s; mv %s.gz %sz"%(fsvg,fsvg,fsvg))

def makegallery(basedir, css=None, logo=None):
    if css: os.system("cp "+css+" "+basedir)
    if logo: os.system("cp %s %s/logo.%s"%(logo,basedir,logo.split('.')[-1]))

    for path, ds, fs in os.walk(basedir):
        pdfs_to_svgs(path)

    for path, ds, fs in os.walk(basedir):
        pname = path.strip("/").split("/")[-1]
        Page,b = makePageStructure(pname, css="/sitestyle.css")
        h1 = addTag(b,"h1",{},pname)
        if path != basedir:
            addTag(h1,"a",{"href":"../index.html"},"[Up]")
            #addTag(h1,"a",{"href":"/index.html"},"[Top]")

        ul = addTag(b,"ul")

        fs.sort()
        for f in fs:
            if f[:5] == "logo.": continue
            if f[-4:]==".svg" or f[-5:]==".svgz":
                li = addTag(ul,"li")
                addTag(li,"img", {"src":f})
            if f[-4:]==".pdf":
                li = addTag(ul,"li")
                addTag(li,"a", {"href":f}, f+", generated "+datetime.datetime.fromtimestamp(os.stat(path+"/"+f).st_mtime).strftime('%a, %b %-d %-H:%M:%S'))

        ds.sort()
        for d in ds:
            li = addTag(ul,"li")
            addTag(li, "a", {"href":"%s/index.html"%d},d)

        open(path+"/index.html","w").write("<!DOCTYPE html>\n"+prettystring(Page))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--dir",  help="base content directory")
    parser.add_option("--css",  default="web_interface/sitestyle.css", help="css file to copy to base")
    parser.add_option("--logo", help="logo.svg file to copy to base")
    options, args = parser.parse_args()

    makegallery(options.dir, options.css, options.logo)
