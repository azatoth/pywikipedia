﻿#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This is not a complete bot; rather, it is a template from which simple
bots can be made. Change workon to edit the contents of a Wikipedia page,
save the result as mybot.py, and then just run:

python mybot.py

to have your change be done on all pages of the wiki. If that takes too
long to work in one stroke, run:

python mybot.py Pagename

to do all pages starting at pagename.

There is one standard command line option:

-debug: Don't do any changes.
"""
__version__ = '$Id$'
import wikipedia
import pagegenerators
import sys

class BasicBot:

    # Edit summary message that should be used.
    # NOTE: Put a good description here, and add translations, if possible!
    msg = {
        'de': u'Bot: Ändere ...',
        'en': u'Robot: changing ...',
    }

    def __init__(self, generator, debug):
        """
        Constructor. Parameters:
            * generator - The page generator that determines on which pages
                          to work on.
            * debug     - If True, doesn't do any real changes, but only show
                          what would have been changed.
        """
        self.generator = generator
        self.debug = debug

    def run(self):
        # Set the edit summary message
        wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), self.msg))
        for page in self.generator:
            self.treat(page)

    def treat(self, page):
        try:
            text = page.get()
        except wikipedia.NoPage:
            wikipedia.output(u"Page %s does not exist; skipping." % page.aslink())
            return
        except wikipedia.IsRedirectPage:
            wikipedia.output(u"Page %s is a redirect; skipping." % page.aslink())
            return
        except wikipedia.LockedPage:
            wikipedia.output(u"Page %s is locked; skipping." % page.aslink())
            return

        # NOTE: Here you can modify the text in whatever way you want.
        # If you find you do not want to edit this page, just return

        # Example: This puts the text 'Foobar' at the beginning of the page.
        text = 'Foobar ' + text

        # only save if something was changed
        if text != page.get():
            # Show the title of the page where the link was found.
            # Highlight the title in purple.
            colors = [None] * 6 + [13] * len(page.title()) + [None] * 4
            wikipedia.output(u"\n\n>>> %s <<<" % page.title(), colors = colors)
            # show what was changed
            wikipedia.showDiff(page.get(), text)
            if not self.debug:
                choice = wikipedia.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No'], ['y', 'N'], 'N')
                if choice == 'y':
                    try:
                        page.put(text)
                    except wikipedia.EditConflict:
                        wikipedia.output(u'Skipping %s because of edit conflict' % (page.title()))
                    except wikipedia.SpamfilterError, e:
                        wikipedia.output(u'Cannot change %s because of blacklist entry %s' % (page.title(), e.url))


def main():
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None
    # This temporary array is used to read the page title if one single
    # page to work on is specified by the arguments.
    pageTitleParts = []
    # If debug is True, doesn't do any real changes, but only show
    # what would have been changed.
    debug = False

    # Parse command line arguments
    for arg in wikipedia.handleArgs():
        if arg.startswith("-debug"):
            debug = True
        else:
            # check if a standard argument like
            # -start:XYZ or -ref:Asdf was given.
            generator = genFactory.handleArg(arg)
            if generator:
                gen = generator
            else:
                pageTitleParts.append(arg)

    if pageTitleParts != []:
        # We will only work on a single page.
        pageTitle = ' '.join(pageTitleParts)
        page = wikipedia.Page(wikipedia.getSite(), pageTitle)
        gen = iter([page])

    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = BasicBot(gen, debug)
        bot.run()
    else:
        wikipedia.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()