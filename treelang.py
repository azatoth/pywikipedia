# Script to check language links for general pages
#
# $Id$
#
# (C) Rob W.W. Hooft, 2003
# Distribute under the terms of the GPL.

import sys,copy,wikipedia,re

# language to check for missing links and modify
mylang = 'nl'

# Summary used in the modification request
wikipedia.setAction('Rob Hooft: semi-automatic interwiki script')

debug = 1
forreal = 1

datetable={
    'januari':{'en':'January %d','de':'%d. Januar','fr':'%d janvier','af':'01-%02d'},
    'februari':{'en':'February %d','de':'%d. Februar','fr':'%d fevrier','af':'02-%02d'},
    'maart':{'en':'March %d','de':'%d. M&auml;rz','fr':'%d mars','af':'03-%02d'},
    'april':{'en':'April %d','de':'%d. April','fr':'%d avril','af':'04-%02d'},
    'mei':{'en':'May %d','de':'%d. Mai','fr':'%d mai','af':'05-%02d'},
    'juni':{'en':'June %d','de':'%d. Juni','fr':'%d juin','af':'06-%02d'},
    'juli':{'en':'July %d','de':'%d. Juli','fr':'%d juillet','af':'07-%02d'},
    'augustus':{'en':'August %d','de':'%d. August','fr':'%d aout','af':'08-%02d'},
    'september':{'en':'September %d','de':'%d. September','fr':'%d septembre','af':'09-%02d'},
    'oktober':{'en':'October %d','de':'%d. Oktober','fr':'%d octobre','af':'10-%02d'},
    'november':{'en':'November %d','de':'%d. November','fr':'%d novembre','af':'11-%02d'},
    'december':{'en':'December %d','de':'%d. Dezember','fr':'%d decembre','af':'12-%02d'},
}

def autotranslate(name,arr):
    # Autotranslate dates into some other languages, the rest will come from
    # existing interwiki links.
    Rdate=re.compile('(\d+)_(%s)'%('|'.join(datetable.keys())))
    m=Rdate.match(name)
    if m:
        for newcode,fmt in datetable[m.group(2)].items():
            newname=fmt%int(m.group(1))
            # Standardize
            newname=wikipedia.url2link(newname)
            newname=wikipedia.link2url(newname)
            # Put as suggestion into array
            arr[newcode,newname]=None
            
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
    
def treestep(arr,code,name):
    assert arr[code,name] is None
    try:
        print "Getting %s:%s"%(code,name)
    except ValueError:
        print "Getting",(code,name)
    n=0
    try:
        text=wikipedia.getPage(code,name)
    except wikipedia.NoPage:
        print "---> Does not actually exist"
        arr[code,name]=''
        return 0
    except wikipedia.IsRedirectPage,arg:
        arg=str(arg)
        newname=arg[0].upper()+arg[1:]
        newname=newname.strip()
        newname=wikipedia.link2url(newname)
        arr[code,name]=''
        print "NOTE: %s:%s is a redirect to %s"%(code,name,arg)
        if not (code,newname) in arr:
            arr[code,newname]=None
            return 1
        return 0
    arr[code,name]=text
    for newcode,newname in wikipedia.getLanguageLinks(text).iteritems():
        # Recognize and standardize for Wikipedia
        newname=newname[0].upper()+newname[1:]
        newname=newname.strip()
        newname=wikipedia.link2url(newname)
        if not (newcode,newname) in arr:
            lname=wikipedia.url2link(newname)
            print "NOTE: from %s:%s we got the new %s:%s"%(code,name,newcode,lname)
            arr[newcode,newname]=None
            n+=1
    return n
    
def treesearch(code,name):
    arr={(code,name):None}
    autotranslate(name,arr)
    modifications=1
    while modifications:
        modifications=0
        for newcode,newname in arr.keys():
            if arr[newcode,newname] is None:
                modifications+=treestep(arr,newcode,newname)
    return arr

name=[]

ask=1
for arg in sys.argv[1:]:
    if arg=='-force':
        ask=0
    else:
        name.append(arg)
    
name='_'.join(name)
if not name:
    name=raw_input('Which page to check:')

name=wikipedia.link2url(name)

m=treesearch(mylang,name)
print "==Result=="
new={}
k=m.keys()
k.sort()
old=None
for code,cname in k:
    if code==mylang:
        if m[code,cname]:
            old=wikipedia.getLanguageLinks(m[code,cname])
            oldtext=m[code,cname]
    elif m[(code,cname)]:
        print "%s:%s"%(code,wikipedia.url2link(cname))
        if new.has_key(code):
            print "ERROR: %s has '%s' as well as '%s'"%(code,new[code],wikipedia.url2link(cname))
            while 1:
                answer=raw_input("Use former (f) or latter (l)?")
                if answer.startswith('f'):
                    break
                elif answer.startswith('l'):
                    new[code]=wikipedia.url2link(cname)
                    break
        else:
            new[code]=wikipedia.url2link(cname)
print "==status=="
if old is None:
    sys.exit(1)
#print old
print compareLanguages(old,new)
print "==upload=="
s=wikipedia.interwikiFormat(new)
s2=wikipedia.removeLanguageLinks(oldtext)
if not s2.startswith('\r\n'):
    s2='\r\n'+s2
newtext=s+s2
if debug:
    print s
if newtext!=oldtext:
    print "NOTE: Replacing %s: %s"%(mylang,name)
    if forreal:
        if ask:
            answer=raw_input('submit y/n ?')
        else:
            answer='y'
        if answer=='y':
            status,reason,data=wikipedia.putPage(mylang,name,newtext)
            if str(status)!='302':
                print status,reason
