"""
Script to help a human solve disambiguations by presenting a set of options.

Specify the disambiguation page on the command line. The program will
pick up the page, and look for all alternative links, and show them with
a number adjacent to them. It will then automatically loop over all pages
referring to the disambiguation page, and show 30 characters on each side
of the reference to help you make the decision between the
alternatives. It will ask you to type the number of the appropriate
replacement, and perform the change robotically.

It is possible to choose to replace only the link (just type the number) or
replace both link and link-text (type 'r' followed by the number).

Multiple references in one page will be scanned in order, but typing 'n' on
any one of them will leave the complete page unchanged; it is not possible to
leave only one reference unchanged.

Command line options:

   -pos:XXXX adds XXXX as an alternative disambiguation

   -just     only use the alternatives given on the command line, do not 
             read the page for other possibilities

Options that are accepted by more robots:

   -lang:XX  set your home wikipedia to XX instead of the one given in
             username.dat
             
To complete a move of a page, one can use:

    python solve_disambiguation.py -just -pos:New_Name Old_Name
"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distribute under the terms of the PSF license.
#
__version__='$Id$'
#
import wikipedia,re,sys

if not wikipedia.special.has_key(wikipedia.mylang):
    print "Please add the translation for the Special: namespace in"
    print "Your home wikipedia to the wikipedia.py module"
    import sys
    sys.exit(1)

msg={
    'en':'Robot-assisted disambiguation',
    'da':'Retter flertydigt link til',
    'nl':'Robot-geholpen doorverwijzing',
    'fr':'Homonymie r\xE9solue \xE0 l\'aide du robot'
    }

ignore={
    'nl':('Wikipedia:Onderhoudspagina',
          'Wikipedia:Doorverwijspagina'),
    'en':('Wikipedia:Links to disambiguating pages',
          'Wikipedia:Disambiguation pages with links',
          'Wikipedia:Multiple-place names (A)',
          'Wikipedia:Multiple-place names (B)',
          'Wikipedia:Multiple-place names (C)',
          'Wikipedia:Multiple-place names (D)',
          'Wikipedia:Multiple-place names (E)',
          'Wikipedia:Multiple-place names (F)',
          'Wikipedia:Multiple-place names (G)',
          'Wikipedia:Multiple-place names (H)',
          'Wikipedia:Multiple-place names (I)',
          'Wikipedia:Multiple-place names (J)',
          'Wikipedia:Multiple-place names (K)',
          'Wikipedia:Multiple-place names (L)',
          'Wikipedia:Multiple-place names (M)',
          'Wikipedia:Multiple-place names (N)',
          'Wikipedia:Multiple-place names (O)',
          'Wikipedia:Multiple-place names (P)',
          'Wikipedia:Multiple-place names (Q)',
          'Wikipedia:Multiple-place names (R)',
          'Wikipedia:Multiple-place names (S)',
          'Wikipedia:Multiple-place names (T)',
          'Wikipedia:Multiple-place names (U)',
          'Wikipedia:Multiple-place names (V)',
          'Wikipedia:Multiple-place names (W)',
          'Wikipedia:Multiple-place names (X)',
          'Wikipedia:Multiple-place names (Y)',
          'Wikipedia:Multiple-place names (Z)',
          'Wikipedia:Non-unique personal name'),
    'da':('Wikipedia:Links til sider med flertydige titler'),
    'fr':('Wikip\xE9dia:Liens aux pages d\'homonymie ')
    }

def getReferences(pl):
    x = wikipedia.getReferences(pl)
    # Remove ignorables
    if ignore.has_key(pl.code()):
        ig=ignore[pl.code()]
        for i in range(len(x)-1, -1, -1):
            if x[i] in ig:
                del x[i]
    return x

wrd = []
alternatives = []
getalternatives = 1
debug = 0

for arg in sys.argv[1:]:
    if wikipedia.argHandler(arg):
        pass
    elif arg.startswith('-pos:'):
        alternatives.append(arg[5:])
    elif arg=='-just':
        getalternatives=0
    else:
        wrd.append(arg)

wrd = ' '.join(wrd)

if msg.has_key(wikipedia.mylang):
    msglang = wikipedia.mylang
else:
    msglang = 'en'

wikipedia.setAction(msg[msglang]+': '+wrd)

thispl = wikipedia.PageLink(wikipedia.mylang, wrd)

if getalternatives:
    thistxt = thispl.get()

    w=r'([^\]\|]*)'
    Rlink = re.compile(r'\[\['+w+r'(\|'+w+r')?\]\]')

    for a in Rlink.findall(thistxt):
        alternatives.append(a[0])

for i in range(len(alternatives)):
    print "%3d"%i,alternatives[i]

def treat(refpl):
    try:
        reftxt=refpl.get()
    except wikipedia.IsRedirectPage:
        pass
    else:
        n = 0
        curpos = 0
        while 1:
            for Rthis in exps:
                m=Rthis.search(reftxt, pos = curpos)
                if m:
                    break
            else:
                if n == 0:
                    print "Not found in %s"%refpl
                elif not debug:
                    refpl.put(reftxt)
                return
            # Make sure that next time around we will not find this same hit.
            curpos = m.start() + 1 
            n += 1
            context = 30
            while 1:
                print "== %s =="%(refpl)
                print reftxt[max(0,m.start()-context):m.end()+context]
                choice=raw_input("Which replacement (#,r#,n=none,q=quit,m=more context,l=list,a=add new):")
                if choice=='n':
                    choice=-1
                    return
                elif choice=='a':
                    ns=raw_input('New alternative:')
                    alternatives.append(ns)
                elif choice=='q':
                    sys.exit(0)
                    break
                elif choice=='m':
                    context*=2
                elif choice=='l':
                    for i in range(len(alternatives)):
                        print "%3d" % i,alternatives[i]
                else:
                    if choice[0] == 'r':
                        replaceit = 1
                        choice = choice[1:]
                    else:
                        replaceit = 0
                    try:
                        choice=int(choice)
                    except ValueError:
                        pass
                    else:
                        break
            if choice<0:
                continue
            g1=m.group(1)
            g2=m.group(2)
            if g2:
                g2=g2[1:]
            else:
                g2=g1
            if replaceit or alternatives[choice] == g2:
                reptxt = alternatives[choice]
            else:
                reptxt = "%s|%s" % (alternatives[choice],g2)
            reftxt = reftxt[:m.start()+2]+reptxt+reftxt[m.end()-2:]
            print reftxt[max(0,m.start()-30):m.end()+30]
        if not debug:
            refpl.put(reftxt)
    
def resafe(s):
    s=s.replace('(','\\(')
    s=s.replace(')','\\)')
    return s

exps=[]
zz='\[\[(%s)(\|[^\]]*)?\]\]'
Rthis=re.compile(zz%resafe(thispl.linkname()))
exps.append(Rthis)
uln=wikipedia.html2unicode(thispl.linkname(),language = wikipedia.mylang)
aln=wikipedia.addEntity(uln)
Rthis=re.compile(zz%resafe(aln))
exps.append(Rthis)
Rthis=re.compile(zz%resafe(thispl.linkname()).lower())
exps.append(Rthis)
Rthis=re.compile(zz%resafe(aln.lower()))
exps.append(Rthis)

for ref in getReferences(thispl):
    refpl=wikipedia.PageLink(wikipedia.mylang, ref)
    treat(refpl)
