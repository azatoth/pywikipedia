#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Nifty script to convert HTML-tables to MediaWiki's own syntax.


-xml           - Retrieve information from a local XML dump (pages_current, see
                 http://download.wikimedia.org).
                 Argument can also be given as "-xml:filename".
                 Searches for pages with HTML tables, and tries to convert them
                 on the live wiki.

-file:filename - Will read any [[wikipedia link]] and use these articles
                 This SQL query might be helpful to generate this file, but
                 it doesn't work for MediaWiki version 1.5 and above.
                 
                 SELECT CONCAT('[[', cur_title, ']]')
                     FROM cur
                     WHERE (cur_text LIKE '%<table%'
                         OR cur_text LIKE '%<TABLE%')
                         AND cur_title REGEXP "^[A-N]"
                         AND cur_namespace=0
                     ORDER BY cur_title
                     LIMIT 500
               
Example:

      python table2wiki.py -xml:20050713_pages_current.xml -lang:de

FEATURES
Save against missing </td>
Corrects attributes of tags

KNOWN BUGS
Broken HTML tables will most likely result in broken wiki tables!
Please check every article you change.
"""

# (C) 2003 Thomas R. Koll, <tomk32@tomk32.de>
#
# Distribute under the terms of the PSF license.
__version__='$Id$'

import re, sys, time
import wikipedia, config, pagegenerators

msg_no_warnings = {'de':'Bot: Tabellensyntax konvertiert',
                   'en':'User-controlled Bot: table syntax updated',
                   'es':'Bot controlado: actualizada sintaxis de tabla',
                   'nl':'Tabel gewijzigd van HTML- naar Wikisyntax',
                   'pt':'Bot: Sintaxe da tabela HTML para Wiki atualizada',
                  }

msg_one_warning = {'de':'Bot: Tabellensyntax konvertiert - %d Warnung!',
                   'en':'User-controlled Bot: table syntax updated - %d warning!',
                   'es':'Bot controlado: actualizada sintaxis de tabla - %d aviso!',
                   'nl':'Tabel gewijzigd van HTML- naar Wikisyntax - %d waarschuwing!',
                   'pt':'Bot: Sintaxe da tabela HTML para Wiki atualizada - %d aviso',
                  }

msg_multiple_warnings = {'de':'Bot: Tabellensyntax konvertiert - %d Warnungen!',
                         'en':'User-controlled Bot: table syntax updated - %d warnings!',
                         'es':'Bot controlado: actualizada sintaxis de tabla - %d avisos!',
                         'nl':'Tabel gewijzigd van HTML- naar Wikisyntax - %d waarschuwingen!',
                         'pt':'Bot: Sintaxe da tabela HTML para Wiki atualizada - %d avisos',
                        }

class TableXmlDumpPageGenerator:
    '''
    A page generator that will yield all pages that seem to contain an HTML
    table.
    '''
    def __init__(self, xmlfilename):
        import xmlreader
        self.xmldump = xmlreader.XmlDump(xmlfilename)

    def __iter__(self):
        tableTagR = re.compile('<table', re.IGNORECASE)
        for entry in self.xmldump.parse():
            if tableTagR.search(entry.text):
                pl = wikipedia.Page(wikipedia.getSite(), entry.title)
                yield pl
              
class Table2WikiRobot:
    def __init__(self, generator, debug = False, quietMode = False):
        self.generator = generator
        self.debug = debug
        self.quietMode = quietMode

    def convertTable(self, table):
        '''
        Converts an HTML table to wiki syntax. If the table already is a wiki
        table or contains a nested wiki table, tries to beautify it.
        Returns the converted table, the number of warnings that occured and
        a list containing these warnings.

        Hint: if you give an entire page text as a parameter instead of a table only,
        this function will convert all HTML tables and will also try to beautify all
        wiki tables already contained in the text.
        '''
        warnings = 0
        # this array will contain strings that will be shown in case of possible
        # errors, before the user is asked if he wants to accept the changes.
        warning_messages = []
        newTable = table
        ##################
        # bring every <tag> into one single line.
        num = 1
        while num != 0:
            newTable, num = re.subn("([^\r\n]{1})(<[tT]{1}[dDhHrR]{1})",
                                   r"\1\r\n\2", newTable)
            
        ##################
        # every open-tag gets a new line.
    
    
        ##################
        # <table> tag with attributes, with more text on the same line
        newTable = re.sub("(?i)[\r\n]*?<table (?P<attr>[\w\W]*?)>(?P<more>[\w\W]*?)[\r\n ]*",
                         r"\r\n{| \g<attr>\r\n\g<more>", newTable)
        # <table> tag without attributes, with more text on the same line
        newTable = re.sub("(?i)[\r\n]*?<table>(?P<more>[\w\W]*?)[\r\n ]*",
                         r"\r\n{|\n\g<more>\r\n", newTable)
        # <table> tag with attributes, without more text on the same line
        newTable = re.sub("(?i)[\r\n]*?<table (?P<attr>[\w\W]*?)>[\r\n ]*",
                         r"\r\n{| \g<attr>\r\n", newTable)
        # <table> tag without attributes, without more text on the same line
        newTable = re.sub("(?i)[\r\n]*?<table>[\r\n ]*",
                         "\r\n{|\r\n", newTable)
        # end </table>
        newTable = re.sub("(?i)[\s]*<\/table>",
                          "\r\n|}", newTable)
        
        ##################
        # caption with attributes
        newTable = re.sub("(?i)<caption (?P<attr>[\w\W]*?)>(?P<caption>[\w\W]*?)<\/caption>",
                         r"\r\n|+\g<attr> | \g<caption>", newTable)
        # caption without attributes
        newTable = re.sub("(?i)<caption>(?P<caption>[\w\W]*?)<\/caption>",
                         r"\r\n|+ \g<caption>", newTable)
        
        ##################
        # <th> often people don't write them within <tr>, be warned!
        # <th> with attributes
        newTable = re.sub("(?i)[\r\n]+<th(?P<attr>[^>]*?)>(?P<header>[\w\W]*?)<\/th>",
                         r"\r\n!\g<attr> | \g<header>\r\n", newTable)
    
        # fail save. sometimes people forget </th>
        # <th> without attributes, without closing </th>
        newTable, n = re.subn("(?i)[\r\n]+<th>(?P<header>[\w\W]*?)[\r\n]+",
                             r"\r\n! \g<header>\r\n", newTable)
        if n>0:
            warning_messages.append(u'WARNING: found <th> without </th>. (%d occurences)\n' % n)
            warnings += n
    
        # <th> with attributes, without closing </th>
        newTable, n = re.subn("(?i)[\r\n]+<th(?P<attr>[^>]*?)>(?P<header>[\w\W]*?)[\r\n]+",
                             r"\n!\g<attr> | \g<header>\r\n", newTable)
        if n>0:
            warning_messages.append(u'WARNING: found <th ...> without </th>. (%d occurences\n)' % n)
            warnings += n

    
        ##################
        # <tr> with attributes
        newTable = re.sub("(?i)[\r\n]*<tr(?P<attr>[^>]*?)>[\r\n]*",
                         r"\r\n|-----\g<attr>\r\n", newTable)
        
        # <tr> without attributes
        newTable = re.sub("(?i)[\r\n]*<tr>[\r\n]*",
                         r"\r\n|-----\r\n", newTable)
        
        ##################
        # normal <td> without arguments
        newTable = re.sub("(?i)[\r\n]+<td>(?P<cell>[\w\W]*?)<\/td>",
                         r"\r\n| \g<cell>\r\n", newTable)
    
        ##################
        # normal <td> with arguments
        newTable = re.sub("(?i)[\r\n]+<td(?P<attr>[^>]*?)>(?P<cell>[\w\W]*?)<\/td>",
                         r"\r\n|\g<attr> | \g<cell>", newTable)
    
        # WARNING: this sub might eat cells of bad HTML, but most likely it
        # will correct errors
        # TODO: some more docu please
        newTable, n = re.subn("(?i)[\r\n]+<td>(?P<cell>[^\r\n]*?)<td>",
                             r"\r\n| \g<cell>\r\n", newTable)
        if n>0:
            warning_messages.append(u'<td> used where </td> was expected. (%d occurences)\n' % n)
            warnings += n
        
        # fail save, sometimes it's a <td><td></tr>
        #        newTable, n = re.subn("[\r\n]+<(td|TD)>([^<]*?)<(td|TD)><\/(tr|TR)>",
        #                             "\r\n| \\2\r\n", newTable)
        #        newTable, n = re.subn("[\r\n]+<(td|TD)([^>]*?)>([^<]*?)<(td|TD)><\/(tr|TR)>",
        #                             "\r\n|\\2| \\3\r\n", newTable)
        # if n>0:
        #     warning_messages.append(u'WARNING: found <td><td></tr>, but no </td>. (%d occurences)\n' % n)
        #     warnings += n

        # what is this for?
        newTable, n = re.subn("[\r\n]+<(td|TD)([^>]+?)>([^\r\n]*?)<\/(td|TD)>",
                             r"\r\n|\2 | \3\r\n", newTable)
        if n>0:
            warning_messages.append(u'WARNING: (sorry, bot code unreadable (1). I don\'t know why this warning is given.) (%d occurences)\n' % n)
        
        # fail save. sometimes people forget </td>
        # <td> without arguments, with missing </td> 
        newTable, n = re.subn("(?i)<td>(?P<cell>[^<]*?)[\r\n]+",
                             r"\r\n| \g<cell>\r\n", newTable)
        if n>0:
            warning_messages.append(u'NOTE: Found <td> without </td>. This shouldn\'t cause problems.\n')
    
        # <td> with arguments, with missing </td> 
        newTable, n = re.subn("(?i)[\r\n]*<td(?P<attr>[^>]*?)>(?P<cell>[\w\W]*?)[\r\n]+",
                             r"\r\n|\g<attr> | \g<cell>\r\n", newTable)
        if n > 0:
            warning_messages.append(u'NOTE: Found <td> without </td>. This shouldn\'t cause problems.\n')
    
    
        ##################
        # Garbage collecting ;-)
        newTable = re.sub("(?i)<td>[\r\n]*<\/tr>", "", newTable)
        # delete closing tags
        newTable = re.sub("(?i)[\r\n]*<\/t[rdh]>", "", newTable)
        
        ##################
        # OK, that's only theory but works most times.
        # Most browsers assume that <th> gets a new row and we do the same
        #        newTable, n = re.subn("([\r\n]+\|\ [^\r\n]*?)([\r\n]+\!)",
        #                             "\\1\r\n|-----\\2", newTable)
        #        warnings = warnings + n
        # adds a |---- below for the case the new <tr> is missing
        #        newTable, n = re.subn("([\r\n]+\!\ [^\r\n]*?[\r\n]+)(\|\ )",
        #                             "\\1|-----\r\n\\2", newTable)
        #        warnings = warnings + n
        
        
        ##################
        # most <th> come with '''title'''. Senseless in my eyes cuz
        # <th> should be bold anyways.
        newTable = re.sub("[\r\n]+\!([^'\n\r]*)'''([^'\r\n]*)'''",
                         r"\r\n!\1\2", newTable)
        
        ##################
        # kills indention within tables. Be warned, it might seldom bring
        # bad results.
        # True by default. Set 'deIndentTables = False' in user-config.py
        if config.deIndentTables:
            num = 1
            while num != 0:
                newTable, num = re.subn("(\{\|[\w\W]*?)\n[ \t]+([\w\W]*?\|\})",
                                       r"\1\r\n\2", newTable)
                
        ##################
        # kills additional spaces after | or ! or {|
        # This line was creating problems, so I commented it out --Daniel
        # newTable = re.sub("[\r\n]+\|[\t ]+?[\r\n]+", "\r\n| ", newTable)
        # kills trailing spaces and tabs
        newTable = re.sub("\r\n(.*)[\t\ ]+[\r\n]+",
                         r"\r\n\1\r\n", newTable)
        # kill extra new-lines
        newTable = re.sub("[\r\n]{4,}(\!|\|)",
                         r"\r\n\1", newTable);
    
    
        ##################        
        # shortening if <table> had no arguments/parameters
        newTable = re.sub("[\r\n]+\{\|[\ ]+\| ", "\r\n\{| ", newTable)
        # shortening if <td> had no articles
        newTable = re.sub("[\r\n]+\|[\ ]+\| ", "\r\n| ", newTable)
        # shortening if <th> had no articles
        newTable = re.sub("\n\|\+[\ ]+\|", "\n|+ ", newTable)
        # shortening of <caption> had no articles
        newTable = re.sub("[\r\n]+\![\ ]+\| ", "\r\n! ", newTable)
        
        ##################
        # proper attributes. attribute values need to be in quotation marks.
        num = 1
        while num != 0:
            # group 1 starts with newlines, followed by a table or row tag
            # ( {| or |--- ), then zero or more attribute key - value
            # pairs where the value already has correct quotation marks, and
            # finally the key of the attribute we want to fix here.
            # group 2 is the value of the attribute we want to fix here.
            # We recognize it by searching for a string of non-whitespace characters
            # - [^\s]+? - which is not embraced by quotation marks - [^"]
            newTable, num = re.subn(r'([\r\n]+(?:\|-|\{\|)[^\r\n\|]+) *= *([^"\s>]+)',
                                   r'\1="\2"', newTable, 1)

        num = 1
        while num != 0:
            # The same for header and cell tags ( ! or | ), but for these tags the
            # attribute part is finished by a | character. We don't want to change
            # cell contents which accidentially contain an equal sign.
            # Group 1 and 2 are anologously to the previous regular expression,
            # group 3 are the remaining attribute key - value pairs.
            newTable, num = re.subn(r'([\r\n]+(?:!|\|)[^\r\n\|]+) *= *([^"\s>]+)([^\|\r\n]*)\|',
                                   r'\1="\2"\3|', newTable, 1)
           
        ##################
        # merge two short <td>s
        num = 1
        while num != 0:
            newTable, num = re.subn("[\r\n]+(\|[^\|\-\}]{1}[^\n\r]{0,35})" +
                                   "[\r\n]+(\|[^\|\-\}]{1}[^\r\n]{0,35})[\r\n]+",
                                   r"\r\n\1 |\2\r\n", newTable)
        ####
        # add a new line if first is * or #
        newTable = re.sub("[\r\n]+\| ([*#]{1})",
                         r"\r\n|\r\n\1", newTable)
        
        ##################
        # strip <center> from <th>
        newTable = re.sub("([\r\n]+\![^\r\n]+?)<center>([\w\W]+?)<\/center>",
                         r"\1 \2", newTable)
        # strip align="center" from <th> because the .css does it
        # if there are no other attributes than align, we don't need that | either
        newTable = re.sub("([\r\n]+\! +)align\=\"center\" +\|",
                         r"\1", newTable)
        # if there are other attributes, simply strip the align="center"
        newTable = re.sub("([\r\n]+\![^\r\n\|]+?)align\=\"center\"([^\n\r\|]+?\|)",
                         r"\1 \2", newTable)
        
        ##################
        # kill additional spaces within arguments
        num = 1
        while num != 0:
            newTable, num = re.subn("[\r\n]+(\||\!)([^|\r\n]*?)[ \t]{2,}([^\r\n]+?)",
                                   r"\r\n\1\2 \3", newTable)
            
        ##################
        # I hate those long lines because they make a wall of letters
        # Off by default, set 'splitLongParagraphs = True' in user-config.py
        if config.splitLongParagraphs:
            num = 1
            while num != 0:
                # TODO: how does this work? docu please.
                # why are only äöüß used, but not other special characters?
                newTable, num = re.subn("(\r\n[A-Z]{1}[^\n\r]{200,}?[a-zäöüß]\.)\ ([A-ZÄÖÜ]{1}[^\n\r]{200,})",
                                       r"\1\r\n\2", newTable)
        # show the changes for this table
        if self.debug:
            print table
            print newTable
        elif not self.quietMode:
            wikipedia.showDiff(table, newTable)
        return newTable, warnings, warning_messages

    def findTable(self, text):
        """
        Finds an HTML table (which can contain nested tables) inside a text.
        Returns the table and the start and end position inside the text.
        """
        start = text.find("<table")
        if start == -1:
            return None, 0, 0
        else:
            # depth level of table nesting
            depth = 1
            i = start + 1
            while depth > 0:
                if text.find("</table>", i) == -1:
                    print "More opening than closing table tags. Skipping."
                    return None, 0, 0
                # if another table tag is opened before one is closed
                if text.find("<table", i) > -1 and  text.find("<table", i) < text.find("</table>", i):
                    i = text.find("<table", i) + 1
                    depth += 1
                else:
                    i = text.find("</table>", i) + len("</table>") + 1
                    depth -= 1
            end = i
            return text[start:end], start, end
                        
    def convertAllHTMLTables(self, text):
        '''
        Converts all HTML tables in text to wiki syntax.
        Returns the converted text, the number of converted tables and the
        number of warnings that occured.
        '''
        convertedTables = 0
        warningSum = 0
        warningMessages = u''

        while True:
            table, start, end = self.findTable(text)
            if not table:
                # no more HTML tables left
                break
            print ">> Table %i <<" % (convertedTables + 1)
            # convert the current table
            newTable, warningsThisTable, warnMsgsThisTable = self.convertTable(table)
            print ""
            warningSum += warningsThisTable
            for msg in warnMsgsThisTable:
                warningMessages += 'In table %i: %s' % (convertedTables + 1, msg)
            text = text[:start] + newTable + text[end:]
            convertedTables += 1

        wikipedia.output(warningMessages)
            
        return text, convertedTables, warningSum

    def treat(self, pl):
        '''
        Loads a page, converts all HTML tables in its text to wiki syntax,
        and saves the converted text.
        Returns True if the converted table was successfully saved, otherwise
        returns False.
        '''
        wikipedia.output(u'\n>>> %s <<<' % pl.title())
        site = pl.site()
        try:
            text = pl.get()
        except wikipedia.NoPage:
            wikipedia.output(u"ERROR: couldn't find %s" % pl.title())
            return False
        except wikipedia.IsRedirectPage:
            wikipedia.output(u'Skipping redirect %s' % pl.title())
            return False
        newText, convertedTables, warningSum = self.convertAllHTMLTables(text)
        if convertedTables == 0:
            wikipedia.output(u"No changes were necessary.")
        else:
            if config.table2wikiAskOnlyWarnings and warningSum == 0:
                doUpload = True
            else:
                if config.table2wikiSkipWarnings:
                    doUpload = True
                else:
                    print "There were %i replacement(s) that might lead to bad output." % warningSum
                    doUpload = (wikipedia.input(u'Do you want to change the page anyway? [y|N]') == "y")
            if doUpload:
                # get edit summary message
                if warningSum == 0:
                    wikipedia.setAction(wikipedia.translate(site.lang, msg_no_warnings))
                elif warningSum == 1:
                    wikipedia.setAction(wikipedia.translate(site.lang, msg_one_warning) % warningSum)
                else:
                    wikipedia.setAction(wikipedia.translate(site.lang, msg_multiple_warnings) % warningSum)
                pl.put(newText)

    def run(self):
        for pl in self.generator:
            self.treat(pl)
            
def main():
    quietMode = False # use -quiet to get less output
    # if the -file argument is used, page titles are stored in this array.
    # otherwise it will only contain one page.
    articles = []
    # if -file is not used, this temporary array is used to read the page title.
    page_title = []
    debug = False
    source = None
    for arg in sys.argv[1:]:
        arg = wikipedia.argHandler(arg, 'table2wiki')
        if arg:
            if arg.startswith('-file:'):
                f=open(arg[6:], 'r')
                R=re.compile(r'.*\[\[([^\]]*)\]\].*')
                m = False
                for line in f.readlines():
                    m=R.match(line)            
                    if m:
                        articles.append(m.group(1))
                    else:
                        print "ERROR: Did not understand %s line:\n%s" % (
                            arg[6:], repr(line))
                f.close()
            elif arg.startswith('-xml'):
                if len(arg) == 4:
                    xmlfilename = wikipedia.input(u'Please enter the XML dump\'s filename: ')
                else:
                    xmlfilename = arg[5:]
                source = 'xmldump'
            elif arg.startswith('-skip:'):
                articles = articles[articles.index(arg[6:]):]
            elif arg.startswith('-auto'):
                config.table2wikiAskOnlyWarnings = True
                config.table2wikiSkipWarnings = True
                print "Automatic mode!\n"
            elif arg.startswith('-quiet'):
                quietMode = True
            elif arg.startswith('-debug'):
                debug = True
            else:
                page_title.append(arg)

    if source == 'xmldump':
        gen = pagegenerators.PreloadingGenerator(TableXmlDumpPageGenerator(xmlfilename))
    # if the page is given as a command line argument,
    # connect the title's parts with spaces
    elif page_title != []:
        page_title = ' '.join(page_title)
        page = wikipedia.Page(wikipedia.getSite(), page_title)
        gen = pagegenerators.PreloadingGenerator(iter([page]))
    else:
        # show help
        wikipedia.output(__doc__, 'utf-8')
        sys.exit(0)

    bot = Table2WikiRobot(gen, debug, quietMode)
    bot.run()
            
try:
    main()
except:
    wikipedia.stopme()
    raise
else:
    wikipedia.stopme()
