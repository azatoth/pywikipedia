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
    for newcode in wikipedia.seriouslangs:
        # Put as suggestion into array
        newname = pl.linkname()
        if newcode in ['eo','cs'] and same == 'name':
            newname = newname.split(' ')
            newname[-1] = newname[-1].upper()
            newname = ' '.join(newname)
        x=wikipedia.PageLink(newcode, newname)
        if x not in arr:
            arr[x] = None

def translate(pl, arr, same = False, hints = None):
    if same:
        return sametranslate(pl, arr, same)
    if hints:
        for h in hints:
            codes, newname = h.split(':', 1)
            if codes == 'all':
                codes = wikipedia.seriouslangs
            elif codes == 'main':
                codes = wikipedia.biglangs
            elif codes == 'more':
                codes = wikipedia.biglangs2
            else:
                codes = codes.split(',')
            for newcode in codes:
                x = wikipedia.PageLink(newcode, newname)
                if x not in arr:
                    arr[x] = None
    # Autotranslate dates into some other languages, the rest will come from
    # existing interwiki links.
    if date.datetable.has_key(wikipedia.mylang):
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
    if m:
        i=int(m.group(0))
        for newcode in wikipedia.seriouslangs:
            if newcode in ['ja', 'zh']:
                fmt = '%d&#24180;'
            else:
                fmt = '%d'
            if newcode == 'ja' and i<1900:
                # ja pages before 1900 are redirects
                pass
            elif newcode == 'ia' and i<1400:
                # some ia pages are numbers
                pass
            elif newcode == 'la':
                # la pages are not years but numbers
                pass
            elif newcode in ['eu', 'gl', 'mr', 'id', 'lv', 'sw', 'tt', 'zh']:
                # years do not exist
                pass
            elif newcode == 'nds' and i<2000 or i>2010:
                # nds years do not exist except for 2003
                pass
            else:
                newname = fmt%i 
                x=wikipedia.PageLink(newcode, newname)
                if x not in arr:
                    arr[x] = None
        return

    # Autotranslate years B.C.
    if wikipedia.mylang == 'nl':
        Ryear = re.compile('^(\d+)_v._Chr.')
        m = Ryear.match(pl.linkname())
        if m:
            for newcode in wikipedia.seriouslangs:
                fmt = date.yearBCfmt.get(newcode)
                if fmt:
                    newname = fmt % int(m.group(1))
                    x=wikipedia.PageLink(newcode, newname)
                    if x not in arr:
                        arr[x] = None
            return
