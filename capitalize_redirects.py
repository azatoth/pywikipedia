# -*- coding: utf-8  -*-

'''
Bot to create redirects.

Command-line arguments:

    -file          Work on all pages listed in a text file.
                   Argument can also be given as "-file:filename".

    -cat           Work on all pages which are in a specific category.
                   Argument can also be given as "-cat:categoryname".

    -ref           Work on all pages that link to a certain page.
                   Argument can also be given as "-ref:referredpagetitle".

    -links         Work on all pages that are linked from a certain page.
                   Argument can also be given as "-link:linkingpagetitle".

    -start         Work on all pages on the home wiki, starting at the named page.
                   
    -page          Work on a single page.


    -namespace     Run over especific namespace.
                   Argument can also be given as "-namespace:100".
                   
    -always        Don't prompt to make changes, just do them.


p.e.: "python capitalize_redirects.py -start:B -always"

"""


'''
#
# (C) Yrithinnd
# Class licensed under terms of the MIT license
#
__version__ = '$Id$'

import time, sys
import wikipedia, pagegenerators, catlib

msg = {
    'en': u'Robot: Create redirect to [[%s]]',
    'pt': u'Bot: Criando redirect para [[%s]]',
    }

class CapitalizeBot:
    def __init__(self, generator, acceptall):
        self.generator = generator
        self.acceptall = acceptall

    def run(self):
        for page in self.generator:
            page_t = page.title()
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            wikipedia.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % page_t)
            if not np.exists():
                wikipedia.output(u'%s don\'t exist' % np.title())
                if not self.acceptall:
                    choice = wikipedia.inputChoice(u'Do you want create redirect?',  ['Yes', 'No', 'All'], ['y', 'N', 'a'], 'N')
                    if choice in ['a', 'A']:
                        self.acceptall = True
                if self.acceptall or choice in ['y', 'Y']:
                    try:
                        wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), msg) % page_t)
                        np.put(u"#REDIRECT [[%s]]" % page_t)
                        print
                    except:
                        wikipedia.output(u"An error occured. Retrying in 15 seconds...")
                        time.sleep(15)
                        continue
            else:
                wikipedia.output(u'%s already exist, skipping...\n' % np.title())
    
def main():
    gen = None
    source = None
    textfilename = None
    categoryname = None
    pageNames = []
    referredPageName = None
    acceptall = False
    namespaces = []
    startpage = None

    for arg in wikipedia.handleArgs():
        if arg.startswith('-file'):
            if len(arg) == 5:
                textfilename = wikipedia.input(u'Please enter the filename:')
            else:
                textfilename = arg[6:]
            source = 'textfile'
        elif arg.startswith('-cat'):
            if len(arg) == 4:
                categoryname = wikipedia.input(u'Please enter the category name:')
            else:
                categoryname = arg[5:]
            source = 'category'
        elif arg.startswith('-page'):
            if len(arg) == 5:
                pageNames.append(wikipedia.input(u'Which page do you want to chage?'))
            else:
                pageNames.append(arg[6:])
            source = 'singlepage'
        elif arg.startswith('-ref'):
            if len(arg) == 4:
                referredPageName = wikipedia.input(u'Links to which page should be processed?')
            else:
                referredPageName = arg[5:]
            source = 'ref'
        elif arg.startswith('-start'):
            if len(arg) == 6:
                firstPageTitle = wikipedia.input(u'Which page do you want to chage?')
            else:
                firstPageTitle = arg[7:]
            source = 'allpages'
        elif arg == '-always':
            acceptall = True
        elif arg.startswith('-namespace:'):
            namespaces.append(int(arg[11:]))
        else:
            commandline_replacements.append(arg)
        
    if source == 'textfile':
        gen = pagegenerators.TextfilePageGenerator(textfilename)
    elif source == 'category':
        cat = catlib.Category(wikipedia.getSite(), categoryname)
        gen = pagegenerators.CategorizedPageGenerator(cat)
    elif source == 'singlepage':
        pages = [wikipedia.Page(wikipedia.getSite(), pageName) for pageName in pageNames]
        gen = iter(pages)
    elif source == 'allpages':
        namespace = wikipedia.Page(wikipedia.getSite(), firstPageTitle).namespace()
        gen = pagegenerators.AllpagesPageGenerator(firstPageTitle, namespace)
    elif source == 'ref':
        referredPage = wikipedia.Page(wikipedia.getSite(), referredPageName)
        gen = pagegenerators.ReferringPageGenerator(referredPage)
    elif source == None or len(commandline_replacements) not in [0, 2]:
        wikipedia.stopme()
        wikipedia.showHelp(u'capitalize_redirects')
        sys.exit()
    if namespaces != []:
        gen =  pagegenerators.NamespaceFilterPageGenerator(gen, namespaces)
    preloadingGen = pagegenerators.PreloadingGenerator(gen, pageNumber = 20)
    bot = CapitalizeBot(preloadingGen, acceptall)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
