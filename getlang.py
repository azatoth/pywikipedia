#
# Script to check language links for years A.D.
#
# (C) Rob W.W. Hooft, 2003
# Distribute under the terms of the GPL.

import sys,copy,wikipedia

# languages to check for missing links and modify
mylangs = ('nl', )

# selection of years to check
years = range(900,999+1)
#years=[879]

# Set to 1 to actually change the pages
forreal = 1

# Summary used in the modification request
wikipedia.setAction('Rob Hooft: automatic interwiki script for years')

debug = 0

def findlangs(year):
    matrix={}
    text={}
    print year,"=",
    missing=0
    for code in wikipedia.languages(mylangs):
        print code+":", ; sys.stdout.flush()
        try:
            t=wikipedia.getPage(code,year)
        except wikipedia.NoPage:
            if code in mylangs:
                missing+=1
                if missing==len(mylangs):
                    # None of the mylangs has this page. Doesn't make sense.
                    print
                    return None,None
            pass
        else:
            text[code]=t
            l=wikipedia.getLanguageLinks(t)
            l[code]=year # Add self-reference
            matrix[code]=l
    print
    return text,matrix

def assemblelangmatrix(m):
    result={}
    for dum,line in m.iteritems():
        for code,name in line.iteritems():
            if not code in m:
                pass
                #print "WARNING: Ignore %s from %s; did not see actual page there"%(code,dum)
            elif code in result:
                if result[code]!=name:
                    print "WARNING: Name %s is either %s or %s"%(code,result[code],name)
            else:
                result[code]=name
    return result

def missingLanguages(m,line,thiscode):
    # Figure out whether any references in the assembled references mentioned in
    # line are missing from the language page referred by thiscode.
    result={}
    for code,name in line.iteritems():
        if code==thiscode:
            pass
        elif code in m[thiscode]:
            pass
        else:
            result[code]=name
    for code,name in m[thiscode].iteritems():
        if not code in line:
            print "WARNING: %s contains reference to unknown %s:%s"%(thiscode,code,name)
        elif line[code]!=name:
            print "WARNING: %s reference to %s is %s and not %s"%(thiscode,code,name,line[code])
    return result

def compareLanguages(old,new):
    removing=[]
    adding=[]
    for code,name in old.iteritems():
        if not new.has_key(code):
            removing.append(code)
    for code,name in new.iteritems():
        if not old.has_key(code):
            adding.append(code)
    s=""
    if adding:
        s=s+" Adding:"+",".join(adding)
    if removing:
        s=s+" Removing:"+",".join(removing)
    return s

for year in years:
    text,m=findlangs(str(year))
    if m is None:
        # None of the mylangs has this page
        continue
    proper=assemblelangmatrix(m)
    for mycode in mylangs:
        if mycode in m: # Page must be present in this language
            ml=copy.copy(proper)
            status=compareLanguages(m[mycode],ml)
            if status:
                print mycode,str(year),":",status
            del ml[mycode]
            s=wikipedia.interwikiFormat(ml)
            newtext=s+wikipedia.removeLanguageLinks(text[mycode])
            if debug:
                print newtext
            if newtext!=text[mycode]:
                print "NOTE: Replacing %s: %s"%(mycode,s)
                if forreal:
                    status,reason,data=wikipedia.putPage(mycode,str(year),newtext)
                    if str(status)!='302':
                        print status,reason
