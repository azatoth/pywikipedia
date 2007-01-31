#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This bot goes over multiple pages of the home wiki, searches for selflinks, and
allows removing them.

This script understands various command-line arguments:

    -start:        used as -start:page_name, specifies that the robot should
                   go alphabetically through all pages on the home wiki,
                   starting at the named page.

    -file:         used as -file:file_name, read a list of pages to treat
                   from the named textfile. Page titles should be enclosed
                   in [[double-squared brackets]].

    -ref:          used as -ref:page_name, specifies that the robot should
                   work on all pages referring to the named page.

    -links:        used as -links:page_name, specifies that the robot should
                   work on all pages referred to from the named page.

    -cat:          used as -cat:category_name, specifies that the robot should
                   work on all pages in the named category.

All other parameters will be regarded as a page title; in this case, the bot
will only work on a single page.
"""

__version__='$Id$'

import wikipedia, pagegenerators, catlib
import re, sys

# Summary messages in different languages
# NOTE: Predefined replacement tasks might use their own dictionary, see 'fixes'
# below.
msg = {
          'de':u'Bot: Entferne Selbstlinks',
          'he':u'רובוט: מסיר קישורים של הדף לעצמו',
          'fr':u'Bot: Enlève autoliens',
          'en':u'Robot: Removing selflinks',
          'pt':u'Bot: Retirando link para o próprio artigo'
       }    

class XmlDumpSelflinkPageGenerator:
    """
    Generator which will yield Pages that might contain selflinks.
    These pages will be retrieved from a local XML dump file
    (cur table).
    """
    def __init__(self, xmlFilename):
        """
        Arguments:
            * xmlFilename  - The dump's path, either absolute or relative
        """

        self.xmlFilename = xmlFilename

    def __iter__(self):
        import xmlreader
        mysite = wikipedia.getSite()
        dump = xmlreader.XmlDump(self.xmlFilename)
        for entry in dump.parse():
            title = re.escape(entry.title)
            if not mysite.nocapitalize:
                title = '[%s%s]%s' % (title[0].lower(), title[0].upper(), title[1:])
            selflinkR = re.compile(r'\[\[' + title + '(\|[^\]]*)?\]\]')
            if selflinkR.search(entry.text):
                yield wikipedia.Page(mysite, entry.title)
                continue

class SelflinkBot:

    def __init__(self, generator):
        self.generator = generator

    def run(self):
        linktrail = wikipedia.getSite().linktrail()
        # The regular expression which finds links. Results consist of four groups:
        # group title is the target page title, that is, everything before | or ].
        # group section is the page section. It'll include the # to make life easier for us.
        # group label is the alternative link title, that's everything between | and ].
        # group linktrail is the link trail, that's letters after ]] which are part of the word.
        # note that the definition of 'letter' varies from language to language.
        linkR = re.compile(r'\[\[(?P<title>[^\]\|#]*)(?P<section>#[^\]\|]*)?(\|(?P<label>[^\]]*))?\]\](?P<linktrail>' + linktrail + ')')
        # how many bytes should be displayed around the current link
        context = 90
        moreContext = 400
        comment = wikipedia.translate(wikipedia.getSite(), msg)
        wikipedia.setAction(comment)

        for page in self.generator:
            # Show the title of the page where the link was found.
            # Highlight the title in purple.
            colors = [None] * 6 + [13] * len(page.title()) + [None] * 4
            wikipedia.output(u"\n\n>>> %s <<<" % page.title(), colors = colors)
            try:
                oldText = page.get()
                text = oldText
                curpos = 0
                while curpos < len(text):
                    m = linkR.search(text, pos = curpos)
                    if not m:
                        break
                    # Make sure that next time around we will not find this same hit.
                    curpos = m.start() + 1
                    # ignore interwiki links and links to sections of the same page as well as section links
                    if not m.group('title') or page.site().isInterwikiLink(m.group('title')) or m.group('section'):
                        continue
                    else:
                        linkedPage = wikipedia.Page(page.site(), m.group('title'))
                    # Check whether the link found is to the current page itself.
                    if linkedPage == page:
                        # at the beginning of the link, start red color.
                        # at the end of the link, reset the color to default
                        colors = [None for c in text[max(0, m.start() - context) : m.start()]] + [12 for c in text[m.start() : m.end()]] + [None for c in text[m.end() : m.end() + context]]
                        wikipedia.output(text[max(0, m.start() - context) : m.end() + context], colors = colors)
                        choice = wikipedia.inputChoice(u'What shall be done with this selflink?',  ['unlink', 'make bold', 'skip', 'context?'], ['U', 'b', 's', '?'], 'u')
                        print
                        if choice != 's':
                            new = m.group('label') or m.group('title')
                            new += m.group('linktrail')
                            if choice == 'u':
                                text = text[:m.start()] + new + text[m.end():]
                            elif choice == '?':
                                colors = [None for c in text[max(0, m.start() - moreContext) : m.start()]] + [12 for c in text[m.start() : m.end()]] + [None for c in text[m.end() : m.end() + moreContext]]
                                wikipedia.output(text[max(0, m.start() - moreContext) : m.end() + moreContext], colors = colors)
                                choice = wikipedia.inputChoice(u'What shall be done with this selflink?',  ['unlink', 'make bold', 'skip'], ['U', 'b', 's'], 'u')
                                print
                                if choice != 's':
                                    new = m.group('label') or m.group('title')
                                    new += m.group('linktrail')
                                    if choice == 'u':
                                        text = text[:m.start()] + new + text[m.end():]
                                    else:
                                        text = text[:m.start()] + "'''" + new + "'''" + text[m.end():]
                            else:
                                text = text[:m.start()] + "'''" + new + "'''" + text[m.end():]
                if oldText == text:
                    wikipedia.output(u'No changes necessary.')
                else:
                    wikipedia.showDiff(oldText, text)
                    page.put(text)
            except wikipedia.NoPage:
                wikipedia.output(u"Page %s does not exist?!" % page.aslink())
            except wikipedia.IsRedirectPage:
                wikipedia.output(u"Page %s is a redirect; skipping." % page.aslink())
            except wikipedia.LockedPage:
                wikipedia.output(u"Page %s is locked?!" % page.aslink())

def main():
    #page generator
    gen = None
    pageTitle = []
    for arg in wikipedia.handleArgs():
        if arg.startswith('-start:'):
            gen = pagegenerators.AllpagesPageGenerator(arg[7:])
        elif arg.startswith('-ref:'):
            referredPage = wikipedia.Page(wikipedia.getSite(), arg[5:])
            gen = pagegenerators.ReferringPageGenerator(referredPage)
        elif arg.startswith('-links:'):
            linkingPage = wikipedia.Page(wikipedia.getSite(), arg[7:])
            gen = pagegenerators.LinkedPageGenerator(linkingPage)
        elif arg.startswith('-file:'):
            gen = pagegenerators.TextfilePageGenerator(arg[6:])
        elif arg.startswith('-cat:'):
            cat = catlib.Category(wikipedia.getSite(), arg[5:])
            gen = pagegenerators.CategorizedPageGenerator(cat)
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = wikipedia.input(u'Please enter the XML dump\'s filename:')
            else:
                xmlFilename = arg[5:]
            gen = XmlDumpSelflinkPageGenerator(xmlFilename)
        elif arg == '-sql':
            # NOT WORKING YET
            query = """
SELECT page_namespace, page_title
FROM page JOIN pagelinks JOIN text ON (page_id = pl_from AND page_id = old_id)
WHERE pl_title = page_title
AND pl_namespace = page_namespace
AND page_namespace = 0
AND (old_text LIKE concat('%[[', page_title, ']]%')
    OR old_text LIKE concat('%[[', page_title, '|%'))
LIMIT 100"""
            gen = pagegenerators.MySQLPageGenerator(query)
        else:
            pageTitle.append(arg)

    if pageTitle:
        page = wikipedia.Page(wikipedia.getSite(), ' '.join(pageTitle))
        gen = iter([page])
    if not gen:
        wikipedia.showHelp('selflink')
    else:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = SelflinkBot(preloadingGen)
        bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
