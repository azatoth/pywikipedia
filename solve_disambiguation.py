# -*- coding: cp1252 -*-
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

   -just      only use the alternatives given on the command line, do not 
              read the page for other possibilities

   -redir     if the page is a redirect page, use the page redirected to as
              the (only) alternative; if not set, the pages linked to from
              the page redirected to are used. If the page is not a redirect
              page, this will raise an error
             
   -primary   "primary topic" disambiguation (Begriffskl�rung nach Modell 2).
              That's titles where one topic is much more important, the
              disambiguation page is saved somewhere else, and the important
              topic gets the nice name.
   
   -file:XYZ  reads a list of pages, which can for example be gotten through 
              extract_names.py. XYZ is the name of the file from which the
              list is taken. If XYZ is not given, the user is asked for a
              filename.
              Page titles should be saved one per line, without [[brackets]].
              The -pos parameter won't work if -file is used.

   -always:XY instead of asking the user what to do, always perform the same
              action. For example, XY can be "r0", "u" or "2". Be careful with
              this option, and check the changes made by the bot. Note that
              some choices for XY don't make sense and will result in a loop,
              e.g. "l" or "m".

Options that are accepted by more robots:

   -lang:XX  set your home wikipedia to XX instead of the one given in
             username.dat
             
To complete a move of a page, one can use:

    python solve_disambiguation.py -just -pos:New_Name Old_Name
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Daniel Herding, 2004
#
# Distribute under the terms of the PSF license.
#
__version__='$Id$'
#
import wikipedia, config
import re,sys

# This is a purely interactive robot. We set the delays lower.
wikipedia.get_throttle.setDelay(5)
wikipedia.put_throttle.setDelay(10)

# Summary message when run without -redir parameter
msg={
    'en':'Robot-assisted disambiguation',
    'da':'Retter flertydigt link til',
    'de':'Bot-unterst\xfctzte Begriffskl\xe4rung',
    'nl':'Robot-geholpen doorverwijzing',
    'fr':'Homonymie r\xE9solue \xE0 l\'aide du robot'
    }

# Summary message when run with -redir parameter
msg_redir={
          'en':'Robot-assisted disambiguation',
          'da':'Retter flertydigt link til',
          'de':'Bot-unterst\xfctzte Redirectaufl\xf6sung',
          'nl':'Robot-geholpen doorverwijzing',
          'fr':'Correction de lien vers redirect'
          }

# disambiguation page name format for "primary topic" disambiguations
# (Begriffskl�rungen nach Modell 2)
primary_topic_format={
          'de':'%s_(Begriffskl\xe4rung)',
          'en':'%s_(disambiguation)'
          }

# letters that can follow a link and are regarded as part of this link
# This depends on the linktrail setting in LanguageXx.php.
# See http://meta.wikipedia.org/wiki/Locales_for_the_Wikipedia_Software
# to find out the setting for your Wikipedia.
# Note: this is a regular expression.
link_trail={
   'de':'[�|�|�|�|a-z]*',
   'da':'[a-z|�|�|�]*',
   'en':'[a-z]*',
   'fr':'[a-z|�|�|�|�|�|�|�|�|�]*',
   'nl':'[a-z]*'
   }
          
# List pages that will be ignored if they got a link to a disambiguation
# page. An example is a page listing disambiguations articles.
# Special chars should be encoded with unicode (\x##) and space used
# instead of _ 

ignore={
    'nl':('Wikipedia:Onderhoudspagina',
          'Wikipedia:Doorverwijspagina',
          'Wikipedia:Lijst van alle tweeletter-combinaties',
          'Gebruiker:Hooft/robot/Interwiki/lijst van problemen',
          'Wikipedia:Woorden die niet als zoekterm gebruikt kunnen worden',
          'Gebruiker:Puckly/Bijdragen',
          'Gebruiker:Waerth/bijdragen',
          "Wikipedia:Project aanmelding bij startpagina's"),
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
          'Wikipedia:Non-unique personal name',
          "User:Jerzy/Disambiguation Pages i've Editted",
          'User:Gareth Owen/inprogress',
          'TLAs from AAA to DZZ',
          'TLAs from EAA to HZZ',
          'TLAs from IAA to LZZ',
          'TLAs from MAA to PZZ',
          'TLAs from UAA to XZZ',
          'TLAs from YAA to ZZZ',
          'List of all two-letter combinations',
          'User:Daniel Quinlan/redirects1',
          'User:Daniel Quinlan/redirects2',
          'User:Daniel Quinlan/redirects3',
          'User:Daniel Quinlan/redirects4',
          'User:Daniel Quinlan/redirects5',
          'User:Daniel Quinlan/redirects6a',
          'User:Daniel Quinlan/redirects6b',
          'User:Daniel Quinlan/redirects6c',
          'User:Daniel Quinlan/redirects6d',
          'User:Daniel Quinlan/redirects6e',
          'User:Daniel Quinlan/redirects6f',
          'User:Daniel Quinlan/redirects6g',
          'User:Daniel Quinlan/redirects6h',
          'User:Daniel Quinlan/redirects6i',
          'User:Daniel Quinlan/redirects6j',
          'User:Daniel Quinlan/redirects6k',
          'User:Daniel Quinlan/redirects6l',
          'User:Daniel Quinlan/redirects6m',
          'User:Daniel Quinlan/redirects6n',
          'User:Daniel Quinlan/redirects6o',
          'User:Daniel Quinlan/redirects6p',
          'User:Oliver Pereira/stuff',
          'Wikipedia:French Wikipedia language links',
          'Wikipedia:Polish language links',
          'Wikipedia:Undisambiguated abbreviations/CIA World Factbook',
          'Wikipedia:Undisambiguated abbreviations/Country codes',
          'Wikipedia:Undisambiguated abbreviations/Currency codes',
          'Wikipedia:Undisambiguated abbreviations/Elements',
          'Wikipedia:Undisambiguated abbreviations/State codes',
          'Wikipedia:Undisambiguated abbreviations/units of measurement',
          'Wikipedia:Undisambiguated abbreviations/file extensions',
          'List of acronyms and initialisms',
          'Wikipedia:Usemod article histories',
          'User:Pizza Puzzle/stuff',
          'List of generic names of political parties',
          'Talk:List of initialisms/marked',
          'Talk:List of initialisms/sorted',
          'Talk:Programming language',
          'Talk:SAMPA/To do',
          "Wikipedia:Outline of Roget's Thesaurus",
          'User:Wik/Articles',
          'User:Egil/Sandbox',
          'Wikipedia talk:Make only links relevant to the context',
          'Wikipedia:Common words, searching for which is not possible'
          ),
    'da':('Wikipedia:Links til sider med flertydige titler'),
    'fr':('Wikip\xE9dia:Liens aux pages d\'homonymie',
          'Wikip\xE9dia:Homonymie',
          'Wikip\xE9dia:Homonymie/Homonymes dynastiques',
  'Wikip\xE9dia:Prise de d\xE9cision\x2C noms des membres de dynasties/liste des dynastiens',
  'Liste de toutes les combinaisons de deux lettres',
  'STLs de AAA \xE0 DZZ',
          'STLs de EAA \xE0 HZZ',
          'STLs de IAA \xE0 LZZ',
          'STLs de MAA \xE0 PZZ',
          'STLs de QAA \xE0 TZZ',
  'STLs de UAA \xE0 XZZ',
  'STLs de YAA \xE0 ZZZ',
  'Wikip\xE9dia\x3APages sans interwiki\x2Ca',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cb',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cc',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cd',
  'Wikip\xE9dia\x3APages sans interwiki\x2Ce',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cf',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cg',
  'Wikip\xE9dia\x3APages sans interwiki\x2Ch',
  'Wikip\xE9dia\x3APages sans interwiki\x2Ci',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cj',
  'Wikip\xE9dia\x3APages sans interwiki\x2Ck',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cl',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cm',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cn',
  'Wikip\xE9dia\x3APages sans interwiki\x2Co',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cp',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cq',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cr',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cs',
  'Wikip\xE9dia\x3APages sans interwiki\x2Ct',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cu',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cv',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cw',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cx',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cy',
  'Wikip\xE9dia\x3APages sans interwiki\x2Cz'
  ),
    'de':(
          '100 W\xf6rter des 21. Jahrhunderts',
          'Abk\xfcrzungen/A',
          'Abk\xfcrzungen/B',
          'Abk\xfcrzungen/C',
          'Abk\xfcrzungen/D',
          'Abk\xfcrzungen/E',
          'Abk\xfcrzungen/F',
          'Abk\xfcrzungen/G',
          'Abk\xfcrzungen/H',
          'Abk\xfcrzungen/I',
          'Abk\xfcrzungen/J',
          'Abk\xfcrzungen/K',
          'Abk\xfcrzungen/L',
          'Abk\xfcrzungen/M',
          'Abk\xfcrzungen/N',
          'Abk\xfcrzungen/O',
          'Abk\xfcrzungen/P',
          'Abk\xfcrzungen/Q',
          'Abk\xfcrzungen/R',
          'Abk\xfcrzungen/S',
          'Abk\xfcrzungen/T',
          'Abk\xfcrzungen/U',
          'Abk\xfcrzungen/V',
          'Abk\xfcrzungen/W',
          'Abk\xfcrzungen/X',
          'Abk\xfcrzungen/Y',
          'Abk\xfcrzungen/Z',
          'Benutzer:Katharina/Begriffskl�rungen',
          'Dreibuchstabenk�rzel von AAA bis DZZ',
          'Dreibuchstabenk�rzel von EAA bis HZZ',
          'Dreibuchstabenk�rzel von IAA bis LZZ',
          'Dreibuchstabenk�rzel von MAA bis PZZ',
          'Dreibuchstabenk�rzel von QAA bis TZZ',
          'Dreibuchstabenk�rzel von UAA bis XZZ',
          'Dreibuchstabenk�rzel von YAA bis ZZZ',
          'GISLexikon (A)',
          'GISLexikon (B)',
          'GISLexikon (C)',
          'GISLexikon (D)',
          'GISLexikon (E)',
          'GISLexikon (F)',
          'GISLexikon (G)',
          'GISLexikon (H)',
          'GISLexikon (I)',
          'GISLexikon (K)',
          'GISLexikon (L)',
          'GISLexikon (M)',
          'GISLexikon (N)',
          'GISLexikon (O)',
          'GISLexikon (P)',
          'GISLexikon (Q)',
          'GISLexikon (R)',
          'GISLexikon (S)',
          'GISLexikon (T)',
          'GISLexikon (U)',
          'GISLexikon (V)',
          'GISLexikon (W)',
          'GISLexikon (X)',
          'GISLexikon (Y)',
          'GISLexikon (Z)',
          'Lehnwort',
          'Liste aller 2-Buchstaben-Kombinationen',
          'Wikipedia:Begriffskl\xe4rung',
          'Wikipedia:Geographisch mehrdeutige Bezeichnungen',
          'Wikipedia:Liste mathematischer Themen/BKS',
          'Wikipedia:WikiProjekt Altertumswissenschaft/Orte (Systematik)',
          'Wikipedia:WikiProjekt Altertumswissenschaft/Orte',
          'Wikipedia:WikiProjekt Altertumswissenschaft/Personen (Systematik)',
          'Wikipedia:WikiProjekt Altertumswissenschaft/Personen'
      )
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

def unique(list):
    # remove duplicate entries
    result={}
    for i in list:
        result[i]=None
    return result.keys()

# the option that's always selected when the bot wonders what to do with
# a link. If it's None, the user is prompted (default behaviour).
always = None
alternatives = []
getalternatives = 1
debug = 0
solve_redirect = 0
# if the -file argument is used, page titles are dumped in this array.
# otherwise it will only contain one page.
page_list = []
# if -file is not used, this temporary array is used to read the page title.
page_title = []
primary = False

for arg in sys.argv[1:]:
    if wikipedia.argHandler(arg):
        pass
    elif arg == '-primary':
        primary = True
    elif arg.startswith('-always:'):
        always = arg[8:]
    elif arg.startswith('-file'):
        if len(arg) == 5:
            # todo: check for console encoding to allow special characters
            # in filenames, as done below with pagename
            file = raw_input('Please enter the list\'s filename: ')
        else:
            file = arg[6:]
        # open file and read page titles out of it
        f=open(file)
        for line in f.readlines():
            if line != '\n':           
                page_list.append(line)
        f.close()
    elif arg.startswith('-pos:'):
        if arg[5]!=':':
            pl=wikipedia.PageLink(wikipedia.mylang,arg[5:])
            if pl.exists():
                alternatives.append(pl.linkname())
            else:
                print "Possibility does not actually exist:",pl
                answer = raw_input('Use it anyway? [y|N] ')
                if answer in ('Y', 'y'):
                    alternatives.append(pl.linkname())
        else:
            alternatives.append(arg[5:])
    elif arg=='-just':
        getalternatives=0
    elif arg=='-redir':
        solve_redirect=1
    else:
        page_title.append(arg)

# if the disambiguation page is given as a command line argument,
# connect the title's parts with spaces
if page_title != []:
     page_title = ' '.join(page_title)
     page_list.append(page_title)

# if no disambiguation pages was given as an argument, and none was
# read from a file, query the user
if page_list == []:
    pagename = raw_input('Which page to check: ')
    pagename = unicode(pagename, config.console_encoding)
    pagename = pagename.encode(wikipedia.code2encoding(wikipedia.mylang))
    page_list.append(pagename)

if msg.has_key(wikipedia.mylang):
    msglang = wikipedia.mylang
else:
    msglang = 'en'

for wrd in (page_list):
    # when run with -redir argument, there's another summary message
    if solve_redirect:
      wikipedia.setAction(msg_redir[msglang]+': '+wrd)
    else: 
      wikipedia.setAction(msg[msglang]+': '+wrd)
    
    thispl = wikipedia.PageLink(wikipedia.mylang, wrd)
    
    if solve_redirect:
        try:
            alternatives.append(str(thispl.getRedirectTo()))
        except wikipedia.NoPage:
            print "The specified page was not found."
            user_input = raw_input("Please enter the name of the page where the redirect should have pointed at, or press enter to quit: ")
            if user_input == "":
                sys.exit(1)
            else:
                alternatives.append(user_input)
        except wikipedia.IsNotRedirectPage:
            print "The specified page is not a redirect."
            sys.exit(1)
    elif getalternatives:
        try:
            if primary:
                disamb_pl = wikipedia.PageLink(wikipedia.mylang, primary_topic_format[wikipedia.mylang] % wrd)
                thistxt = disamb_pl.get()
            else:
                thistxt = thispl.get()
        except wikipedia.IsRedirectPage,arg:
            thistxt = wikipedia.PageLink(wikipedia.mylang, str(arg)).get()
        thistxt = wikipedia.removeLanguageLinks(thistxt)
        w=r'([^\]\|]*)'
        Rlink = re.compile(r'\[\['+w+r'(\|'+w+r')?\]\]')
        for a in Rlink.findall(thistxt):
            alternatives.append(a[0])
    
    alternatives = unique(alternatives)
    # sort possible choices
    alternatives.sort()

    # print choices on screen
    for i in range(len(alternatives)):
        print "%3d" % i, repr(alternatives[i])
    
    def treat(refpl, thispl):
        try:
            reftxt=refpl.get()
        except wikipedia.IsRedirectPage:
            pass
        else:
            n = 0
            curpos = 0
            while 1:
                m=linkR.search(reftxt, pos = curpos)
                if not m:
                    if n == 0:
                        print "Not found in %s"%refpl
                    elif not debug:
                        refpl.put(reftxt)
                    return True
                # Make sure that next time around we will not find this same hit.
                curpos = m.start() + 1 
                # Try to standardize the page.
                if wikipedia.isInterwikiLink(m.group(1)):
                    linkpl = None
                else:
                    linkpl=wikipedia.PageLink(thispl.code(), m.group(1),
                                              incode = refpl.code())
                # Check whether the link found is to thispl.
                if linkpl != thispl:
                    continue
    
                n += 1
                context = 30
                while 1:
                    print '\n'
                    print "== %s =="%(refpl)
                    print wikipedia.UnicodeToAsciiHtml(reftxt[max(0,m.start()-context):m.end()+context])
                    if always == None:
                        choice=raw_input("Option (#,r#,s=skip link,n=next page,u=unlink,q=quit,\n"
                                         "        m=more context,l=list,a=add new):")
                    else:
                        choice=always
                    if choice=='n':
                        return True
                    elif choice=='s':
                        choice=-1
                        break
                    elif choice=='u':
                        choice=-2
                        break
                    elif choice=='a':
                        ns=raw_input('New alternative:')
                        alternatives.append(ns)
                    elif choice=='q':
                        return False
                    elif choice=='m':
                        context*=2
                    elif choice=='l':
                        print '\n'
                        for i in range(len(alternatives)):
                            print "%3d" % i,repr(alternatives[i])
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
                if choice==-1:
                    # Next link on this page
                    continue
                page_title = m.group(1)
                link_text = m.group(2)
                if not link_text:
                    link_text = page_title
                trailing_chars = m.group(3)
                if trailing_chars:
                    link_text += trailing_chars
                if choice==-2:
                    # unlink
                    reftxt = reftxt[:m.start()] + link_text + reftxt[m.end():]
                else:
                    # Normal replacement
                    new_page_title = alternatives[choice]
                    reppl = wikipedia.PageLink(thispl.code(), new_page_title,
                                               incode = refpl.code())
                    new_page_title = reppl.linkname()
                    # There is a function that uncapitalizes the link target's first letter
                    # if the link description starts with a small letter. This is useful on
                    # nl: but annoying on de:.
                    # At the moment the de: exclusion is only a workaround because I don't
                    # know if other languages don't want this feature either.
                    # We might want to introduce a list of languages that don't want to use
                    # this feature.
                    if wikipedia.mylang != 'de' and link_text[0] in 'abcdefghijklmnopqrstuvwxyz':
                        new_page_title = new_page_title[0].lower() + new_page_title[1:]
                    if replaceit or new_page_title == link_text:
                        reptxt = new_page_title
                    # check if we can create a link with trailing characters instead of a pipelink
                    elif len(new_page_title) <= len(link_text) and link_text[:len(new_page_title)] == new_page_title and re.sub(trailR, '', link_text[len(new_page_title):]) == '':
                        newlink = "[[%s]]%s" % (new_page_title, link_text[len(new_page_title):])
                    else:
                        newlink = "[[%s|%s]]" % (new_page_title, link_text)
                    reftxt = reftxt[:m.start()] + newlink + reftxt[m.end():]
    
                print wikipedia.UnicodeToAsciiHtml(reftxt[max(0,m.start()-30):m.end()+30])
            if not debug:
                refpl.put(reftxt)
        return True

    trailR=re.compile(link_trail[wikipedia.mylang])
    # The regular expression which finds links. Results consist of three groups:
    # group(1) is the target page title, that is, everything before | or ].
    # group(2) is the alternative link title, that's everything between | and ].
    # group(3) is the link trail, that's letters after ]] which are part of the word.
    # note that the definition of 'letter' varies from language to language.
    linkR=re.compile(r'\[\[([^\]\|]*)(?:\|([^\]]*))?\]\](' + link_trail[wikipedia.mylang] + ')')

    def resafe(s):
        s=s.replace('(','\\(')
        s=s.replace(')','\\)')
        return s
    
    active=True

    for ref in getReferences(thispl):
        refpl=wikipedia.PageLink(wikipedia.mylang, ref)
        if active:
            if not treat(refpl, thispl):
                active=False
    
    # clear alternatives before working on next disambiguation page
    alternatives = []
