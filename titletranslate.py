#
# (C) Rob W.W. Hooft, 2003
#
# Distribute under the terms of the PSF license.
#
__version__ = '$Id$'
#
import re

import wikipedia, date

def sametranslate(pl, arr, same):
    for newcode in wikipedia.family.seriouslangs:
        # Put as suggestion into array
        newname = pl.linkname()
        if newcode in ['eo','cs'] and same == 'name':
            newname = newname.split(' ')
            newname[-1] = newname[-1].upper()
            newname = ' '.join(newname)
        x=wikipedia.PageLink(newcode, newname)
        if x not in arr:
            arr[x] = None

def translate(pl, arr, same = False, hints = None, auto = True):
    if same:
        return sametranslate(pl, arr, same)
    if hints:
        for h in hints:
            if h.find(':') == -1:
                # argument given as -hint:xy where xy is a language code
                codes = h
                newname = ''
            else:
                codes, newname = h.split(':', 1)
            if newname == '':
                # if given as -hint:xy or -hint:xy:, assume that there should
                # be a page in language xy with the same title as the page 
                # we're currently working on
                newname = pl.linkname()
            if codes == 'all':
                codes = wikipedia.family.seriouslangs
            elif codes == '10' or codes == 'main': # names 'main' and 'more' kept for backward compatibility
                codes = wikipedia.family.biglangs
            elif codes == '20' or codes == 'more':
                codes = wikipedia.family.biglangs2
            elif codes == '30':
                codes = wikipedia.family.biglangs3
            elif codes == '50':
                codes = wikipedia.family.biglangs4
            elif codes == 'cyril':
                codes = wikipedia.family.cyrilliclangs
            else:
                codes = codes.split(',')
            for newcode in codes:
                if newcode <> wikipedia.mylang:
                    x = wikipedia.PageLink(newcode, newname)
                    if x not in arr:
                        arr[x] = None
    # Autotranslate dates into some other languages, the rest will come from
    # existing interwiki links.
    if date.datetable.has_key(wikipedia.mylang) and auto:
        dt='(\d+) (%s)' % ('|'.join(date.datetable[wikipedia.mylang].keys()))
        Rdate = re.compile(dt)
        m = Rdate.match(pl.linkname())
        if m:
            for newcode, fmt in date.datetable[wikipedia.mylang][m.group(2)].items():
                newname = fmt % int(m.group(1))
                x = wikipedia.PageLink(newcode,newname)
                if x not in arr:
                    arr[x] = None
            return

    # Autotranslate years A.D.
    Ryear = re.compile('^\d+$')
    m = Ryear.match(pl.linkname())
    if m and auto:
        i=int(m.group(0))
        if i==0:
            return
        if wikipedia.mylang in ['ja','zh','ko','la']:
            return
        if wikipedia.mylang=='ia' and i<1400:
            return
        if wikipedia.mylang=='simple' and i<200:
            return
        for newcode in wikipedia.family.seriouslangs:
            if newcode in ['ja', 'zh']:
                fmt = '%d&#24180;'
            elif newcode == 'ko':
                fmt = '%d&#45380;'
            else:
                fmt = '%d'
            if newcode == 'ja' and i<1900:
                # ja pages before 1900 are redirects
                pass
            elif newcode == 'ia' and i<1400:
                # some ia pages are numbers
                pass
            elif newcode == 'simple' and i<200:
                # some simple pages are numbers
                pass
            elif newcode == 'la':
                # la pages are not years but numbers
                pass
            elif newcode in ['mr', 'id', 'lv', 'sw', 'tt']:
                # years do not exist
                pass
            else:
                newname = fmt%i 
                x=wikipedia.PageLink(newcode, newname)
                if x not in arr:
                    arr[x] = None
        return

    # Autotranslate years B.C.
    if date.yearBCfmt.has_key(wikipedia.mylang) and auto:
        dt=date.yearBCfmt[wikipedia.mylang]
        dt = re.compile('%d').sub('(\d+)',dt)
        Ryear = re.compile(dt)
        m = Ryear.match(pl.linkname())
        if m:
            m = int(m.group(1))
            for newcode in wikipedia.family.seriouslangs:
                include = True
                if date.maxyearBC.has_key(newcode):
                    if m > date.maxyearBC[newcode]:
                        include = False
                if include:
                    fmt = date.yearBCfmt.get(newcode)
                    if fmt:
                        newname = fmt % m
                        x=wikipedia.PageLink(newcode, newname)
                        if x not in arr:
                            arr[x] = None
            return
