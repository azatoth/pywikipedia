"""
A robot to implement backlinks from a interwiki.log file without checking them
against the live wikipedia.

Just run this with the warnfile name as parameter. If not specified, the
default filename for the family and language given by global parameters or
user-config.py will be used.

Example:

   python warnfile.py -lang:es

"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distribute under the terms of the PSF license.
# 
__version__ = '$Id$'
#
import wikipedia, interwiki
import sys, re

class WarnfileReader:
    def __init__(self, filename):
        self.filename = filename

    def getHints(self):
        print "Parsing warnfile..."
	R=re.compile(r'WARNING: (?P<family>.+?): \[\[(?P<locallang>.+?):(?P<localtitle>.+?)\]\](?P<warningtype>.+?)\[\[(?P<targetsite>.+?):(?P<targettitle>.+?)\]\]')
        import codecs
        f = codecs.open(self.filename, 'r', 'utf-8')
        hints={}
        removeHints={}
        mysite=wikipedia.getSite()
        for line in f.readlines():
            m=R.search(line)
            if m:
                #print "DBG>",line
                if m.group('locallang') == mysite.lang and m.group('family') == mysite.family.name:
                    #wikipedia.output(u' '.join([m.group('locallang'), m.group('localtitle'), m.group('warningtype'), m.group('targetsite'), m.group('targettitle')]))
                    #print m.group(3)
                    removing = (m.group('warningtype') == ' links to incorrect ')
                    try:
                        if ':' in m.group('targetsite'):
                            family, lang = m.group('targetsite').split(':')
                            thesite = wikipedia.getSite(code=lang, fam=family)
                        else:
                            thesite = mysite.getSite(code = m.group('targetsite'))
                        targetPl = wikipedia.Page(thesite, m.group('targettitle'))
                        if removing:
                            if not removeHints.has_key(m.group('localtitle')):
                                removeHints[m.group('localtitle')]=[]
                            removeHints[m.group('localtitle')].append(targetPl)
                        else:
                            if not hints.has_key(m.group('localtitle')):
                                hints[m.group('localtitle')]=[]
                            hints[m.group('localtitle')].append(targetPl)
                    except wikipedia.Error:
                        print "DBG> Failed to add", line
                    #print "DBG> %s : %s" % (m.group(2), hints[m.group(2)])
        f.close()
        return hints, removeHints
    
class WarnfileRobot:
    def __init__(self, warnfileReader):
        self.warnfileReader = warnfileReader

    def run(self):
        hints, removeHints = self.warnfileReader.getHints()
        k=hints.keys()
        k.sort()
        print "Fixing... %d pages" % len(k)
        for pagename in k:
            pl = wikipedia.Page(wikipedia.getSite(), pagename)
            old={}
            try:
                for pl2 in pl.interwiki():
                    old[pl2.site()] = pl2
            except wikipedia.IsRedirectPage:
                wikipedia.output(u"%s is a redirect page; not changing" % pl.aslink())
                continue
            except wikipedia.NoPage:
                wikipedia.output(u"Page %s not found; skipping" % pl.aslink())
                continue
            new={}
            new.update(old)
            if hints.has_key(pagename):
                for pl2 in hints[pagename]:
                    site = pl2.site()
                    new[site] = pl2
            if removeHints.has_key(pagename):
                for pl2 in removeHints[pagename]:
                    site = pl2.site()
                    try:
                        del new[site]
                    except KeyError:
                        pass
            mods, removing = interwiki.compareLanguages(old, new)
            if mods:
                wikipedia.output(pl.aslink() + mods)
                oldtext = pl.get()
                newtext = wikipedia.replaceLanguageLinks(oldtext, new)
                if 1:
                    wikipedia.showColorDiff(oldtext, newtext)
                    status, reason, data = pl.put(newtext, comment='warnfile '+mods)
                    if str(status) != '302':
                        print status, reason

def main():
    filename = None
    for arg in sys.argv[1:]:
        arg = wikipedia.argHandler(arg, 'warnfile')
        if arg:
            filename = arg

    if not filename:
        mysite = wikipedia.getSite()
        filename = 'logs/warning-%s-%s.log' % (mysite.family.name, mysite.lang)
    reader = WarnfileReader(filename)
    bot = WarnfileRobot(reader)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()

