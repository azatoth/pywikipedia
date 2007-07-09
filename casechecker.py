#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Script to enumerate all pages on the wiki and find all titles
with mixed latin and cyrilic alphabets.
"""

#
# Permutations code was taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/190465
#
from __future__ import generators

def xuniqueCombinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in xuniqueCombinations(items[i+1:],n-1):
                yield [items[i]]+cc
# End of permutation code

#
# Windows Concose colors
# This code makes this script Windows ONLY!!!  Feel free to adapt it to another platform
#
#
FOREGROUND_BLUE = 1
FOREGROUND_GREEN = 2
FOREGROUND_RED = 4

FOREGROUND_WHITE = 1|2|4

def SetColor(color):
    try:
        import win32console
        stdout=win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
        stdout.SetConsoleTextAttribute(color)
    except:
        if color == FOREGROUND_BLUE: print '(b:'
        if color == FOREGROUND_GREEN: print '(g:'
        if color == FOREGROUND_RED: print '(r:'
                
# end of console code




import sys, query, wikipedia, re, codecs


class CaseChecker( object ):

    langs = {
        'ru': {
           'alphabet'  : u'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя',
           'localsuspects': u'АаВЕеКкМНОоРрСсТуХх',
           'latinsuspects': u'AaBEeKkMHOoPpCcTyXx',
           },
        'uk': {
           'alphabet'  : u'АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЮюЯяЬь',
           'localsuspects': u'АаВЕеІіКкМНОоРрСсТУуХх',
           'latinsuspects': u'AaBEeIiKkMHOoPpCcTYyXx',
           },
        'bg': {
           'alphabet'  : u'АаБбВвГгДдЕеЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЬьЮюЯя',
           'localsuspects': u'АаВЕеКкМНОоРрСсТуХх',
           'latinsuspects': u'AaBEeKkMHOoPpCcTyXx',
           },
        'be': {
           'alphabet'  : u'АаБбВвГгҐґДдЖжЗзЕеЁёЖжЗзІіЙйКкЛлМмНнОоПпРрСсТтУуЎўФфХхЦцЧчШшЫыЬьЭэЮюЯя',
           'localsuspects': u'АаВЕеІіКкМНОоРрСсТуХх',
           'latinsuspects': u'AaBEeIiKkMHOoPpCcTyXx',
           },
        }
        
    knownWords = set([u'Zемфира', u'KoЯn', u'Deadушки', u'ENTERМУЗЫКА', u'Юz', u'Lюк', u'Яndex', u'КариZма', u'Стогoff', u'UltraВожык', u'Hardcoreманія', u'БМАgroup', u'Tviй', u'Undergroўnd', u'recordц', u'Bэzu'])
    latLtr = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    lclClrFnt = u'<font color=green>'
    latClrFnt = u'<font color=brown>'
    suffixClr = u'</font>'
    
    wordBreaker = re.compile(u'[ _\-/\|#[\]()]')

    titles = True
    links = False
    aplimit = 500
    apfrom = u''
    title = None
    replace = False
    stopAfter = 0
    verbose = False
    wikilog = None
    autonomous = False
    namespaces = []
    
    def __init__(self):
        
        for arg in wikipedia.handleArgs():
            if arg.startswith('-from'):
                if arg.startswith('-from:'):
                    self.apfrom = arg[6:]
                else:
                    self.apfrom = wikipedia.input(u'Which page to start from: ')
            elif arg.startswith('-reqsize:'):
                self.aplimit = int(arg[9:])
            elif arg == '-links':
                self.links = True
            elif arg == '-linksonly':
                self.links = True
                self.titles = False
            elif arg == '-replace':
                self.replace = True
            elif arg.startswith('-limit:'):
                self.stopAfter = int(arg[7:])
            elif arg == '-verbose':
                self.verbose = True
            elif arg == '-autonomous':
                self.autonomous = True
            elif arg.startswith('-ns:'):
                self.namespaces.append( int(arg[4:]) )
            elif arg.startswith('-wikilog:'):
                try:
                    self.wikilog = codecs.open(arg[9:], 'a', 'utf-8')
                except IOError:
                    self.wikilog = codecs.open(arg[9:], 'w', 'utf-8')
            else:
                wikipedia.output(u'Unknown argument %s.' % arg)
                wikipedia.showHelp()
                sys.exit()

        if self.namespaces == []:
            if self.apfrom == u'':
                self.namespaces = [14, 10, 12, 0]    # 0 should be after templates ns
            else:
                self.namespaces = [0]

        self.params = {'what'         : 'allpages',
                      'aplimit'       : self.aplimit, 
                      'apfilterredir' : 'nonredirects',
                      'noprofile'     : '' }

        if self.links:
            self.params['what'] += '|links|categories';
            
        self.site = wikipedia.getSite()
        
        if self.site.lang in self.langs:
            l = self.langs[self.site.lang]
            self.localSuspects = l['localsuspects']
            self.latinSuspects = l['latinsuspects']
            self.localLtr = l['alphabet']
        else:
            raise u'Unsupported site ' + self.site.lang
    
        if len(self.localSuspects) != len(self.latinSuspects):
            raise u'Suspects must be the same size'

        self.lclToLatDict = dict([(ord(self.localSuspects[i]), self.latinSuspects[i]) for i in range(len(self.localSuspects))])
        self.latToLclDict = dict([(ord(self.latinSuspects[i]), self.localSuspects[i]) for i in range(len(self.localSuspects))])
    
        badPtrnStr = u'([%s][%s]|[%s][%s])' % (self.latLtr, self.localLtr, self.localLtr, self.latLtr)
        self.badPtrn = re.compile(badPtrnStr)
        self.badWordPtrn = re.compile(u'[%s%s]*%s[%s%s]*' % (self.latLtr, self.localLtr, badPtrnStr, self.latLtr, self.localLtr) )
            
        
    def Run(self):
        try:
            count = 0
            lastLetter = ''
            for namespace in self.namespaces:
                self.params['apnamespace'] = namespace
                title = None
                
                while True:                
                    # Get data
                    self.params['apfrom'] = self.apfrom
                    data = query.GetData(self.site.lang, self.params, self.verbose)
                    try:
                        self.apfrom = data['query']['allpages']['next']
                    except:
                        self.apfrom = None
    
                    # Process received data
                    if 'pages' in data:
                        firstItem = True
                        for pageID, page in data['pages'].iteritems():
                            printed = False
                            title = page['title']
                            if firstItem:
                                if lastLetter != title[0]:
                                    print 'Processing ' + title
                                    lastLetter = title[0]
                                firstItem = False
                            if self.titles:
                                err = self.ProcessTitle(title)
                                if err:
                                    if page['ns'] == 14:
                                        self.WikiLog(u"* Move category content: " + err[0])
                                    else:
                                        changed = False
                                        if self.replace:
                                            newTitle = self.PickTarget(False, title, err[1])
                                            if newTitle:
                                                src = wikipedia.Page(self.site, title)
                                                src.move( newTitle, u'mixed case rename')
                                                changed = True
                                        
                                        if not changed:
                                            self.WikiLog(u"* " + err[0])
                                            printed = True
                                                                    
                            if self.links:
                                allLinks = None
                                if 'links' in page:
                                    allLinks = page['links']
                                if 'categories' in page:
                                    if allLinks:
                                        allLinks = allLinks + page['categories']
                                    else:
                                        allLinks = page['categories']
                                
                                if allLinks:
                                    pageObj = None
                                    pageTxt = None
                                    msg = []
                                    
                                    for l in allLinks:
                                        ltxt = l['*']
                                        err = self.ProcessTitle(ltxt)
                                        if err:
                                            newTitle = None
                                            if self.replace:
                                                newTitle = self.PickTarget(True, ltxt, err[1])
                                                if newTitle:
                                                    if pageObj is None:
                                                        pageObj = wikipedia.Page(self.site, title)
                                                        pageTxt = pageObj.get()
                                                    msg.append(u'[[%s]] => [[%s]]' % (ltxt, newTitle))
#                                                    pageTxt = pageTxt.replace(ltxt, newTitle)
#                                                    pageTxt = pageTxt.replace(ltxt[0].lower() + ltxt[1:], newTitle[0].lower() + newTitle[1:])
#                                                    pageTxt = pageTxt.replace(ltxt.replace(u' ', '_'), newTitle)
                                                    
                                                    frmParts = self.wordBreaker.split(ltxt)
                                                    toParts = self.wordBreaker.split(newTitle)
                                                    if len(frmParts) != len(toParts):
                                                        raise u'Splitting parts do not match counts'
                                                    for i in range(0, len(frmParts)):
                                                        if len(frmParts[i]) != len(toParts[i]):
                                                            raise u'Splitting parts do not match word length'
                                                        if len(frmParts[i]) > 0:
                                                            pageTxt = pageTxt.replace(frmParts[i], toParts[i])
                                                            pageTxt = pageTxt.replace(frmParts[i][0].lower() + frmParts[i][1:], toParts[i][0].lower() + toParts[i][1:])
                                                        
                                            if not newTitle:
                                                if not printed:
                                                    self.WikiLog(u"* [[:%s]]: link to %s" % (title, err[0]))
                                                    printed = True
                                                else:
                                                    self.WikiLog(u"** link to %s" % err[0])
                                                
        
                                    if pageObj is not None:
                                        coloredMsg = u', '.join([self.ColorCodeWord(m) for m in msg])
                                        if pageObj.get() == pageTxt:
                                            self.WikiLog(u"* Error: Text replacement failed in [[:%s]] (%s)" % (title, coloredMsg))
                                        else:
                                            wikipedia.output(u'Case Replacements: %s' % u', '.join(msg))
                                            try:
                                                pageObj.put(pageTxt, u'Case Replacements: %s' % u', '.join(msg))
                                            except KeyboardInterrupt:
                                                raise
                                            except:
                                                self.WikiLog(u"* Error: Could not save updated page [[:%s]] (%s)" % (title, coloredMsg))
                                                
                        
                            count += 1
                            if self.stopAfter > 0 and count == self.stopAfter:
                                raise "Stopping because we are done"
                        
                    if self.apfrom is None:
                        break
                
                self.apfrom = u''    # Restart apfrom for other namespaces

            print "***************************** Done"
                
        except:
            if self.apfrom is not None:
                wikipedia.output(u'Exception at Title = %s, Next = %s' % (title, self.apfrom))
            wikipedia.stopme()
            raise

    def WikiLog(self, text):
        wikipedia.output(text)
        if self.wikilog:
            self.wikilog.write(text + u'\n')
            self.wikilog.flush()
        
    def ProcessTitle(self, title):
        
        found = False
        for m in self.badWordPtrn.finditer(title):
            
            badWord = title[m.span()[0] : m.span()[1]]
            if badWord in self.knownWords:
                continue

            if not found:
                # lazy-initialization of the local variables
                possibleWords = []
                tempWords = []
                count = 0
                duplWordCount = 0
                ambigBadWords = set()
                ambigBadWordsCount = 0
                mapLcl = {}
                mapLat = {}
                found = True
                                        
            # See if it would make sense to treat the whole word as either cyrilic or latin
            mightBeLat = mightBeLcl = True
            for l in badWord:
                if l in self.localLtr:
                    if mightBeLat and l not in self.localSuspects:
                        mightBeLat = False
                else:
                    if mightBeLcl and l not in self.latinSuspects:
                        mightBeLcl = False
                    if l not in self.latLtr: raise "Assert failed"
            
            if mightBeLcl:
                mapLcl[badWord] = badWord.translate(self.latToLclDict)
            if mightBeLat:
                mapLat[badWord] = badWord.translate(self.lclToLatDict)
            if mightBeLcl and mightBeLat:
                ambigBadWords.add(badWord)
                ambigBadWordsCount += 1    # Cannot do len(ambigBadWords) because they might be duplicates
            count += 1

        if not found:
            return None
        
        infoText = self.MakeLink(title)
        possibleAlternatives = []
        
        if len(mapLcl) + len(mapLat) - ambigBadWordsCount < count:
            # We cannot auto-translate - offer a list of suggested words
            suggestions = mapLcl.values() + mapLat.values()
            if len(suggestions) > 0:
                infoText += u", word suggestions: " + u', '.join([self.ColorCodeWord(t) for t in suggestions])
            else:
                infoText += u", no suggestions"
        else:
            
            # Replace all unambiguous bad words
            for k,v in mapLat.items() + mapLcl.items():
                if k not in ambigBadWords:
                    title = title.replace(k,v)

            if len(ambigBadWords) == 0:
                # There are no ambiguity, we can safelly convert
                possibleAlternatives.append(title)
                infoText += u", convert to " + self.MakeLink(title)
            else:
                # Try to pick 0, 1, 2, ..., len(ambiguous words) unique combinations
                # from the bad words list, and convert just the picked words to cyrilic,
                # whereas making all other words as latin character.
                for itemCntToPick in range(0, len(ambigBadWords)+1):
                    title2 = title
                    for uc in xuniqueCombinations(list(ambigBadWords), itemCntToPick):
                        wordsToLat = ambigBadWords.copy()
                        for bw in uc:
                            title2 = title2.replace(bw, mapLcl[bw])
                            wordsToLat.remove(bw)
                        for bw in wordsToLat:
                            title2 = title2.replace(bw, mapLat[bw])
                        possibleAlternatives.append(title2)

                if len(possibleAlternatives) > 0:
                    infoText += u", can be converted to " + u', '.join([self.MakeLink(t) for t in possibleAlternatives])
                else:
                    infoText += u", no suggestions"

        return (infoText, possibleAlternatives)
    
    def PickTarget(self, isLink, original, candidates):
        if len(candidates) == 0:
            return None
        
        if isLink:
            if len(candidates) == 1:
                return candidates[0]
            
            pagesDontExist = []
            pagesRedir = {}
            pagesExist = []
            
            for newTitle in candidates:
                dst = wikipedia.Page(self.site, newTitle)
                if not dst.exists():
                    pagesDontExist.append(newTitle)
                elif dst.isRedirectPage():
                    pagesRedir[newTitle] = dst.getRedirectTarget()
                else:
                    pagesExist.append(newTitle)
            
            if len(pagesExist) == 1:
                return pagesExist[0]
            elif len(pagesExist) == 0 and len(pagesRedir) > 0:
                if len(pagesRedir) == 1:
                    return pagesRedir.keys()[0]
                t = None
                for k,v in pagesRedir.iteritems():
                    if not t:
                        t = v # first item
                    elif t != v:
                        break
                else:
                    # all redirects point to the same target
                    # pick the first one, doesn't matter what it is
                    return pagesRedir.keys()[0]
                
            if not self.autonomous:
                wikipedia.output(u'Could not auto-decide. Which should be chosen?')
                wikipedia.output(u'Original title: ', newline=False)
                self.ColorCodeWord(original + "\n", True)
                count = 1
                for t in candidates:
                    if t in pagesDontExist: msg = u'missing'
                    elif t in pagesRedir: msg = u'Redirect to ' + pagesRedir[t]
                    else: msg = u'page exists'
                    self.ColorCodeWord(u'  %d: %s (%s)\n' % (count, t, msg), True)
                    count += 1
                
                answers = [str(i) for i in range(0, count)]
                choice = int(wikipedia.inputChoice(u'Which link to choose? (0 to skip)', answers, [a[0] for a in answers]))
                if choice > 0:
                    return candidates[choice-1]

        else:
            if len(candidates) == 1:
                newTitle = candidates[0]
                dst = wikipedia.Page(self.site, newTitle)
                if not dst.exists():
                    # choice = wikipedia.inputChoice(u'Move %s to %s?' % (title, newTitle), ['Yes', 'No'], ['y', 'n'])
                    return newTitle
        
        return None

    def ColorCodeWord(self, word, toScreen = False):
        
        if not toScreen: res = u"<b>"
        lastIsCyr = word[0] in self.localLtr
        if lastIsCyr:
            if toScreen: SetColor(FOREGROUND_GREEN)
            else: res += self.lclClrFnt
        else:
            if toScreen: SetColor(FOREGROUND_RED)
            else: res += self.latClrFnt

        for l in word:
            if l in self.localLtr:
                if not lastIsCyr:
                    if toScreen: SetColor(FOREGROUND_GREEN)
                    else: res += self.suffixClr + self.lclClrFnt
                    lastIsCyr = True
            elif l in self.latLtr:
                if lastIsCyr:
                    if toScreen: SetColor(FOREGROUND_RED)
                    else: res += self.suffixClr + self.latClrFnt
                    lastIsCyr = False
            if toScreen: wikipedia.output(l, newline=False)
            else: res += l
        
        if toScreen: SetColor(FOREGROUND_WHITE)
        else: return res + self.suffixClr + u"</b>"
        

    def MakeLink(self, title):
        return u"[[:%s|««« %s »»»]]" % (title, self.ColorCodeWord(title))
        
if __name__ == "__main__":
    try:
        bot = CaseChecker()
        bot.Run()
    finally:
        wikipedia.stopme()