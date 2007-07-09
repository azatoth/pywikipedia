#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to check language links for general pages. This works by downloading the
page, and using existing translations plus hints from the command line to
download the equivalent pages from other languages. All of such pages are
downloaded as well and checked for interwiki links recursively until there are
no more links that are encountered. A rationalization process then selects the
right interwiki links, and if this is unambiguous, the interwiki links in the
original page will be automatically updated and the modified page uploaded.

This script understands various command-line arguments:
    -force:        do not ask permission to make "controversial" changes,
                   like removing a language because none of the found
                   alternatives actually exists.

    -hint:         used as -hint:de:Anweisung to give the robot a hint
                   where to start looking for translations. This is only
                   useful if you specify a single page to work on. If no
                   text is given after the second ':', the name of the page
                   itself is used as the title for the hint.

    There are some special hints, trying a number of languages at once:
    all:    Provides the hint for all languages with at least ca. 100 pages
    10:     Provides the hint for ca. 10 of the largest languages
    20:, 30:, 50: Analogous to 10: with ca. 20, 30 and 50 languages 
    cyril:  Provides the hint for all languages that use the cyrillic alphabet

    -cat           Work on all pages which are in a specific category.
                   Argument can also be given as "-cat:categoryname".

    -subcat        Like -cat, but also includes pages in subcategories of the
                   given category.
                   Argument can also be given as "-subcat:categoryname".

    -ref           Work on all pages that link to a certain page.
                   Argument can also be given as "-ref:referredpagetitle".

    -links         Work on all pages that are linked from a certain page.
                   Argument can also be given as "-links:linkingpagetitle".

    -new           Work on the most recent new pages on the wiki

    -same:         looks over all 'serious' languages for the same title.
                   -same is equivalent to -hint:all:

    -wiktionary:   similar to -same, but will ONLY accept names that are
                   identical to the original. Also, if the title is not
                   capitalized, it will only go through other wikis without
                   automatic capitalization.

    -askhints:     for each page one or more hints are asked. See hint: above
                   for the format, one can for example give "en:something" or
                   "20:" as hint.

    -untranslated: works normally on pages with at least one interlanguage
                   link; asks hints for pages that have none.

    -untranslatedonly: same as -untranslated, but pages which already have a
                   translation are skipped. Hint: do NOT use this in
                   combination with -start without a -number limit, because
                   you will go through the whole alphabet before any queries
                   are performed!

    -file:         used as -file:filename, read a list of pages to treat
                   from the named file

    -confirm:      ask for confirmation before any page is changed on the
                   live wiki. Without this argument, additions and
                   unambiguous modifications are made without confirmation.

    -select:       ask for each link whether it should be include before
                   changing any page. This is useful if you want to remove
                   invalid interwiki and if you do multiple hints of which
                   some might be correct and others incorrect. Combining
                   -select and -confirm is possible, but seems like overkill.

    -autonomous:   run automatically, do not ask any questions. If a question
                   to an operator is needed, write the name of the page
                   to autonomous_problems.dat and continue on the next page.

    -nobacklink:   switch off the backlink warnings

    -start:        used as -start:title, specifies that the robot should
                   go alphabetically through all pages on the home wiki,
                   starting at the named page. If -start:title and -cat:category
                   are both added, go through category category, but start
                   alphabetically at pagename title instead of the beginning.

    -number:       used as -number:#, specifies that the robot should process
                   that amount of pages and then stop. This is only useful in
                   combination with -start. The default is not to stop.

    -array:        used as -array:#, specifies that the robot should process
                   that amount of pages at once, only starting to load new
                   pages in the original language when the total falls below
                   that number. Default is to process (at least) 100 pages at
                   once. The number of new ones loaded is equal to the number
                   that is loaded at once from another language (default 60)

    -years:        run on all year pages in numerical order. Stop at year 2050.
                   If the argument is given in the form -years:XYZ, it
                   will run from [[XYZ]] through [[2050]]. If XYZ is a
                   negative value, it is interpreted as a year BC. If the
                   argument is simply given as -years, it will run from 1
                   through 2050.
                   
                   This implies -noredirect.

    -noauto:       Do not use the automatic translation feature for years and
                   dates, only use found links and hints.

    -days:         Like -years, but runs through all date pages. Stops at
                   Dec 31.  If the argument is given in the form -days:X,
                   it will start at month no. X through Dec 31. If the
                   argument is simply given as -days, it will run from
                   Jan 1 through Dec 31.  E.g. for -days:9 it will run
                   from Sep 1 through Dec 31.
    
    -skipfile:     used as -skipfile:filename, skip all links mentioned in
                   the given file from the list generated by -start. This
                   does not work with -number!
                   
    -skipauto:     use to skip all pages that can be translated automatically,
                   like dates, centuries, months, etc.

    -restore:      restore a set of "dumped" pages the robot was working on
                   when it terminated.

    -continue:     as restore, but after having gone through the dumped pages,
                   continue alphabetically starting at the last of the dumped
                   pages.

    -warnfile:     used as -warnfile:filename, reads all warnings from the
                   given file that apply to the home wiki language,
                   and read the rest of the warning as a hint. Then
                   treats all the mentioned pages. A quicker way to
                   implement warnfile suggestions without verifying them
                   against the live wiki is using the warnfile.py
                   robot.

    -noredirect    do not follow redirects (note: without ending columns).

    -noshownew:    don't show the source of every new pagelink found.

    -neverlink:    used as -neverlink:xx where xx is a language code:
                   Disregard any links found to language xx. You can also
                   specify a list of languages to disregard, separated by
                   commas.

    -ignore:       used as -ignore:xx:aaa where xx is a language code, and
                   aaa is a page title to be ignored.

    -ignorefile:   similar to -ignore, except that the pages are taken from
                   the given file instead of the command line.
    
    -showpage      when asking for hints, show the first bit of the text
                   of the page always, rather than doing so only when being
                   asked for (by typing '?'). Only useful in combination
                   with a hint-asking option like -untranslated, -askhints
                   or -untranslatedonly

    -localonly     only work on the local wiki, not on other wikis in the family
                   I have a login at
                   
    -limittwo      only update two pages - one in the local wiki (if loged-in),
                   and one in the top available one.
                   For example, if the local page has links to de and fr,
                   this option will make sure that only local and de: (larger)
                   site is updated. This option is useful to quickly set two way
                   links without updating all of wiki's sites.

    -whenneeded    works like limittwo, but other languages are changed in the
                   following cases:
                   * If there are no interwiki at all on the page
                   * If an interwiki must be removed
                   * If an interwiki must be changed and there has been a
                     conflict for this page
                   Optionally, -whenneeded can be given an additional number
                   (for example -whenneeded:3), in which case other languages
                   will be changed if there are that number or more links to
                   change or add
                   
    -bracket       only work on pages that have (in the home language) a bracket
                   in their title. All other pages are skipped.

    -withoutinterwiki work on [[Special:Withoutinterwiki]] articles.

Some configuration option can be used to change the working of this robot:

interwiki_backlink: if set to True, all problems in foreign wikis will
                    be reported

interwiki_shownew:  should interwiki.py display every new link it discovers?

interwiki_graph:    output a graph PNG file on conflicts? You need pydot for
                    this: http://dkbza.org/pydot.html

interwiki_graph_format: the file format for interwiki graphs 

without_interwiki:  save file with local articles without interwikis

All these options can be changed through the user-config.py configuration file.

If interwiki.py is terminated before it is finished, it will write a dump file
to the interwiki-dumps subdirectory. The program will read it if invoked with
the "-restore" or "-continue" option, and finish all the subjects in that list.
To run the interwiki-bot on all pages on a language, run it with option
"-start:!", and if it takes so long you have to break it off, use "-continue"
next time.
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
# (C) Yuri Astrakhan, 2005-2006
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#
import sys, copy, re
import time
import codecs
import socket

try:
    set # introduced in Python 2.4: faster and future
except NameError:
    from sets import Set as set

try: sorted ## Introduced in 2.4
except NameError:
    def sorted(seq, cmp=None, key=None, reverse=False):
        """Copy seq and sort and return it.
        >>> sorted([3, 1, 2])
        [1, 2, 3]
        """
        seq2 = copy.copy(seq)
        if key:
            if cmp == None:
                cmp = __builtins__.cmp
            seq2.sort(lambda x,y: cmp(key(x), key(y)))
        else:
            if cmp == None:
                seq2.sort()
            else:
                seq2.sort(cmp)
        if reverse:
            seq2.reverse()
        return seq2

import wikipedia, config, pagegenerators, catlib
import titletranslate, interwiki_graph

class SaveError(wikipedia.Error):
    """
    An attempt to save a page with changed interwiki has failed.
    """

class LinkMustBeRemoved(SaveError):
    """
    An interwiki link has to be removed, but this can't be done because of user
    preferences or because the user chose not to change the page.
    """

class GiveUpOnPage(wikipedia.Error):
    """
    The user chose not to work on this page and its linked pages any more.
    """
msg = {
    'af': (u'robot ', u'Bygevoeg', u'Verwyder', u'Verander'),
    'ar': (u'روبوت ', u'إضافة', u'إزالة', u'تعديل'),
    'bat-smg': (u'robots ', u'Pridedama', u'Trėnama', u'Keitama'),
    'be': (u'робат ', u'Дадаем', u'Выдаляем', u'Мяняем'),
    'be-x-old': (u'робат ', u'дадаў', u'выдаліў', u'зьмяніў'),
    'bg': (u'Робот ', u'Добавяне', u'Изтриване', u'Промяна'),
    'br': (u'Robot ', u'ouzhpennet', u'tennet', u'kemmet'),
    'ca': (u'Robot ', u'afegeix', u'esborra', u'modifica'),
    'cs': (u'robot ', u'přidal', u'odebral', u'změnil'),
    'csb':(u'robot ', u'dodôwô', u'rëmô', u'pòprôwiô'),
    'da': (u'robot ', u'Tilføjer', u'Fjerner', u'Ændrer'),
    'de': (u'Bot: ', u'Ergänze', u'Entferne', u'Ändere'),
    'el': (u'Ρομπότ:', u'Προσθήκη', u'Αφαίρεση', u'Τροποποίηση'),
    'en': (u'robot ', u'Adding', u'Removing', u'Modifying'),
    'eo': (u'roboto ', u'aldono de', u'forigo de', u'modifo de'),
    'es': (u'robot ', u'Añadido', u'Eliminado', u'Modificado'),
    'eu': (u'robota ', u'Erantsia', u'Ezabatua', u'Aldatua'),
    'fa': (u'ربات ', u'افزودن', u'حذف', u'اصلاح'),
    'fi': (u'Botti ', u'lisäsi', u'poisti', u'muokkasi'),
    'fr': (u'robot ', u'Ajoute', u'Retire', u'Modifie'),
    'fur': (u'Robot: ', u'o zonti', u'o cambii', u'o gjavi'),
    'he': (u'רובוט ', u'מוסיף', u'מסיר', u'משנה'),
    'hr': (u'robot', u'Dodaje', u'Uklanja', u'Mijenja'),
    'hu': (u'Robot: ', u'következő hozzáadása', u'következő eltávolítása', u'következő módosítása'),
    'ia': (u'Robot: ', u'Addition de', u'Elimination de', u'Modification de'),
    'id': (u'bot ', u'Menambah', u'Membuang', u'Mengubah'),
    'io': (u'roboto ', u'adjuntas', u'efacas', u'modifikas'),
    'is': (u'robot ', u'Bæti við', u'Fjarlægi', u'Breyti'),
    'it': (u'robot ', u'Aggiungo', u'Tolgo', u'Modifico'),
    'ka': (u'რობოტი ', u'დამატება', u'წაშლა', u'შეცვლა'),
    'ksh': (u'Bot: ', u'dobëijedonn', u'erußjenumme', u'ußjewääßelt'),
    'lmo': (u'Robot ', u'jontant', u'trant via', u'modifiant'),
    'lt': (u'robotas ', u'Pridedama', u'Šalinama', u'Keičiama'),
    'lv': (u'robots ', u'pievieno', u'izņem', u'izmaina'),
    'mzn': (u'Rebot ', u'Biyeshten', u'Bayten', u'Hekărden'),
    'nds': (u'IW-Bot: ', u'dorto', u'rut', u'ännert'),
    'nds-nl': (u'bot', u'derbie', u'derof', u'aanders'),
    'nl': (u'robot ', u'Erbij', u'Eraf', u'Anders'),
    'nn': (u'robot ', u'la til', u'fjerna', u'endra'),
    'no': (u'robot ', u'Tilføyer', u'Fjerner', u'Endrer'),
    'os': (u'Робот', u'баххæст кодта', u'Баивта', u'Аиуварс'),
    'pl': (u'robot ', u'dodaje', u'usuwa', u'poprawia'),
    'pms': (u'ël trigomiro ', u'a gionta', u'a modìfica', u'a gava'),
    'pt': (u'Bot: ', u'Adicionando', u'Removendo',u'Modificando'),
    'qu': (u'Rurana antacha ', u'Yapasqa', u'Qullusqa', u'Hukchasqa'),
    'ro': (u'Robot interwiki: ', u'Adãugat', u'Înlãturat',u'Modificat'),
    'ru': (u'робот ', u'добавил', u'удалил', u'изменил'),
    'sk': (u'robot ', u'Pridal', u'Odobral',u'Zmenil' ),
    'sl': (u'robot ', u'Dodajanje', u'Odstranjevanje', u'Spreminjanje'),
    'sr': (u'Бот', u'Додаје', u'Брише', u'Мења'),
    'su': (u'bot ', u'Nambih', u'Miceun', u'Ngarobih'),
    'sv': (u'robot ', u'Lägger till', u'Tar bort', u'Ändrar'),
    'tet': (u'bot ', u'tau tan', u'hasai', u'filak'),
    'tg': (u'робот ', u'илова карда истодааст', u'дигаргуни карда истодааст', u'ҳaвз карда истодааст'),
    'uk': (u'робот', u'додав', u'видалив', u'змінив'),
    'vi': (u'robot ', u'Thêm', u'Dời', u'Thay'),
    'vo': (u'bot ', u'läükon', u'moükon', u'votükon'),
    }

class Global(object):
    """Container class for global settings.
       Use of globals outside of this is to be avoided."""
    autonomous = False
    backlink = config.interwiki_backlink
    confirm = False
    select = False
    debug = True
    followredirect = True
    force = False
    minarraysize = 100
    maxquerysize = 60
    same = False
    shownew = config.interwiki_shownew
    skip = set()
    skipauto = False
    untranslated = False
    untranslatedonly = False
    askhints = False
    auto = True
    neverlink = []
    showtextlink = 0
    showtextlinkadd = 300
    localonly = False
    limittwo = False
    strictlimittwo = False
    needlimit = 0
    ignore = []
    bracketonly = False
    rememberno = False

class Subject(object):
    """
    Class to follow the progress of a single 'subject' (i.e. a page with
    all its translations)
    """

    def __init__(self, originPage, hints = None):
        """Constructor. Takes as arguments the Page on the home wiki
           plus optionally a list of hints for translation"""
        # Remember the "origin page"
        self.originPage = originPage
        # todo is a list of all pages that still need to be analyzed.
        # Mark the origin page as todo.
        self.todo = [originPage]
        # done is a list of all pages that have been analyzed and that
        # are known to belong to this subject.
        self.done = []
        # foundIn is a dictionary where pages are keys and lists of
        # pages are values. It stores where we found each page.
        # As we haven't yet found a page that links to the origin page, we
        # start with an empty list for it.
        self.foundIn = {self.originPage:[]}
        # This is a list of all pages that are currently scheduled for
        # download.
        self.pending = []
        self.translate(hints)
        self.confirm = globalvar.confirm
        self.problemfound = False
        self.untranslated = None
        self.hintsAsked = False

    def getFoundDisambig(self, site):
        """
        If we found a disambiguation on the given site while working on the
        subject, this method returns it. If several ones have been found, the
        first one will be returned.
        Otherwise, None will be returned.
        """
        for page in self.done + self.pending:
            if page.site() == site:
                if page.exists() and page.isDisambig():
                    return page
        return None

    def getFoundNonDisambig(self, site):
        """
        If we found a non-disambiguation on the given site while working on the
        subject, this method returns it. If several ones have been found, the
        first one will be returned.
        Otherwise, None will be returned.
        """
        for page in self.done + self.pending:
            if page.site() == site:
                if page.exists() and not page.isDisambig() and not page.isRedirectPage():
                    return page
        return None

    def getFoundInCorrectNamespace(self, site):
        """
        If we found a page that has the expected namespace on the given site
        while working on the subject, this method returns it. If several ones
        have been found, the first one will be returned.
        Otherwise, None will be returned.
        """
        # Hmmm... working on the todo list is quite risky,
        # because we don't know yet if the pages there
        # really exist...
        for page in self.done + self.pending + self.todo:
            if page.site() == site:
                if page.namespace() == self.originPage.namespace():
                    return page
        return None

    def translate(self, hints = None):
        """Add the given translation hints to the todo list"""
        if globalvar.same:
            if hints:
                pages = titletranslate.translate(self.originPage, hints = hints + ['all:'], auto = globalvar.auto)
            else:
                pages = titletranslate.translate(self.originPage, hints = ['all:'], auto = globalvar.auto)
        else:
            pages = titletranslate.translate(self.originPage, hints = hints, auto = globalvar.auto)
        for page in pages:
            self.todo.append(page)
            self.foundIn[page] = [None]

    def openSites(self):
        """Return a list of sites for all things we still need to do"""
        return [page.site() for page in self.todo] # TODO: remove duplicates

    def willWorkOn(self, site):
        """
        By calling this method, you 'promise' this instance that you will
        work on any todo items for the wiki indicated by 'site'. This routine
        will return a list of pages that can be treated.
        """
        # Bug-check: Isn't there any work still in progress? We can't work on
        # different sites at a time!
        if self.pending != []:
            raise 'BUG: Can\'t start to work on %s; still working on %s' % (repr(site), self.pending)
        # Prepare a list of suitable pages
        for page in self.todo:
            if page.site() == site:
                self.pending.append(page)
        for page in self.pending:
            self.todo.remove(page)
        # If there are any, return them. Otherwise, nothing is in progress.
        return self.pending

    def addIfNew(self, page, counter, linkingPage):
        """
        Adds the pagelink given to the todo list, but only if we didn't know
        it before. If it is added, update the counter accordingly.

        Also remembers where we found the page, regardless of whether it had
        already been found before or not.

        Returns True iff the page is new.
        """
        if self.foundIn.has_key(page):
            # not new
            self.foundIn[page].append(linkingPage)
            return False
        else:
            self.foundIn[page] = [linkingPage]
            self.todo.append(page)
            counter.plus(page.site())
            return True

    def namespaceMismatch(self, linkingPage, linkedPage):
        """
        Checks whether or not the given page has another namespace
        as the origin page.

        Returns True iff the namespaces are different and the user
        has selected not to follow the linked page.
        """
        if self.foundIn.has_key(linkedPage):
            # We have seen this page before, don't ask again.
            return False
        elif self.originPage.namespace() != linkedPage.namespace():
            if globalvar.autonomous:
                wikipedia.output(u"NOTE: Ignoring link from page %s in namespace %i to page %s in namespace %i." % (self.originPage.aslink(True), self.originPage.namespace(), linkedPage.aslink(True), linkedPage.namespace()))
                # Fill up foundIn, so that we will not write this notice
                self.foundIn[linkedPage] = [linkingPage]
                return True
            else:
                preferredPage = self.getFoundInCorrectNamespace(linkedPage.site())
                if preferredPage:
                    wikipedia.output(u"NOTE: Ignoring link from page %s in namespace %i to page %s in namespace %i because page %s in the correct namespace has already been found." % (self.originPage.aslink(True), self.originPage.namespace(), linkedPage.aslink(True), linkedPage.namespace(), preferredPage.aslink(True)))
                    return True
                else:
                    choice = wikipedia.inputChoice('WARNING: %s is in namespace %i, but %s is in namespace %i. Follow it anyway?' % (self.originPage.aslink(True), self.originPage.namespace(), linkedPage.aslink(True), linkedPage.namespace()), ['Yes', 'No'], ['y', 'n'])
                    if choice != 'y':
                        # Fill up foundIn, so that we will not ask again
                        self.foundIn[linkedPage] = [linkingPage]
                        wikipedia.output(u"NOTE: ignoring %s and its interwiki links" % linkedPage.aslink(True))
                        return True
        else:
            # same namespaces, no problem
            return False

    def wiktionaryMismatch(self, page):
        if globalvar.same=='wiktionary':
            if page.title().lower() != self.originPage.title().lower():
                wikipedia.output(u"NOTE: Ignoring %s for %s in wiktionary mode" % (page.aslink(), self.originPage.aslink()))
                return True
            elif page.title() != self.originPage.title() and self.originPage.site().nocapitalize and page.site().nocapitalize:
                wikipedia.output(u"NOTE: Ignoring %s for %s in wiktionary mode because both languages are uncapitalized." % (page.aslink(), self.originPage.aslink()))
                return True
        return False

    def disambigMismatch(self, page):
        """
        Checks whether or not the given page has the another disambiguation
        status than the origin page.

        Returns a tuple (skip, alternativePage).

        skip is True iff the pages have mismatching statuses and the bot
        is either in autonomous mode, or the user chose not to use the
        given page.

        alternativePage is either None, or a page that the user has
        chosen to use instead of the given page.
        """
        if globalvar.autonomous:
            if self.originPage.isDisambig() and not page.isDisambig():
                wikipedia.output(u"NOTE: Ignoring link from disambiguation page %s to non-disambiguation %s" % (self.originPage.aslink(True), page.aslink(True)))
                return (True, None)
            elif not self.originPage.isDisambig() and page.isDisambig():
                wikipedia.output(u"NOTE: Ignoring link from non-disambiguation page %s to disambiguation %s" % (self.originPage.aslink(True), page.aslink(True)))
                return (True, None)
        else:
            choice = 'y'
            if self.originPage.isDisambig() and not page.isDisambig():
                if self.getFoundDisambig(page.site()):
                    wikipedia.output(u"NOTE: Ignoring non-disambiguation page %s for %s because disambiguation page %s has already been found." % (page.aslink(True), self.originPage.aslink(True), self.getFoundDisambig(page.site()).aslink(True)))
                    return (True, None)
                else:
                    choice = wikipedia.inputChoice('WARNING: %s is a disambiguation page, but %s doesn\'t seem to be one. Follow it anyway?' % (self.originPage.aslink(True), page.aslink(True)), ['Yes', 'No', 'Add an alternative'], ['y', 'n', 'a'])
            elif not self.originPage.isDisambig() and page.isDisambig():
                if self.getFoundNonDisambig(page.site()):
                    wikipedia.output(u"NOTE: Ignoring disambiguation page %s for %s because non-disambiguation page %s has already been found." % (page.aslink(True), self.originPage.aslink(True), self.getFoundNonDisambig(page.site()).aslink(True)))
                    return (True, None)
                else:
                    choice = wikipedia.inputChoice('WARNING: %s doesn\'t seem to be a disambiguation page, but %s is one. Follow it anyway?' % (self.originPage.aslink(True), page.aslink(True)), ['Yes', 'No', 'Add an alternative'], ['y', 'n', 'a'])
            if choice == 'n':
                return (True, None)
            elif choice == 'a':
                newHint = wikipedia.input(u'Give the alternative for language %s, not using a language code:' % page.site().language())
                alternativePage = wikipedia.Page(page.site(), newHint)
                return (True, alternativePage)
        # We can follow the page.
        return (False, None)

    def isIgnored(self, page):
        if page.site().language() in globalvar.neverlink:
            wikipedia.output(u"Skipping link %s to an ignored language" % page.aslink())
            return True
        if page in globalvar.ignore:
            wikipedia.output(u"Skipping link %s to an ignored page" % page.aslink())
            return True
        return False

    def reportInterwikilessPage(self, page):
        wikipedia.output(u"NOTE: %s does not have any interwiki links" % self.originPage.aslink(True))
        if config.without_interwiki:
            f = codecs.open('without_interwiki.txt', 'a', 'utf-8')
            f.write("# %s \n" % page.aslink())
            f.close()

    def askForHints(self, counter):
        if (self.untranslated or globalvar.askhints) and not self.hintsAsked and not self.originPage.isRedirectPage():
            # Only once!
            self.hintsAsked = True
            if globalvar.untranslated:
                newhint = None
                t = globalvar.showtextlink
                if t:
                    wikipedia.output(self.originPage.get()[:t])
                # loop 
                while True:
                    newhint = wikipedia.input(u'Give a hint (? to see pagetext):')
                    if newhint == '?':
                        t += globalvar.showtextlinkadd
                        wikipedia.output(self.originPage.get()[:t])
                    elif newhint and not ':' in newhint:
                        wikipedia.output(u'Please enter a hint in the format language:pagename or type nothing if you do not have a hint.')
                    elif not newhint:
                        break
                    else:
                        pages = titletranslate.translate(self.originPage, hints = [newhint], auto = globalvar.auto)
                        for page in pages:
                            self.addIfNew(page, counter, None)

    def workDone(self, counter):
        """
        This is called by a worker to tell us that the promised work
        was completed as far as possible. The only argument is an instance
        of a counter class, that has methods minus() and plus() to keep
        counts of the total work todo.
        """
        # Loop over all the pages that should have been taken care of
        for page in self.pending:
            # Mark the page as done
            self.done.append(page)

            # make sure that none of the linked items is an auto item
            if globalvar.skipauto:
                dictName, year = page.autoFormat()
                if dictName != None:
                    wikipedia.output(u'WARNING: %s:%s relates to %s:%s, which is an auto entry %s(%s)' % (self.originPage.site().language(), self.originPage.title(), page.site().language(),page.title(),dictName,year))                

            # Register this fact at the todo-counter.
            counter.minus(page.site())
            # Assume it's not a redirect
            isRedirect = False
            # Now check whether any interwiki links should be added to the
            # todo list.
            if page.section() and not page.isRedirectPage():
                # We have been referred to a part of a page, not the whole page. Do not follow references.
                pass
            else:
                try:
                    iw = page.interwiki()
                except wikipedia.IsRedirectPage, arg:
                    redirectTargetPage = wikipedia.Page(page.site(), arg.args[0])
                    wikipedia.output(u"NOTE: %s is redirect to %s" % (page.aslink(True), redirectTargetPage.aslink(True)))
                    if page == self.originPage:
                        # This is a redirect page to the origin. We don't need to
                        # follow the redirection.
                        # In this case we can also stop all hints!
                        for page2 in self.todo:
                            counter.minus(page2.site())
                        self.todo = []
                        pass
                    elif not globalvar.followredirect:
                        wikipedia.output(u"NOTE: not following redirects.")
                    else:
                        if not (self.isIgnored(redirectTargetPage) or self.namespaceMismatch(page, redirectTargetPage) or self.wiktionaryMismatch(redirectTargetPage) or (page.site().family != redirectTargetPage.site().family)):
                            if self.addIfNew(redirectTargetPage, counter, page):
                                if globalvar.shownew:
                                    wikipedia.output(u"%s: %s gives new redirect %s" %  (self.originPage.aslink(), page.aslink(True), redirectTargetPage.aslink(True)))
                except wikipedia.NoPage:
                    wikipedia.output(u"NOTE: %s does not exist" % page.aslink(True))
                    if page == self.originPage:
                        # The page we are working on is the page that does not exist.
                        # No use in doing any work on it in that case.
                        for page2 in self.todo:
                            counter.minus(page2.site())
                        self.todo = []
                        self.done = [] # In some rare cases it might be we already did check some 'automatic' links
                        pass
                #except wikipedia.SectionError:
                #    wikipedia.output(u"NOTE: section %s does not exist" % page.aslink())
                else:
                    (skip, alternativePage) = self.disambigMismatch(page)
                    if skip:
                        wikipedia.output(u"NOTE: ignoring %s and its interwiki links" % page.aslink(True))
                        if page in self.done: #XXX: Ugly bugfix - the following line has reportedly thrown "ValueError: list.remove(x): x not in list"
                            self.done.remove(page)
                        iw = ()
                        if alternativePage:
                            # add the page that was entered by the user
                            self.addIfNew(alternativePage, counter, None)

                    if self.originPage == page:
                        self.untranslated = (len(iw) == 0)
                        if globalvar.untranslatedonly:
                            # Ignore the interwiki links.
                            iw = ()
                    elif page.isEmpty() and not page.isCategory():
                        wikipedia.output(u"NOTE: %s is empty; ignoring it and its interwiki links" % page.aslink(True))
                        # Ignore the interwiki links
                        if page in self.done: #XXX: Ugly bugfix - the following line has reportedly thrown "ValueError: list.remove(x): x not in list"
                            self.done.remove(page)
                        iw = ()
                    # Temporary change because of be/be-x-old issue
                    for linkedPage in iw:
                        if linkedPage.site() == wikipedia.getSite('be','wikipedia'):
                            iw.append(wikipedia.Page(wikipedia.getSite('be-x-old','wikipedia'),linkedPage.title()))
                    for linkedPage in iw:
                        if not (self.isIgnored(linkedPage) or self.namespaceMismatch(page, linkedPage) or self.wiktionaryMismatch(linkedPage)):
                            if self.addIfNew(linkedPage, counter, page):
                                # It is new. Also verify whether it is the second on the
                                # same site
                                lpsite=linkedPage.site()
                                for prevPage in self.foundIn.keys():
                                    if prevPage != linkedPage and prevPage.site() == lpsite:
                                        # Still, this could be "no problem" as either may be a
                                        # redirect to the other. No way to find out quickly!
                                        wikipedia.output(u"NOTE: %s: %s gives duplicate interwiki on same site %s" % (self.originPage.aslink(), page.aslink(True), linkedPage.aslink(True)))
                                        break
                                else:
                                    if globalvar.shownew:
                                        wikipedia.output(u"%s: %s gives new interwiki %s"% (self.originPage.aslink(), page.aslink(True), linkedPage.aslink(True)))

        # These pages are no longer 'in progress'
        self.pending = []
        # Check whether we need hints and the user offered to give them
        if self.untranslated and not self.hintsAsked:
            self.reportInterwikilessPage(page)
        self.askForHints(counter)

    def isDone(self):
        """Return True if all the work for this subject has completed."""
        return len(self.todo) == 0

    def problem(self, txt, createneed = True):
        """Report a problem with the resolution of this subject."""
        wikipedia.output(u"ERROR: %s" % txt)
        self.confirm = True
        if createneed:
            self.problemfound = True
        if globalvar.autonomous:
            try:
                f = codecs.open('autonomous_problem.dat', 'a', 'utf-8')
                f.write("* %s {%s}" % (self.originPage.aslink(True), txt))
                if config.interwiki_graph and config.interwiki_graph_url:
                    filename = interwiki_graph.getFilename(self.originPage, extension = config.interwiki_graph_formats[0])
                    f.write(" [%s%s graph]" % (config.interwiki_graph_url, filename))
                f.write("\n")
                f.close()
            except:
               #raise
               wikipedia.output(u'File autonomous_problem.dat open or corrupted! Try again with -restore.')
               sys.exit()

    def whereReport(self, page, indent=4):
        for page2 in sorted(self.foundIn[page]):
            if page2 is None:
                wikipedia.output(u" "*indent + "Given as a hint.")
            else:
                wikipedia.output(u" "*indent + page2.aslink(True))


    def assemble(self):
        # No errors have been seen so far, except....
        errorCount = self.problemfound
        mysite = wikipedia.getSite()
        # Build up a dictionary of all pages found, with the site as key.
        # Each value will be a list of pages.
        new = {}
        for page in self.done:
            site = page.site()
            if site == self.originPage.site() and page.exists() and not page.isRedirectPage():
                if page != self.originPage:
                    self.problem("Found link to %s" % page.aslink(True) )
                    self.whereReport(page)
                    errorCount += 1
            elif page.exists() and not page.isRedirectPage():
                if site in new:
                    new[site].append(page)
                else:
                    new[site] = [page]
        # See if new{} contains any problematic values
        result = {}
        for site, pages in new.items():
            if len(pages) > 1:
                errorCount += 1
                self.problem("Found more than one link for %s" % site)
        # If there are any errors, we need to go through all
        # items manually.
        if errorCount > 0 or globalvar.select:

            if config.interwiki_graph:
                graphDrawer = interwiki_graph.GraphDrawer(self)
                graphDrawer.createGraph()

            # We don't need to continue with the rest if we're in autonomous
            # mode.
            if globalvar.autonomous:
                return None

            # First loop over the ones that have more solutions
            for site, pages in new.items():
                if len(pages) > 1:
                    wikipedia.output(u"=" * 30)
                    wikipedia.output(u"Links to %s" % site)
                    i = 0
                    for page2 in pages:
                        i += 1
                        wikipedia.output(u"  (%d) Found link to %s in:" % (i, page2.aslink(True)))
                        self.whereReport(page2, indent = 8)
                    while True:
                        answer = wikipedia.input(u"Which variant should be used [number, (n)one, (g)ive up] :")
                        if answer:
                            if answer == 'g':
                                return None
                            elif answer == 'n':
                                # None acceptable
                                break
                            elif answer.isdigit():
                                answer = int(answer)
                                try:
                                    result[site] = pages[answer - 1]
                                except IndexError:
                                    # user input is out of range
                                    pass
                                else:
                                    break
            # Loop over the ones that have one solution, so are in principle
            # not a problem.
            acceptall = False
            for site, pages in new.items():
                if len(pages) == 1:
                    if not acceptall:
                        wikipedia.output(u"=" * 30)
                        page2 = pages[0]
                        wikipedia.output(u"Found link to %s in:" % page2.aslink(True))
                        self.whereReport(page2, indent = 4)
                    while True:
                        if acceptall: 
                            answer = 'a'
                        else: 
                            answer = wikipedia.inputChoice(u'What should be done?', ['accept', 'reject', 'give up', 'accept all'], ['a', 'r', 'g', 'l'])
                            if not answer:
                                answer = 'a'
                        if answer == 'l': # accept all
                            acceptall = True
                            answer = 'a'
                        if answer == 'a': # accept this one
                            result[site] = pages[0]
                            break
                        elif answer == 'g': # give up
                            return None
                        elif answer == 'r': # reject
                            # None acceptable
                            break
        else: # errorCount <= 0, hence there are no lists longer than one.
            for site, pages in new.items():
                result[site] = pages[0]
        return result
    
    def finish(self, bot = None):
        """Round up the subject, making any necessary changes. This method
           should be called exactly once after the todo list has gone empty.

           This contains a shortcut: if a subject array is given in the argument
           bot, just before submitting a page change to the live wiki it is
           checked whether we will have to wait. If that is the case, the bot will
           be told to make another get request first."""
        if not self.isDone():
            raise "Bugcheck: finish called before done"
        if self.originPage.isRedirectPage():
            return
        if not self.untranslated and globalvar.untranslatedonly:
            return
        # The following check is not always correct and thus disabled.
        # self.done might contain no interwiki links because of the -neverlink
        # argument or because of disambiguation conflicts.
#         if len(self.done) == 1:
#             # No interwiki at all
#             return
        wikipedia.output(u"======Post-processing %s======" % self.originPage.aslink(True))
        # Assemble list of accepted interwiki links
        new = self.assemble()
        if new == None: # User said give up or autonomous with problem
            wikipedia.output(u"======Aborted processing %s======" % self.originPage.aslink(True))
            return
        
        # Make sure new contains every page link, including the page we are processing
        # replaceLinks will skip the site it's working on.
        if not new.has_key(self.originPage.site()):
            new[self.originPage.site()] = self.originPage

        #self.replaceLinks(self.originPage, new, True, bot)

        updatedSites = []
        notUpdatedSites = []
        # Process all languages here
        if globalvar.limittwo:
            lclSite = self.originPage.site()
            lclSiteDone = False
            frgnSiteDone = False
            for siteCode in lclSite.family.languages_by_size + [s for s in lclSite.family.knownlanguages if (not s in lclSite.family.languages_by_size and not s in lclSite.family.obsolete)]:
                site = wikipedia.getSite(code = siteCode)
                if (not lclSiteDone and site == lclSite) or (not frgnSiteDone and site != lclSite and new.has_key(site)):
                    if site == lclSite:
                        lclSiteDone = True   # even if we fail the update
                    if config.usernames.has_key(site.family.name) and config.usernames[site.family.name].has_key(site.lang):
                        try:
                            if self.replaceLinks(new[site], new, bot):
                                updatedSites.append(site)
                            if site != lclSite:
                                 frgnSiteDone = True
                        except SaveError:
                            notUpdatedSites.append(site)
                        except GiveUpOnPage:
                            break
                elif not globalvar.strictlimittwo and new.has_key(site) and site != lclSite:
                    old={}
                    try:
                        for page in new[site].interwiki():
                            old[page.site()] = page
                    except wikipedia.NoPage:
                        wikipedia.output(u"BUG>>> %s no longer exists?" % new[site].aslink(True))
                        continue
                    mods, adding, removing, modifying = compareLanguages(old, new, insite = lclSite)
                    if (len(removing) > 0 and not globalvar.autonomous) or (len(modifying) > 0 and self.problemfound) or len(old.keys()) == 0 or (globalvar.needlimit and len(adding) + len(modifying) >= globalvar.needlimit +1):
                        try:
                            if self.replaceLinks(new[site], new, bot):
                                updatedSites.append(site)
                        except SaveError:
                            notUpdatedSites.append(site)
                        except wikipedia.NoUsername:
                            pass
                        except GiveUpOnPage:
                            break
        else:
            for (site, page) in new.iteritems():
                # if we have an account for this site
                if config.usernames.has_key(site.family.name) and config.usernames[site.family.name].has_key(site.lang):
                    # Try to do the changes
                    try:
                        if self.replaceLinks(page, new, bot):
                            # Page was changed
                            updatedSites.append(site)
                    except SaveError:
                        notUpdatedSites.append(site)
                    except GiveUpOnPage:
                        break
        
        # disabled graph drawing for minor problems: it just takes too long 
        #if notUpdatedSites != [] and config.interwiki_graph:
        #    # at least one site was not updated, save a conflict graph
        #    self.createGraph()
            
        # don't report backlinks for pages we already changed
        if globalvar.backlink:
            self.reportBacklinks(new, updatedSites)

    def replaceLinks(self, page, newPages, bot):
        """
        Returns True if saving was successful.
        """
        if globalvar.localonly:
            # In this case only continue on the Page we started with
            if page != self.originPage:
                raise SaveError

        if page.title() != page.sectionFreeTitle():
            # This is not a page, but a subpage. Do not edit it.
            wikipedia.output(u"Not editing %s: not doing interwiki on subpages" % page.aslink(True))
            raise SaveError
        # Show a message in purple.
        text = u"Updating links on page %s." % page.aslink(True)
        colors = [13] * len(text)
        wikipedia.output(text, colors = colors)

        # clone original newPages dictionary, so that we can modify it to the local page's needs
        new = dict(newPages)
        
        # sanity check - the page we are fixing must be the only one for that site.
        pltmp = new[page.site()]
        if pltmp != page:
            s = "None"
            if pltmp != None: s = pltmp.aslink(True)
            wikipedia.output(u"BUG>>> %s is not in the list of new links! Found %s." % (page.aslink(True), s))
            raise SaveError
        
        # Avoid adding an iw link back to itself
        del new[page.site()]

        # Put interwiki links into a map
        old={}
        try:
            for page2 in page.interwiki():
                old[page2.site()] = page2
        except wikipedia.NoPage:
            wikipedia.output(u"BUG>>> %s no longer exists?" % page.aslink(True))
            raise SaveError

        # Check what needs to get done
        mods, adding, removing, modifying = compareLanguages(old, new, insite = page.site())

        # When running in autonomous mode without -force switch, make sure we don't remove any items, but allow addition of the new ones
        if globalvar.autonomous and not globalvar.force and len(removing) > 0:
            for rmpl in removing:
                if rmpl.site() != page.site():   # Sometimes sites have an erroneous link to itself as an interwiki
                    new[rmpl.site()] = old[rmpl.site()]
                    wikipedia.output(u"WARNING: %s is either deleted or has a mismatching disambiguation state." % rmpl.aslink(True))
            # Re-Check what needs to get done
            mods, adding, removing, modifying = compareLanguages(old, new, insite = page.site())

        if not mods:
            wikipedia.output(u'No changes needed' )
        else:
            if mods:
                wikipedia.output(u"Changes to be made: %s" % mods)
            oldtext = page.get()
            newtext = wikipedia.replaceLanguageLinks(oldtext, new, site = page.site())
            if globalvar.debug:
                wikipedia.showDiff(oldtext, newtext)
            if newtext != oldtext:
                # wikipedia.output(u"NOTE: Replace %s" % page.aslink())
                # Determine whether we need permission to submit
                ask = False
                if removing and removing != [page]:   # Allow for special case of a self-pointing interwiki link
                    # Temporary because of be/be-x-old issue - removing be: is ok if there is a be-x-old: link
                    if len(removing) == 1 and removing[0].site() == wikipedia.getSite('be','wikipedia') and wikipedia.getSite('be-x-old','wikipedia') in new:
                        pass
                    elif len(removing) == 1 and removing[0].site() == wikipedia.getSite('be-x-old','wikipedia') and wikipedia.getSite('be','wikipedia') in new:
                        pass                    
                    else:
                        self.problem('Found incorrect link to %s in %s'% (",".join([x.site().lang for x in removing]), page.aslink(True)), createneed = False)
                        ask = True
                if globalvar.force:
                    ask = False
                if globalvar.confirm:
                    ask = True
                # If we need to ask, do so
                if ask:
                    if globalvar.autonomous:
                        # If we cannot ask, deny permission
                        answer = 'n'
                    else:
                        answer = wikipedia.inputChoice(u'Submit?', ['Yes', 'No', 'Give up'], ['y', 'n', 'g'])
                else:
                    # If we do not need to ask, allow
                    answer = 'y'
                # If we got permission to submit, do so
                if answer == 'y':
                    # Check whether we will have to wait for wikipedia. If so, make
                    # another get-query first.
                    if bot:
                        while wikipedia.get_throttle.waittime() + 2.0 < wikipedia.put_throttle.waittime():
                            wikipedia.output(u"NOTE: Performing a recursive query first to save time....")
                            qdone = bot.oneQuery()
                            if not qdone:
                                # Nothing more to do
                                break
                    wikipedia.output(u"NOTE: Updating live wiki...")
                    timeout=60
                    while 1:
                        try:
                            status, reason, data = page.put(newtext, comment = wikipedia.translate(page.site().lang, msg)[0] + mods)
                        except wikipedia.LockedPage:
                            wikipedia.output(u'Page %s is locked. Skipping.' % (page.title(),))
                            raise SaveError
                        except wikipedia.EditConflict:
                            wikipedia.output(u'ERROR putting page: An edit conflict occurred. Giving up.')
                            raise SaveError                            
                        except (wikipedia.SpamfilterError), error:
                            wikipedia.output(u'ERROR putting page: %s blacklisted by spamfilter. Giving up.' % (error.url,))
                            raise SaveError
                        except (wikipedia.PageNotSaved), error:
                            wikipedia.output(u'ERROR putting page: %s' % (error.args,))
                            raise SaveError
                        except (socket.error, IOError), error:
                            if timeout>3600:
                                raise
                            wikipedia.output(u'ERROR putting page: %s' % (error.args,))
                            wikipedia.output(u'Sleeping %i seconds before trying again.' % (timeout,))
                            timeout *= 2
                            time.sleep(timeout)
                        else:
                            break
                    if str(status) == '302':
                        return True
                    else:
                        wikipedia.output(u'%s %s' % (status, reason))
                elif answer == 'g':
                    raise GiveUpOnPage
                else:
                    raise LinkMustBeRemoved('Found incorrect link to %s in %s'% (",".join([x.site().lang for x in removing]), page.aslink(True)))
            return False

    def reportBacklinks(self, new, updatedSites):
        """
        Report missing back links. This will be called from finish() if needed.

        updatedSites is a list that contains all sites we changed, to avoid
        reporting of missing backlinks for pages we already fixed

        """
        try:
            for site, page in new.iteritems():
                if site not in updatedSites and not page.section():
                    shouldlink = new.values()
                    try:
                        linked = page.interwiki()
                    except wikipedia.NoPage:
                        wikipedia.output(u"WARNING: Page %s does no longer exist?!" % page.title())
                        break
                    for xpage in shouldlink:
                        if xpage != page and not xpage in linked:
                            for l in linked:
                                if l.site() == xpage.site():
                                    wikipedia.output(u"WARNING: %s: %s does not link to %s but to %s" % (page.site().family.name, page.aslink(True), xpage.aslink(True), l.aslink(True)))
                                    break
                            else:
                                wikipedia.output(u"WARNING: %s: %s does not link to %s" % (page.site().family.name, page.aslink(True), xpage.aslink(True)))
                    # Check for superfluous links
                    for xpage in linked:
                        if not xpage in shouldlink:
                            # Check whether there is an alternative page on that language.
                            for l in shouldlink:
                                if l.site() == xpage.site():
                                    # Already reported above.
                                    break
                            else:
                                # New warning
                                wikipedia.output(u"WARNING: %s: %s links to incorrect %s" % (page.site().family.name, page.aslink(True), xpage.aslink(True)))
        except (socket.error, IOError):
            wikipedia.output(u'ERROR: could not report backlinks')
    
class InterwikiBot(object):
    """A class keeping track of a list of subjects, controlling which pages
       are queried from which languages when."""
    
    def __init__(self):
        """Constructor. We always start with empty lists."""
        self.subjects = []
        # We count how many pages still need to be loaded per site.
        # This allows us to find out from which site to retrieve pages next
        # in a way that saves bandwidth.
        # sites are keys, integers are values. 
        # Modify this only via plus() and minus()!
        self.counts = {}
        self.pageGenerator = None
        self.generated = 0

    def add(self, page, hints = None):
        """Add a single subject to the list"""
        subj = Subject(page, hints = hints)
        self.subjects.append(subj)
        for site in subj.openSites():
            # Keep correct counters
            self.plus(site)

    def setPageGenerator(self, pageGenerator, number = None):
        """Add a generator of subjects. Once the list of subjects gets
           too small, this generator is called to produce more Pages"""
        self.pageGenerator = pageGenerator
        self.generateNumber = number

    def dump(self):
        site = wikipedia.getSite()
        import wikipediatools as _wt
        dumpfn = _wt.absoluteFilename('interwiki-dumps', 'interwikidump-%s-%s.txt' % (site.family.name, site.lang))
        f = codecs.open(dumpfn, 'w', 'utf-8')
        for subj in self.subjects:
            f.write(subj.originPage.aslink(None)+'\n')
        f.close()
        wikipedia.output(u'Dump %s (%s) saved' % (site.lang, site.family.name))
        
    def generateMore(self, number):
        """Generate more subjects. This is called internally when the
           list of subjects becomes too small, but only if there is a
           PageGenerator"""
        fs = self.firstSubject()
        if fs:
            wikipedia.output(u"NOTE: The first unfinished subject is " + fs.originPage.aslink(True))
        wikipedia.output(u"NOTE: Number of pages queued is %d, trying to add %d more."%(len(self.subjects), number))
        for i in range(number):
            try:
                while True:
                    page = self.pageGenerator.next()
                    if page in globalvar.skip:
                        wikipedia.output(u'Skipping: %s is in the skip list' % page.title())
                        continue
                    if globalvar.skipauto:
                        dictName, year = page.autoFormat()
                        if dictName != None:
                            wikipedia.output(u'Skipping: %s is an auto entry %s(%s)' % (page.title(),dictName,year))
                            continue
                    if globalvar.bracketonly:
                        if page.title().find("(") == -1:
                            continue
                    break

                self.add(page, hints = hints)
                self.generated += 1
                if self.generateNumber:
                    if self.generated == self.generateNumber:
                        self.pageGenerator = None
                        break
            except StopIteration:
                self.pageGenerator = None
                break

    def firstSubject(self):
        """Return the first subject that is still being worked on"""
        if self.subjects:
            return self.subjects[0]
        
    def maxOpenSite(self):
        """Return the site that has the most
           open queries plus the number. If there is nothing left, return
           None. Only languages that are TODO for the first Subject
           are returned."""
        max = 0
        maxlang = None
        if not self.firstSubject():
            return None
        oc = self.firstSubject().openSites()
        if not oc:
            # The first subject is done. This might be a recursive call made because we
            # have to wait before submitting another modification to go live. Select
            # any language from counts.
            oc = self.counts.keys()
        if wikipedia.getSite() in oc:
            return wikipedia.getSite()
        for lang in oc:
            count = self.counts[lang]
            if count > max:
                max = count
                maxlang = lang
        return maxlang

    def selectQuerySite(self):
        """Select the site the next query should go out for."""
        # How many home-language queries we still have?
        mycount = self.counts.get(wikipedia.getSite(), 0)
        # Do we still have enough subjects to work on for which the
        # home language has been retrieved? This is rough, because
        # some subjects may need to retrieve a second home-language page!
        if len(self.subjects) - mycount < globalvar.minarraysize:
            # Can we make more home-language queries by adding subjects?
            if self.pageGenerator and mycount < globalvar.maxquerysize:
                timeout = 60
                while timeout<3600:
                    try:
                        self.generateMore(globalvar.maxquerysize - mycount)
                    except wikipedia.ServerError:
                        # Could not extract allpages special page?
                        wikipedia.output(u'ERROR: could not retrieve more pages. Will try again in %d seconds'%timeout)
                        time.sleep(timeout)
                        timeout *= 2
                    else:
                        break
            # If we have a few, getting the home language is a good thing.
            try:
                if self.counts[wikipedia.getSite()] > 4:
                    return wikipedia.getSite()
            except KeyError:
                pass
        # If getting the home language doesn't make sense, see how many 
        # foreign page queries we can find.
        return self.maxOpenSite()
    
    def oneQuery(self):
        """
        Perform one step in the solution process.

        Returns True if pages could be preloaded, or false
        otherwise.
        """
        # First find the best language to work on
        site = self.selectQuerySite()
        if site == None:
            wikipedia.output(u"NOTE: Nothing left to do")
            return False
        # Now assemble a reasonable list of pages to get
        subjectGroup = []
        pageGroup = []
        for subject in self.subjects:
            # Promise the subject that we will work on the site.
            # We will get a list of pages we can do.
            pages = subject.willWorkOn(site)
            if pages:
                pageGroup.extend(pages)
                subjectGroup.append(subject)
                if len(pageGroup) >= globalvar.maxquerysize:
                    # We have found enough pages to fill the bandwidth.
                    break
        if len(pageGroup) == 0:
            wikipedia.output(u"NOTE: Nothing left to do 2")
            return False
        # Get the content of the assembled list in one blow
        gen = pagegenerators.PreloadingGenerator(iter(pageGroup))
        for page in gen:
            # we don't want to do anything with them now. The
            # page contents will be read via the Subject class.
            pass
        # Tell all of the subjects that the promised work is done
        for subject in subjectGroup:
            subject.workDone(self)
        return True
        
    def queryStep(self):
        self.oneQuery()
        # Delete the ones that are done now.
        for i in range(len(self.subjects)-1, -1, -1):
            subj = self.subjects[i]
            if subj.isDone():
                subj.finish(self)
                del self.subjects[i]
    
    def isDone(self):
        """Check whether there is still more work to do"""
        return len(self) == 0 and self.pageGenerator is None

    def plus(self, site):
        """This is a routine that the Subject class expects in a counter"""
        try:
            self.counts[site] += 1
        except KeyError:
            self.counts[site] = 1

    def minus(self, site):
        """This is a routine that the Subject class expects in a counter"""
        self.counts[site] -= 1
        
    def run(self):
        """Start the process until finished"""
        while not self.isDone():
            self.queryStep()

    def __len__(self):
        return len(self.subjects)
    
def compareLanguages(old, new, insite):
    removing = []
    adding = []
    modifying = []
    for site in old.keys():
        if site not in new:
            removing.append(old[site])
        elif old[site] != new[site]:
            modifying.append(new[site])

    for site2 in new.keys():
        if site2 not in old:
            adding.append(new[site2])
    mods = ""
    # sort by language code
    adding.sort()
    modifying.sort()
    removing.sort()
    
    if len(adding) + len(removing) + len(modifying) <= 3:
        # Use an extended format for the string linking to all added pages.
        fmt = lambda page: page.aslink(forceInterwiki=True)
    else:
        # Use short format, just the language code
        fmt = lambda page: page.site().lang
    
    if adding:
        mods += " %s: %s" % (wikipedia.translate(insite.lang, msg)[1], ", ".join([fmt(x) for x in adding]))
    if removing: 
        mods += " %s: %s" % (wikipedia.translate(insite.lang, msg)[2], ", ".join([fmt(x) for x in removing]))
    if modifying:
        mods += " %s: %s" % (wikipedia.translate(insite.lang, msg)[3], ", ".join([fmt(x) for x in modifying]))
    return mods, adding, removing, modifying

def readWarnfile(filename, bot):
    import warnfile
    reader = warnfile.WarnfileReader(filename)
    # we won't use removeHints
    (hints, removeHints) = reader.getHints()
    pages = hints.keys()
    for page in pages:
        # The WarnfileReader gives us a list of pagelinks, but titletranslate.py expects a list of strings, so we convert it back.
        # TODO: This is a quite ugly hack, in the future we should maybe make titletranslate expect a list of pagelinks.
        hintStrings = ['%s:%s' % (hintedPage.site().language(), hintedPage.title()) for hintedPage in hints[page]]
        bot.add(page, hints = hintStrings)

#===========
        
globalvar=Global()
    
if __name__ == "__main__":
    try:
        singlePageTitle = []
        hints = []
        start = None
        number = None
        warnfile = None
        # a normal PageGenerator (which doesn't give hints, only Pages)
        hintlessPageGen = None
        optContinue = False
        optRestore = False
        # This factory is responsible for processing command line arguments
        # that are also used by other scripts and that determine on which pages
        # to work on.
        genFactory = pagegenerators.GeneratorFactory()
        
        if not config.never_log:
            wikipedia.activateLog('interwiki.log')

        for arg in wikipedia.handleArgs():
            if arg == '-noauto':
                globalvar.auto = False
            elif arg.startswith('-hint:'):
                hints.append(arg[6:])
            elif arg == '-force':
                globalvar.force = True
            elif arg == '-same':
                globalvar.same = True
            elif arg == '-wiktionary':
                globalvar.same = 'wiktionary'
            elif arg == '-untranslated':
                globalvar.untranslated = True
            elif arg == '-untranslatedonly':
                globalvar.untranslated = True
                globalvar.untranslatedonly = True
            elif arg == '-askhints':
                globalvar.untranslated = True
                globalvar.untranslatedonly = False
                globalvar.askhints = True    
            elif arg == '-noauto':
                pass
            elif arg.startswith('-warnfile:'):
                warnfile = arg[10:]
            elif arg == '-confirm':
                globalvar.confirm = True
            elif arg == '-select':
                globalvar.select = True
            elif arg == '-autonomous':
                globalvar.autonomous = True
            elif arg == '-noshownew':
                globalvar.shownew = False
            elif arg == '-nobacklink':
                globalvar.backlink = False
            elif arg == '-noredirect':
                globalvar.followredirect = False
            elif arg == '-localonly':
                globalvar.localonly = True
            elif arg == '-limittwo':
                globalvar.limittwo = True
                globalvar.strictlimittwo = True
            elif arg.startswith('-whenneeded'):
                globalvar.limittwo = True
                globalvar.strictlimittwo = False
                try:
                    globalvar.needlimit = int(arg[12:])
                except KeyError:
                    pass
                except ValueError:
                    pass
            elif arg.startswith('-years'):
                # Look if user gave a specific year at which to start
                # Must be a natural number or negative integer.
                if len(arg) > 7 and (arg[7:].isdigit() or (arg[7] == "-" and arg[8:].isdigit())):
                    startyear = int(arg[7:])
                else:
                    startyear = 1
                # avoid problems where year pages link to centuries etc.
                globalvar.followredirect = False
                hintlessPageGen = pagegenerators.YearPageGenerator(startyear)
            elif arg.startswith('-days'):
                if len(arg) > 6 and arg[5] == ':' and arg[6:].isdigit():
                    # Looks as if the user gave a specific month at which to start
                    # Must be a natural number.
                    startMonth = int(arg[6:])
                else:
                    startMonth = 1
                hintlessPageGen = pagegenerators.DayPageGenerator(startMonth)
            elif arg.startswith('-skipfile:'):
                skipfile = arg[10:]
                skipPageGen = pagegenerators.TextfilePageGenerator(skipfile)
                for page in skipPageGen:
                    globalvar.skip.add(page)
            elif arg == '-skipauto':
                globalvar.skipauto = True
            elif arg == '-restore':
                optRestore = True
            elif arg == '-continue':
                optContinue = True
            # deprecated for consistency with other scripts
            elif arg.startswith('-number:'):
                number = int(arg[8:])
            elif arg.startswith('-array:'):
                globalvar.minarraysize = int(arg[7:])
            elif arg.startswith('-neverlink:'):
                globalvar.neverlink += arg[11:].split(",")
            elif arg.startswith('-ignore:'):
                globalvar.ignore += [wikipedia.Page(None,p) for p in arg[8:].split(",")]
            elif arg.startswith('-ignorefile:'):
                ignorefile = arg[12:]
                ignorePageGen = pagegenerators.TextfilePageGenerator(ignorefile)
                for page in ignorePageGen:
                    globalvar.ignore.append(page)
            elif arg == '-showpage':
                globalvar.showtextlink += globalvar.showtextlinkadd
            elif arg == '-graph':
                # override configuration
                config.interwiki_graph = True
            elif arg == '-bracket':
                globalvar.bracketonly = True
            else:
                generator = genFactory.handleArg(arg)
                if generator:
                    hintlessPageGen = generator
                else:
                    singlePageTitle.append(arg)
        
        # ensure that we don't try to change main page
        try:
            site = wikipedia.getSite()
            mainpagename = site.family.mainpages[site.language()]
            globalvar.skip.add(wikipedia.Page(site, mainpagename))
        except:
            wikipedia.output(u'Missing main page name')

        if optRestore or optContinue:
            site = wikipedia.getSite()
            import wikipediatools as _wt
            dumpFileName = _wt.absoluteFilename('interwiki-dumps', u'interwikidump-%s-%s.txt' % (site.family.name, site.lang))
            hintlessPageGen = pagegenerators.TextfilePageGenerator(dumpFileName)
            if optContinue:
                # We waste this generator to find out the last page's title
                # This is an ugly workaround.
                for page in hintlessPageGen:
                    pass
                try:
                    nextPage = page.titleWithoutNamespace() + '!'
                    namespace = page.namespace()
                except NameError:
                    wikipedia.output(u"Dump file is empty?! Starting at the beginning.")
                    nextPage = "!"
                    namespace = 0
                # old generator is used up, create a new one
                hintlessPageGen = pagegenerators.CombinedPageGenerator([pagegenerators.TextfilePageGenerator(dumpFileName), pagegenerators.AllpagesPageGenerator(nextPage, namespace, includeredirects = False)])

        bot = InterwikiBot()

        if hintlessPageGen:
            # we'll use iter() to create make a next() function available.
            bot.setPageGenerator(iter(hintlessPageGen),number = number)
        elif warnfile:
            readWarnfile(warnfile, bot)
        else:
            singlePageTitle = ' '.join(singlePageTitle)
            if not singlePageTitle:
                singlePageTitle = wikipedia.input(u'Which page to check:')
            singlePage = wikipedia.Page(wikipedia.getSite(), singlePageTitle)
            bot.add(singlePage, hints = hints)
        
        try:
            bot.run()
        except KeyboardInterrupt:
            bot.dump()
        except:
            bot.dump()
            raise

    finally:
        wikipedia.stopme()
