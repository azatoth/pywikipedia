"""
Script to extract all wiki page names a certain HTML file points to in
interwiki-link format

The output can be used as input to interwiki.py.

This script takes a single file name argument, the file should be a HTML file
as captured from one of the wikipedia servers.

Arguments:
-sorted     Print the pages sorted alphabetically (default: the order in which
            they occur in the HTML file)
"""
#
# (C) Rob W.W. Hooft, Andre Engels, 2003-2004
#
# Distribute under the terms of the PSF license.
#
__version__='$Id$'
#
import sys,re,wikipedia
R = re.compile('/wiki/(.*?)" *')
fn = []
sorted = False
list = []

for arg in sys.argv[1:]:
    arg = wikipedia.argHandler(arg)
    if arg:
        if arg=="-sorted":
            sorted = True
        elif fn:
            print "Ignoring argument %s"%arg
        else:
            fn = arg

if not fn:
    print "No file specified to get the links from"
    sys.exit(1)

mysite = wikipedia.getSite()

f=open(fn)
text=f.read()
f.close()
for hit in R.findall(text):
    list += [mysite.linkto(hit)]
if sorted:
    list.sort()
for page in list:
    print page
