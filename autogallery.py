#!/bin/env python3

from WebpageUtils import *
import os
import glob
import sys
from optparse import OptionParser

def pdfs_to_svgs(basedir):
    for f in glob.glob(basedir+"/*.pdf"):
        fsvg = f[:-3]+"svg"
        #os.system("rm "+fsvg)
        if not os.path.exists(fsvg): os.system("pdf2svg %s %s"%(f,fsvg))

def makegallery(basedir, css=None, logo=None):
    if css: os.system("cp "+css+" "+basedir)
    if logo: os.system("cp %s %s/logo.svg"%(logo,basedir))

    for path, ds, fs in os.walk(basedir):
        pdfs_to_svgs(path)

        pname = path.strip("/").split("/")[-1]
        Page,b = makePageStructure(pname, css="/sitestyle.css")
        h1 = addTag(b,"h1",{},pname)
        if path != basedir:
            addTag(h1,"a",{"href":"../index.html"},"[Up]")
            #addTag(h1,"a",{"href":"/index.html"},"[Top]")

        fs.sort()
        for f in fs:
            ff = os.path.basename(f)
            if ff == "logo.svg": continue
            if(f[-4:]==".svg"):
                addTag(b,"img", {"src":ff})
            if(f[-4:]==".pdf"):
                addTag(b,"a", {"href":ff}, ff)

        if ds:
            ul = addTag(b,"ul")
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
