#coding: iso-8859-1
"""
This bot finds a collection of pages, starting with a single page. For
each page found, it checks all pages linked form or to the page, and asks
for each page linked from or to it, whether the user wants to include it.
This way, a collection of wikipages about a given subject can be found.

Arguments understood by all bots:
   -lang:XX  set your home wikipedia to XX instead of the one given in
             username.dat

Any other argument is taken as a page that at least has to be in the set.
Note that if a page has spaces in the title, you need to specify them
with _'s. A collection of pages about World War II would thus be gotten
with pagelist.py World_War_II
"""
#
# (C) Andre Engels, 2003
#
# Distribute under the terms of the PSF license.
#
#
import sys, copy, re

import wikipedia

tocheck = []
include = []
exclude = []

for arg in sys.argv[1:]:
    if wikipedia.argHandler(arg):
        pass
    else:
        new=wikipedia.PageLink(wikipedia.mylang,arg)
        tocheck.append(new)

while tocheck <> []:
    pg = tocheck[0]
    tocheck = tocheck[1:]
    if pg.exists():
        if pg.isRedirectPage():
            exclude.append(pg)
            new = pg.getRedirectTo()
            if not (new in tocheck or new in include or new in exclude):
                tocheck.append(wikipedia.PageLink(wikipedia.mylang,new))
        else:
            include.append(pg)
            for new in pg.links():
                if not (new in tocheck or new in include or new in exclude):
                    print("%s")%new
                    answer = raw_input("(y/n)? ")
                    if answer=='y':
                        tocheck.append(wikipedia.PageLink(wikipedia.mylang,new))
                    elif answer=='n':
                        exclude.append(wikipedia.PageLink(wikipedia.mylang,new))
            for new in wikipedia.getReferences(pg):
                if not (new in tocheck or new in include or new in exclude):
                    print("%s")%new
                    answer = raw_input("(y/n)? ")
                    if answer=='y':
                        tocheck.append(wikipedia.PageLink(wikipedia.mylang,new))
                    elif answer=='n':
                        exclude.append(wikipedia.PageLink(wikipedia.mylang,new))
    else:
        exclude.append(pg)
        for new in wikipedia.getReferences(pg):
            if not (new in tocheck or new in include or new in exclude):
                print("%s")%new
                answer = raw_input("(y/n)? ")
                if answer=='y':
                    tocheck.append(wikipedia.PageLink(wikipedia.mylang,new))
                elif answer=='n':
                    exclude.append(wikipedia.PageLink(wikipedia.mylang,new))
    print()

include.sort()
print()
print("Collection of pages complete.")
print("=============================")
for page in include:
    print page.linkname()

 
