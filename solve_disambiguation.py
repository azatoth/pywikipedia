#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to help a human solve disambiguations by presenting a set of options.

Specify the disambiguation page on the command line, or enter it at the
prompt after starting the program. (If the disambiguation page title starts
with a '-', you cannot name it on the command line, but you can enter it at
the prompt.)  The program will pick up the page, and look for all
alternative links, and show them with a number adjacent to them.  It will
then automatically loop over all pages referring to the disambiguation page,
and show 30 characters of context on each side of the reference to help you
make the decision between the alternatives.  It will ask you to type the
number of the appropriate replacement, and perform the change.

It is possible to choose to replace only the link (just type the number) or
replace both link and link-text (type 'r' followed by the number).

Multiple references in one page will be scanned in order, but typing 'n' (next)
on any one of them will leave the complete page unchanged. To leave only some reference unchanged, use the 's' (skip) option.

Command line options:

   -pos:XXXX   adds XXXX as an alternative disambiguation

   -just       only use the alternatives given on the command line, do not
               read the page for other possibilities

   -primary    "primary topic" disambiguation (Begriffsklärung nach Modell 2).
               That's titles where one topic is much more important, the
               disambiguation page is saved somewhere else, and the important
               topic gets the nice name.

   -primary:XY like the above, but use XY as the only alternative, instead of
               searching for alternatives in [[Keyword (disambiguation)]].
               Note: this is the same as -primary -just -pos:XY

   -file:XYZ   reads a list of pages from a text file. XYZ is the name of the
               file from which the list is taken. If XYZ is not given, the user is asked for a filename.
               Page titles should be inside [[double brackets]].
               The -pos parameter won't work if -file is used.

   -always:XY  instead of asking the user what to do, always perform the same
               action. For example, XY can be "r0", "u" or "2". Be careful with
               this option, and check the changes made by the bot. Note that
               some choices for XY don't make sense and will result in a loop,
               e.g. "l" or "m".

   -main       only check pages in the main namespace, not in the talk,
               wikipedia, user, etc. namespaces.

   -start:XY   goes through all disambiguation pages in the category on your wiki
               that is defined (to the bot) as the category containing disambiguation
               pages, starting at XY. If only '-start' or '-start:' is given, it starts
               at the beginning.

To complete a move of a page, one can use:

    python solve_disambiguation.py -just -pos:New_Name Old_Name
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
# (C) Andre Engels, 2003-2004
# (C) WikiWichtel, 2004
#
# Distributed under the terms of the MIT license.
#
__version__='$Id$'
#
# Standard library imports
import re, sys, codecs

# Application specific imports
import wikipedia, pagegenerators, editarticle

# This is a purely interactive robot. We set the delays lower.
wikipedia.put_throttle.setDelay(4)

# Summary message when working on disambiguation pages
msg = {
    'cs': u'Odstranění linku na rozcestník [[%s]] s použitím robota',
    'en': u'Robot-assisted disambiguation: %s',
    'da': u'Retter flertydigt link til: %s',
    'de': u'Bot-unterstützte Begriffsklärung: %s',
    'fr': u'Homonymie résolue à l\'aide du robot: %s',
    'he': u'תיקון הפניה לדף פירושונים באמצעות בוט: %s',
    'ia': u'Disambiguation assistite per robot: %s',
    'it': u'Sistemazione automatica della disambigua: %s',
    'lt': u'Nuorodų į nukrepiamąjį straipsnį keitimas: %s',
    'nl': u'Robot-geholpen doorverwijzing: %s',
    'pt': u'Desambiguação assistida por bot: %s',
    'ru': u'Разрешение значений с помощью бота: %s',
    'sr': u'Решавање вишезначних одредница помоћу бота: %s',
    'sv': u'Länkar direkt till rätt artikel för: %s',
    }

# Summary message when working on redirects
msg_redir = {
    'cs': u'Robot opravil přesměrování na %s',
    'en': u'Robot-assisted disambiguation: %s',
    'da': u'Retter flertydigt link til: %s',
    'de': u'Bot-unterstützte Redirectauflösung: %s',
    'fr': u'Correction de lien vers redirect: %s',
    'he': u'תיקון הפניה לדף פירושונים באמצעות בוט: %s',
    'ia': u'Resolution de redirectiones assistite per robot: %s',
    'it': u'Sistemazione automatica del redirect: %s',
    'lt': u'Nuorodų į peradresavimo straipsnį keitimas: %s',
    'nl': u'Robot-geholpen redirect-oplossing: %s',
    'pt': u'Desambiguação assistida por bot: %s',
    'ru': u'Разрешение значений с помощью бота: %s',
    'sr': u'Решавање вишезначних одредница помоћу бота: %s',
    'sv': u'Länkar direkt till rätt artikel för: %s',
    }

# disambiguation page name format for "primary topic" disambiguations
# (Begriffsklärungen nach Modell 2)
primary_topic_format = {
    'cs': u'%s_(rozcestník)',
    'de': u'%s_(Begriffsklärung)',
    'en': u'%s_(disambiguation)',
    'ia': u'%s_(disambiguation)',
    'it': u'%s_(disambigua)',
    'lt': u'%s_(reikšmės)',
    'nl': u'%s_(doorverwijspagina)',
    'pt': u'%s_(desambiguação)',
    'he': u'%s_(פירושונים)',
    'ru': u'%s_(значения)',
    'sr': u'%s_(вишезначна одредница)',
    'sv': u'%s_(olika betydelser)',
    }

# List pages that will be ignored if they got a link to a disambiguation
# page. An example is a page listing disambiguations articles.
# Special chars should be encoded with unicode (\x##) and space used
# instead of _

ignore_title = {
    'wikipedia': {
        'cs': [
            u'Wikipedie:Chybějící interwiki/.+',
            u'Wikipedie:Rozcestníky',
            u'Wikipedie diskuse:Rozcestníky',
            u'Wikipedie:Seznam rozcestníků/první typ',
            u'Wikipedie:Seznam rozcestníků/druhý typ',
        ],
        'da': [
            u'Wikipedia:Links til sider med flertydige titler'
        ],
        'de': [
            u'Benutzer:Katharina/Begriffsklärungen',
            u'Benutzer:Noisper/Dingliste/[A-Z]',
            u'Benutzer:SirJective/.+',
            u'Benutzer Diskussion:.+',
            u'GISLexikon \([A-Z]\)',
            u'Lehnwort',
            u'Wikipedia:Archiv:.+',
            u'Wikipedia:Artikelwünsche/Ding-Liste/[A-Z]',
            u'Wikipedia:Begriffsklärung.*',
            u'Wikipedia:Dreibuchstabenkürzel von [A-Z][A-Z][A-Z] bis [A-Z][A-Z][A-Z]',
            u'Wikipedia:Interwiki-Konflikte',
            u'Wikipedia:Kurze Artikel',
            u'Wikipedia:Liste aller 2-Buchstaben-Kombinationen',
            u'Wikipedia:Liste mathematischer Themen/BKS',
            u'Wikipedia:Liste mathematischer Themen/Redirects',
            u'Wikipedia:Löschkandidaten/.+',
            u'Wikipedia:Qualitätsoffensive/UNO', #requested by Benutzer:Addicted 
            u'Wikipedia:WikiProjekt Altertumswissenschaft/.+',
        ],
         'en': [
            u'Wikipedia:Links to disambiguating pages',
            u'Wikipedia:Disambiguation pages with links',
            u'Wikipedia:Multiple-place names \([A-Z]\)',
            u'Wikipedia:Non-unique personal name',
            u"User:Jerzy/Disambiguation Pages i've Editted",
            u'User:Gareth Owen/inprogress',
            u'TLAs from [A-Z][A-Z][A-Z] to [A-Z][A-Z][A-Z]',
            u'List of all two-letter combinations',
            u'User:Daniel Quinlan/redirects.+',
            u'User:Oliver Pereira/stuff',
            u'Wikipedia:French Wikipedia language links',
            u'Wikipedia:Polish language links',
            u'Wikipedia:Undisambiguated abbreviations/.+',
            u'List of acronyms and initialisms',
            u'Wikipedia:Usemod article histories',
            u'User:Pizza Puzzle/stuff',
            u'List of generic names of political parties',
            u'Talk:List of initialisms/marked',
            u'Talk:List of initialisms/sorted',
            u'Talk:Programming language',
            u'Talk:SAMPA/To do',
            u"Wikipedia:Outline of Roget's Thesaurus",
            u'User:Wik/Articles',
            u'User:Egil/Sandbox',
            u'Wikipedia talk:Make only links relevant to the context',
            u'Wikipedia:Common words, searching for which is not possible',
        ],
        'fr': [
            u'Wikipédia:Liens aux pages d\'homonymie',
            u'Wikipédia:Homonymie',
            u'Wikipédia:Homonymie/Homonymes dynastiques',
            u'Wikipédia:Prise de décision, noms des membres de dynasties/liste des dynastiens',
            u'Liste de toutes les combinaisons de deux lettres',
            u'Wikipédia:Log d\'upload/.*',
            u'Sigles de trois lettres de [A-Z]AA à [A-Z]ZZ',
            u'Wikipédia:Pages sans interwiki,.'
        ],
        'fy': [
            u'Wikipedy:Fangnet',
        ],
        'ia': [
            u'Categoria:Disambiguation',
            u'Wikipedia:.+',
            u'Usator:.+',
            u'Discussion Usator:.+',
        ],
        'it': [
 	    u'Aiuto:Disambigua/Disorfanamento',
 	    u'Discussioni utente:.+',
 	    u'Utente:Civvi/disorfanamento',
 	],
        'lt': [
            u'Wikipedia:Rodomi nukreipiamieji straipsniai',
        ],
        'nl': [
            u'Wikipedia:Onderhoudspagina',
            u'Wikipedia:Doorverwijspagina',
            u'Wikipedia:Lijst van alle tweeletter-combinaties',
            u'Gebruiker:Hooft/robot/Interwiki/lijst van problemen',
            u'Wikipedia:Woorden die niet als zoekterm gebruikt kunnen worden',
            u'Gebruiker:Puckly/Bijdragen',
            u'Gebruiker:Waerth/bijdragen',
            u"Wikipedia:Project aanmelding bij startpagina's",
            u'Gebruiker:Gustar/aantekeningen denotatie annex connotatie',
            u'Wikipedia:Protection log',
            u'Gebruiker:Pven/Romeinse cijfers',
            u'Categorie:Doorverwijspagina',
            u'Wikipedia:Ongelijke redirects',
            u'Gebruiker:Cars en travel',
            u'Overleg Wikipedia:Logboek*',
            u'Gebruiker:Rex/Gestarte artikelen',
            u'Gebruiker:Ucucha/Doorverwijspagina',
            u'Gebruiker:CyeZ/Klad2',
            u'Wikipedia:Te verwijderen.*',
            u'Gebruiker:IIVQ.*',
            u"Gebruiker:Rex/Meest storende doorverwijspagina's",
            u'Gebruiker:Mystro82',
            u'Overleg:Lage Landen (staatkunde)',
            u'Overleg gebruiker:Sybren/test.*',
            u'Gebruiker:Verrekijker/Alle edits',
            u'Gebruiker:Verrekijker/Bijdragen',
            u'Gebruiker:Sybren/Verwijzingen',
            u'Overleg Wikipedia:Doorverwijspagina',
            u'Gebruiker:Al/Bijdragen',
            u'Gebruiker:Ellywa/kladblok',
            u'Gebruiker:Yorian/oud',
            u'Lijst van Nederlandse namen van pausen',
            u"Gebruiker:Henna/Ucacha's redirects",
            u"Gebruiker:Andre Engels/Haakjesproblemen.*",
            u"Gebruiker:Dedalus/Namen/.",
            u"Gebruiker:R.Koot/Unicode",
            u"Gebruiker:Magalhães/Artikelen",
            u"Gebruiker:Rex/Encarta/.+",
            u'Wikipedia:.+rchief.*',
            u"Gebruiker:R'n'B/DPL",
            u"Portaal:.+[aA]rchief.*",
            u"Gebruiker:Erik Baas.*",
            u"Gebruiker:Venullian/Aanvulverhaal",
            u"Overleg gebruiker:Pven",
            u"Wikipedia:Humor en onzin.*",
            u"Gebruiker:.+[aA]rchief.*",
            u"Overleg gebruiker:.+[aA]rchief.*",
            u"Wikipedia:Wikiproject Roemeense gemeenten/Doorverwijspagina's",
            u"Gebruiker:Emiel/artikelen",
            u"Wikipedia:Links naar doorverwijspagina's/20060917 dump",
            u'Gebruiker:Waerth/Wikipedia hitsparade.*',
            u'Overleg gebruiker:[0-9][0-9]?[0-9]?\.[0-9][0-9]?[0-9]?\.[0-9][0-9]?[0-9]?\.[0-9][0-9]?[0-9]?',
            u'Gebruiker:Lankhorst/Lijst.*',
            u'Wikipedia:Wikipedianen met een encyclopedisch artikel',
            u'Gebruiker:Al/Informatie Roemenië/.*',
            u'Gebruiker:GruffiGummi:Problemen',
            u'Gebruiker:Thor NL/Onderhanden werk/.+',
         ],
        'pt': [
            u'Usuário:.+',
            u'Usuário Discussão:.+',
            u'Lista de combinações de duas letras',
        ],
        'ru': [
            u'Категория:Disambig',
            u'Википедия:Страницы разрешения неоднозначностей',
            u'Википедия:Вики-уборка/Статьи без языковых ссылок',
            u'Википедия:Страницы с пометкой «(значения)»',
            u'Список общерусских фамилий',
        ],
    },
    'memoryalpha': {
        'en': [
            u'Memory Alpha:Links to disambiguating pages'
        ],
        'de': [
            u'Memory Alpha:Liste der Wortklärungsseiten'
        ],
    },
}

def firstcap(string):
    return string[0].upper()+string[1:]

class ReferringPageGeneratorWithIgnore:
    def __init__(self, disambPage, primary=False):
        self.disambPage = disambPage
        # if run with the -primary argument, enable the ignore manager
        self.primaryIgnoreManager = PrimaryIgnoreManager(disambPage,
                                                         enabled=primary)
        
    def __iter__(self):
        # TODO: start yielding before all referring pages have been found
        refs = [page for page in self.disambPage.getReferences(follow_redirects = False, withTemplateInclusion = False)]
        wikipedia.output(u"Found %d references." % len(refs))
        # Remove ignorables
        if ignore_title.has_key(self.disambPage.site().family.name) and ignore_title[self.disambPage.site().family.name].has_key(self.disambPage.site().lang):
            for ig in ignore_title[self.disambPage.site().family.name][self.disambPage.site().lang]:
                for i in range(len(refs)-1, -1, -1):
                    if re.match(ig, refs[i].title()):
                        wikipedia.output('Ignoring page %s' % refs[i].title())
                        del refs[i]
                    elif self.primaryIgnoreManager.isIgnored(refs[i]):
                        #wikipedia.output('Ignoring page %s because it was skipped before' % refs[i].title())
                        del refs[i]
        wikipedia.output(u"Will work on %d pages." % len(refs))
        for ref in refs:
            yield ref

class PrimaryIgnoreManager(object):
    '''
    If run with the -primary argument, reads from a file which pages should
    not be worked on; these are the ones where the user pressed n last time.
    If run without the -primary argument, doesn't ignore any pages.
    '''
    def __init__(self, disambPage, enabled = False):
        self.disambPage = disambPage
        self.enabled = enabled
        
        self.ignorelist = []
        filename = 'disambiguations/' + self.disambPage.urlname() + '.txt'
        try:
            # The file is stored in the disambiguation/ subdir. Create if necessary.
            f = codecs.open(self.makepath(filename), 'r', 'utf-8')
            for line in f.readlines():
                # remove trailing newlines and carriage returns
                while line[-1] in ['\n', '\r']:
                    line = line[:-1]
                #skip empty lines
                if line != '':
                    self.ignorelist.append(line)
            f.close()
        except IOError:
            pass

    def isIgnored(self, refPage):
        return self.enabled and refPage.urlname() in self.ignorelist
        
    def ignore(self, refPage):
        if self.enabled:
            # Skip this occurence next time.
            filename = 'disambiguations/' + self.disambPage.urlname() + '.txt'
            try:
                # Open file for appending. If none exists yet, create a new one.
                # The file is stored in the disambiguation/ subdir. Create if necessary.
                f = codecs.open(self.makepath(filename), 'a', 'utf-8')
                f.write(refPage.urlname() + '\n')
                f.close()
            except IOError:
                pass

    def makepath(self, path):
        """ creates missing directories for the given path and
            returns a normalized absolute version of the path.
    
        - if the given path already exists in the filesystem
          the filesystem is not modified.
    
        - otherwise makepath creates directories along the given path
          using the dirname() of the path. You may append
          a '/' to the path if you want it to be a directory path.
    
        from holger@trillke.net 2002/03/18
        """
        from os import makedirs
        from os.path import normpath,dirname,exists,abspath
    
        dpath = normpath(dirname(path))
        if not exists(dpath): makedirs(dpath)
        return normpath(abspath(path))
    

class DisambiguationRobot(object):
    ignore_contents = {
        'de':(u'{{[Ii]nuse}}',
              u'{{[Ll]öschen}}',
            ),
        'nl':(u'{{wiu2}}',
              u'{{nuweg}}',
            ),
        'ru':(u'{{[Ii]nuse}}',
              u'{{[Pp]rocessing}}',
            ),
    }
    
    def __init__(self, always, alternatives, getAlternatives, generator, primary, main_only):
        self.always = always
        self.alternatives = alternatives
        self.getAlternatives = getAlternatives
        self.generator = generator
        self.primary = primary
        self.main_only = main_only

        self.mysite = wikipedia.getSite()
        self.mylang = self.mysite.language()

        self.setupRegexes()
        
    def checkContents(self, text):
        '''
        For a given text, returns False if none of the regular
        expressions given in the dictionary at the top of this class
        matches a substring of the text.
        Otherwise returns the substring which is matched by one of
        the regular expressions.
        '''
        for ig in self.ignore_contents_regexes:
            match = ig.search(text)
            if match:
                return match.group()
        return None
    
    def makeAlternativesUnique(self):
        # remove duplicate entries
        result={}
        for i in self.alternatives:
            result[i]=None
        self.alternatives = result.keys()
    
    def listAlternativesGui(self):
        # list in new window, does not behave as expected, so not used currently.
        print '\n\t\t--> beachte neues Fenster <--'
        import gui
        list_window = gui.ListBoxWindow()
        list_window.list(self.alternatives)
    
    def listAlternatives(self):
        list = u'\n'
        for i in range(len(self.alternatives)):
            list += (u"%3i - %s\n" % (i, self.alternatives[i]))
        wikipedia.output(list)

    def setupRegexes(self):
        # compile regular expressions
        self.ignore_contents_regexes = []
        if self.ignore_contents.has_key(self.mylang):
            for ig in self.ignore_contents[self.mylang]:
                self.ignore_contents_regexes.append(re.compile(ig))

        linktrail = self.mysite.linktrail()
        self.trailR = re.compile(linktrail)
        # The regular expression which finds links. Results consist of four groups:
        # group title is the target page title, that is, everything before | or ].
        # group section is the page section. It'll include the # to make life easier for us.
        # group label is the alternative link title, that's everything between | and ].
        # group linktrail is the link trail, that's letters after ]] which are part of the word.
        # note that the definition of 'letter' varies from language to language.
        self.linkR = re.compile(r'\[\[(?P<title>[^\]\|#]*)(?P<section>#[^\]\|]*)?(\|(?P<label>[^\]]*))?\]\](?P<linktrail>' + linktrail + ')')
        
    def treat(self, refPage, disambPage):
        """
        Parameters:
            disambPage - The disambiguation page or redirect we don't want anything
                     to link on
            refPage - A page linking to disambPage
        Returns False if the user pressed q to completely quit the program.
        Otherwise, returns True.
        """
        # TODO: break this function up into subroutines!

        include = False
        try:
            text=refPage.get(throttle=False)
            ignoreReason = self.checkContents(text)
            if ignoreReason:
                wikipedia.output('\n\nSkipping %s because it contains %s.\n\n' % (refPage.title(), ignoreReason))
            else:
                include = True
        except wikipedia.IsRedirectPage:
            wikipedia.output(u'%s is a redirect to %s' % (refPage.title(), disambPage.title()))
            if disambPage.isRedirectPage():
                target = self.alternatives[0]
                choice = wikipedia.inputChoice(u'Do you want to make redirect %s point to %s?' % (refPage.title(), target), ['yes', 'no'], ['y', 'N'], 'N')
                if choice in ['y', 'Y']:
                    redir_text = '#%s [[%s]]' % (self.mysite.redirect(default=True), target)
                    try:
                        refPage.put(redir_text)
                    except wikipedia.PageNotSaved, error:
                        wikipedia.output(u'Page not saved: %s' % error)
            else:
                choice = wikipedia.inputChoice(u'Do you want to work on pages linking to %s?' % refPage.title(), ['yes', 'no', 'change redirect'], ['y', 'N', 'c'], 'N')
                if choice in ['y', 'Y']:
                    gen = ReferringPageGeneratorWithIgnore(refPage, self.primary)
                    preloadingGen = pagegenerators.PreloadingGenerator(gen)
                    for refPage2 in preloadingGen:
                        # run until the user selected 'quit'
                        if not self.treat(refPage2, refPage):
                            break
                elif choice in ['c', 'C']:
                    text=refPage.get(throttle=False,get_redirect=True)
                    include = "redirect"
        except wikipedia.NoPage:
            wikipedia.output(u'Page [[%s]] does not seem to exist?! Skipping.' % refPage.title())
            include = False
        if include in (True, "redirect"):
            # make a backup of the original text so we can show the changes later
            original_text = text
            n = 0
            curpos = 0
            edited = False
            # This loop will run until we have finished the current page
            while True:
                m = self.linkR.search(text, pos = curpos)
                if not m:
                    if n == 0:
                        wikipedia.output(u"No changes necessary in %s" % refPage.title())
                        return True
                    else:
                        # stop loop and save page
                        break
                # Make sure that next time around we will not find this same hit.
                curpos = m.start() + 1
                # ignore interwiki links and links to sections of the same page
                if m.group('title') == '' or self.mysite.isInterwikiLink(m.group('title')):
                    continue
                else:
                    linkPage = wikipedia.Page(disambPage.site(), m.group('title'))
                    # Check whether the link found is to disambPage.
                    if linkPage != disambPage:
                        continue
    
                n += 1
                # how many bytes should be displayed around the current link
                context = 30
                # This loop will run while the user doesn't choose an option
                # that will actually change the page
                while True:
                    # Show the title of the page where the link was found.
                    # Highlight the title in purple.
                    colors = [None] * 6 + [13] * len(refPage.title()) + [None] * 4
                    wikipedia.output(u"\n\n>>> %s <<<" % refPage.title(), colors = colors)
                    
                    
                    # at the beginning of the link, start red color.
                    # at the end of the link, reset the color to default
                    
                    colors = [None for c in text[max(0, m.start() - context) : m.start()]] + [12 for c in text[m.start() : m.end()]] + [None for c in text[m.end() : m.end() + context]]
                    wikipedia.output(text[max(0, m.start() - context) : m.end() + context], colors = colors)

                    if not self.always:
                        if edited:
                            choice = wikipedia.input(u"Option (#, r#, s=skip link, e=edit page, n=next page, u=unlink, q=quit\n"
                                               "        m=more context, l=list, a=add new, x=save in this form):")
                        else:
                            choice = wikipedia.input(u"Option (#, r#, s=skip link, e=edit page, n=next page, u=unlink, q=quit\n"
                                               "        m=more context, d=show disambiguation page, l=list, a=add new):")
                    else:
                        choice = self.always
                    if choice in ['a', 'A']:
                        newAlternative = wikipedia.input(u'New alternative:')
                        self.alternatives.append(newAlternative)
                        self.listAlternatives()
                    elif choice in ['e', 'E']:
                        editor = editarticle.TextEditor()
                        newText = editor.edit(text, jumpIndex = m.start(), highlight = disambPage.title())
                        # if user didn't press Cancel
                        if newText and newText != text:
                            text = newText
                            break
                    elif choice in ['d', 'D']:
                        editor = editarticle.TextEditor()
                        if disambPage.isRedirectPage():
                            disambredir1 = disambPage.getRedirectTarget()
                            disambredir2 = wikipedia.Page(wikipedia.getSite(), disambredir1)
                            disambigText = editor.edit(disambredir2.get(), jumpIndex = m.start(), highlight = disambredir2.title())
                        else:
                            disambigText = editor.edit(disambPage.get(), jumpIndex = m.start(), highlight = disambPage.title())
                    elif choice in ['l', 'L']:
                        self.listAlternatives()
                    elif choice in ['m', 'M']:
                        # show more text around the link we're working on
                        context *= 2
                    else:
                        break
            
                if choice in ['e', 'E']:
                    # user has edited the page and then pressed 'OK'
                    edited = True
                    curpos = 0
                    continue
                elif choice in ['n', 'N']:
                    # skip this page
                    if self.primary:
                        # If run with the -primary argument, skip this occurence next time.
                        self.primaryIgnoreManager.ignore(refPage)
                    return True
                elif choice in ['q', 'Q']:
                    # quit the program
                    return False
                elif choice in ['s', 'S']:
                    # Next link on this page
                    n -= 1
                    continue
                elif choice in ['x', 'X'] and edited:
                    # Save the page as is
                    break
    
                # The link looks like this:
                # [[page_title|link_text]]trailing_chars
                page_title = m.group('title')
                link_text = m.group('label')
    
                if not link_text:
                    # or like this: [[page_title]]trailing_chars
                    link_text = page_title
                if m.group('section') == None:
                    section = ''
                else:
                    section = m.group('section')
                trailing_chars = m.group('linktrail')
                if trailing_chars:
                    link_text += trailing_chars
    
                if choice in ['u', 'U']:
                    # unlink - we remove the section if there's any
                    text = text[:m.start()] + link_text + text[m.end():]
                    continue
                else:
                    if len(choice)>0 and choice[0] == 'r':
                        # we want to throw away the original link text
                        replaceit = True
                        choice = choice[1:]
                    elif include == "redirect":
                        replaceit = True
                    else:
                        replaceit = False
    
                    try:
                        choice=int(choice)
                    except ValueError:
                        wikipedia.output(u"Unknown option")
                        # step back to ask the user again what to do with the current link
                        curpos -= 1
                        continue
                    if choice >= len(self.alternatives) or choice < 0:
                        wikipedia.output(u"Choice out of range. Please select a number between 0 and %i." % (len(self.alternatives) - 1))
                        # show list of possible choices
                        self.listAlternatives()
                        # step back to ask the user again what to do with the current link
                        curpos -= 1
                        continue
                    new_page_title = self.alternatives[choice]
                    repPl = wikipedia.Page(disambPage.site(), new_page_title)
                    if (new_page_title[0].isupper()) or (link_text[0].isupper()):
                        new_page_title = repPl.title()
                    else:
                        new_page_title = repPl.title()
                        new_page_title = new_page_title[0].lower() + new_page_title[1:]
                    if replaceit and trailing_chars:
                        newlink = "[[%s%s]]%s" % (new_page_title, section, trailing_chars)
                    elif replaceit or (new_page_title == link_text and not section):
                        newlink = "[[%s]]" % new_page_title
                    # check if we can create a link with trailing characters instead of a pipelink
                    elif len(new_page_title) <= len(link_text) and firstcap(link_text[:len(new_page_title)]) == firstcap(new_page_title) and re.sub(self.trailR, '', link_text[len(new_page_title):]) == '' and not section:
                        newlink = "[[%s]]%s" % (link_text[:len(new_page_title)], link_text[len(new_page_title):])
                    else:
                        newlink = "[[%s%s|%s]]" % (new_page_title, section, link_text)
                    text = text[:m.start()] + newlink + text[m.end():]
                    continue

                wikipedia.output(text[max(0,m.start()-30):m.end()+30])
            wikipedia.output(u'\nThe following changes have been made:\n')
            wikipedia.showDiff(original_text, text)
            wikipedia.output(u'')
            # save the page
            try:
                refPage.put(text)
            except wikipedia.PageNotSaved, error:
                wikipedia.output(u'Page not saved: %s' % error)
        return True
    
    
    def run(self):
        if self.main_only:
            if not ignore_title.has_key(self.mysite.family.name):
                ignore_title[self.mysite.family.name] = {}
            if not ignore_title[self.mysite.family.name].has_key(self.mylang):
                ignore_title[self.mysite.family.name][self.mylang] = []
            ignore_title[self.mysite.family.name][self.mylang] += [
                u'%s:' % namespace for namespace in self.mysite.namespaces()]
    
        for disambPage in self.generator:
            # first check whether user has customized the edit comment
            if wikipedia.config.disambiguation_comment.has_key(self.mysite.family.name)  and wikipedia.config.disambiguation_comment[self.mysite.family.name].has_key(self.mylang):
                comment = wikipedia.translate(self.mysite,
                              wikipedia.config.disambiguation_comment[
                              self.mysite.family.name]
                              ) % disambPage.title()
            elif disambPage.isRedirectPage():
                # when working on redirects, there's another summary message
                comment = wikipedia.translate(self.mysite, msg_redir) % disambPage.title()
            else:
                comment = wikipedia.translate(self.mysite, msg) % disambPage.title()

            wikipedia.setAction(comment)
            
            self.primaryIgnoreManager = PrimaryIgnoreManager(disambPage,
                                            enabled=self.primary)
    
            if disambPage.isRedirectPage() and not self.primary:
                try:
                    target = disambPage.getRedirectTarget()
                    self.alternatives.append(target)
                except wikipedia.NoPage:
                    wikipedia.output(u"The specified page was not found.")
                    user_input = wikipedia.input(u"""\
Please enter the name of the page where the redirect should have pointed at,
or press enter to quit:""")
                    if user_input == "":
                        sys.exit(1)
                    else:
                        self.alternatives.append(user_input)
                except wikipedia.IsNotRedirectPage:
                    wikipedia.output(
                        u"The specified page is not a redirect. Skipping.")
                    continue
            elif self.getAlternatives:
                try:
                    if self.primary:
                        try:
                            disambPage2 = wikipedia.Page(self.mysite,
                                            primary_topic_format[self.mylang]
                                                % disambPage.title()
                                        )
                            thistxt = disambPage2.get(throttle=False)
                        except wikipedia.NoPage:
                            wikipedia.output(u"Page does not exist, using the first link in page %s." % disambPage.title())
                            thistxt = disambPage.linkedPages()[0].aslink()
                    else:
                        try:
                            thistxt = disambPage.get(throttle=False)
                        except wikipedia.NoPage:
                            wikipedia.output(u"Page does not exist, skipping.")
                            continue
                except wikipedia.IsRedirectPage:
                    wikipedia.output(u"Page is a redirect, skipping.")
                    continue
                thistxt = wikipedia.removeLanguageLinks(thistxt)
                thistxt = wikipedia.removeCategoryLinks(thistxt, self.mysite)
                # regular expression matching a wikilink
                w = r'([^\]\|]*)'
                Rlink = re.compile(r'\[\['+w+r'(\|'+w+r')?\]\]')
                for matchObj in Rlink.findall(thistxt):
                    self.alternatives.append(matchObj[0])
    
            self.makeAlternativesUnique()
            # sort possible choices
            self.alternatives.sort()
            self.listAlternatives()
    
            gen = ReferringPageGeneratorWithIgnore(disambPage, self.primary)
            preloadingGen = pagegenerators.PreloadingGenerator(gen)
            for refPage in preloadingGen:
                if not self.primaryIgnoreManager.isIgnored(refPage):
                    # run until the user selected 'quit'
                    if not self.treat(refPage, disambPage):
                        break
    
            # clear alternatives before working on next disambiguation page
            self.alternatives = []

def main():
    # the option that's always selected when the bot wonders what to do with
    # a link. If it's None, the user is prompted (default behaviour).
    always = None
    alternatives = []
    getAlternatives = True
    # if the -file argument is used, page titles are dumped in this array.
    # otherwise it will only contain one page.
    generator = None
    # if -file is not used, this temporary array is used to read the page title.
    pageTitle = []
    primary = False
    main_only = False

    for arg in wikipedia.handleArgs():
        if arg.startswith('-primary:'):
            primary = True
            getAlternatives = False
            alternatives.append(arg[9:])
        elif arg == '-primary':
            primary = True
        elif arg.startswith('-always:'):
            always = arg[8:]
        elif arg.startswith('-file'):
            if len(arg) == 5:
                generator = pagegenerators.TextfilePageGenerator(filename = None)
            else:
                generator = pagegenerators.TextfilePageGenerator(filename = arg[6:])
        elif arg.startswith('-pos:'):
            if arg[5]!=':':
                mysite = wikipedia.getSite()
                page = wikipedia.Page(mysite, arg[5:])
                if page.exists():
                    alternatives.append(page.title())
                else:
                    answer = wikipedia.inputChoice(u'Possibility %s does not actually exist. Use it anyway?'
                             % page.title(), ['yes', 'no'], ['y', 'N'], 'N')
                    if answer in ('Y', 'y'):
                        alternatives.append(page.title())
            else:
                alternatives.append(arg[5:])
        elif arg == '-just':
            getAlternatives = False
        elif arg == '-main':
            main_only = True
        elif arg.startswith('-start'):
            try:
                if len(arg) < 8:
                    generator = pagegenerators.CategoryPartPageGenerator(wikipedia.getSite().disambcategory())
                else:
                    generator = pagegenerators.CategoryPartPageGenerator(wikipedia.getSite().disambcategory(),arg[7:])
            except wikipedia.NoPage:
                print "Disambiguation category for your wiki is not known."
                raise
        elif arg.startswith("-"):
            print "Unrecognized command line argument: %s" % arg
            # show help text and exit
            wikipedia.showHelp()
        else:
            pageTitle.append(arg)
            
    # if the disambiguation page is given as a command line argument,
    # connect the title's parts with spaces
    if pageTitle != []:
        pageTitle = ' '.join(pageTitle)
        page = wikipedia.Page(wikipedia.getSite(), pageTitle)
        generator = iter([page])

    # if no disambiguation pages was given as an argument, and none was
    # read from a file, query the user
    if not generator:
        pageTitle = wikipedia.input(u'Which page to check:')
        page = wikipedia.Page(wikipedia.getSite(), pageTitle)
        generator = iter([page])
                
    bot = DisambiguationRobot(always, alternatives, getAlternatives, generator, primary, main_only)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
