﻿# -*- coding: utf-8  -*-
"""
This bot will make direct text replacements. It will retrieve information on
which pages might need changes either from an SQL dump or a text file, or only
change a single page.

You can run the bot with the following commandline parameters:

-sql         - Retrieve information from a local SQL dump (cur table, see
               http://download.wikimedia.org).
               Argument can also be given as "-sql:filename".
-file        - Retrieve information from a local text file.
               Will read any [[wiki link]] and use these articles.
               Argument can also be given as "-file:filename".
-page        - Only edit a single page.
               Argument can also be given as "-page:pagename". You can give this
               parameter multiple times to edit multiple pages.
-regex       - Make replacements using regular expressions. If this argument
               isn't given, the bot will make simple text replacements.
-except:XYZ  - Ignore pages which contain XYZ. If the -regex argument is given,
               XYZ will be regarded as a regular expression.
-fix:XYZ     - Perform one of the predefined replacements tasks, which are given
               in the dictionary 'fixes' defined inside this file.
               The -regex argument and given replacements will be ignored if
               you use -fix.
               Currently available predefined fixes are:
                   * HTML - convert HTML tags to wiki syntax, and fix XHTML
-namespace:n - Namespace to process. Works only with a sql dump
-always      - Don't prompt you for each replacement
other:       - First argument is the old text, second argument is the new text.
               If the -regex argument is given, the first argument will be
               regarded as a regular expression, and the second argument might
               contain expressions like \\1 or \g<name>.
      
NOTE: Only use either -sql or -file or -page, but don't mix them.

Examples:

If you want to change templates from the old syntax, e.g. {{msg:Stub}}, to the
new syntax, e.g. {{Stub}}, download an SQL dump file (cur table) from
http://download.wikimedia.org, then use this command:

    python replace.py -sql -regex "{{msg:(.*?)}}" "{{\\1}}"

If you have a dump called foobar.sql and want to fix typos, e.g.
Errror -> Error, use this:

    python replace.py -sql:foobar.sql "Errror" "Error"

If you have a page called 'John Doe' and want to convert HTML tags to wiki
syntax, use:
    
    python replace.py -page:John_Doe -fix:HTML
"""
#
# (C) Daniel Herding, 2004
#
# Distributed under the terms of the PSF license.
#

from __future__ import generators
import sys, re
import wikipedia, config

# Summary messages in different languages
# NOTE: Predefined replacement tasks might use their own dictionary, see 'fixes'
# below.
msg = {
       'de':u'Bot: Automatisierte Textersetzung %s',
       'en':u'Robot: Automated text replacement %s',
       'es':u'Robot: Reemplazo automático de texto %s',
       'fr':u'Bot : Remplacement de texte automatisé %s',
       'hu':u'Robot: Automatikus szövegcsere %s',
       }

# Predefined replacements tasks.
fixes = {
    'cat': {
        'regex': True,
        'msg': {
            'de':u'Bot: entferne Grundkategorien'
            },
        'replacements': {
            r'\[\[Kategorie:Zeit:.+?\]\][\r\n ]*': '',
            r'\[\[Kategorie:Raum:.+?\]\][\r\n ]*': '',
            r'\[\[Kategorie:Thema:.+?\]\][\r\n ]*': '',
            r'\[\[Kategorie:Typ:.+?\]\][\r\n ]*': '',
        }
    },
            
    # These replacements will convert HTML to wiki syntax where possible, and
    # make remaining tags XHTML compliant.
    'HTML': {
        'regex': True,
        # We don't want to mess up pages which discuss HTML tags, so we skip
        # all pages which contain nowiki tags.
        'exceptions':  ['<nowiki>'],
        'msg': {
               'en':u'Robot: converting/fixing HTML',
               'de':u'Bot: konvertiere/korrigiere HTML',
              },
        'replacements': {
            # Everything case-insensitive (?i)
            # Keep in mind that MediaWiki automatically converts <br> to <br />
            # when rendering pages, so you might comment the next two lines out
            # to save some time/edits.
            #r'(?i)<br>':                      r'<br />',
            # linebreak with attributes
            #r'(?i)<br ([^>/]+?)>':            r'<br \1 />',
            r'(?i)<b>(.*?)</b>':              r"'''\1'''",
            r'(?i)<strong>(.*?)</strong>':    r"'''\1'''",
            r'(?i)<i>(.*?)</i>':              r"''\1''",
            r'(?i)<em>(.*?)</em>':            r"''\1''",
            # horizontal line without attributes in a single line
            r'(?i)([\r\n])<hr[ /]*>([\r\n])': r'\1----\2',
            # horizontal line without attributes with more text in the same line
            r'(?i) +<hr[ /]*> +':             r'\r\n----\r\n',
            # horizontal line with attributes; can't be done with wiki syntax
            # so we only make it XHTML compliant
            r'(?i)<hr ([^>/]+?)>':            r'<hr \1 />',
            # a header where only spaces are in the same line
            r'(?i)([\r\n]) *<h1> *([^<]+?) *</h1> *([\r\n])':  r"\1= \2 =\3",
            r'(?i)([\r\n]) *<h2> *([^<]+?) *</h2> *([\r\n])':  r"\1== \2 ==\3",
            r'(?i)([\r\n]) *<h3> *([^<]+?) *</h3> *([\r\n])':  r"\1=== \2 ===\3",
            r'(?i)([\r\n]) *<h4> *([^<]+?) *</h4> *([\r\n])':  r"\1==== \2 ====\3",
            r'(?i)([\r\n]) *<h5> *([^<]+?) *</h5> *([\r\n])':  r"\1===== \2 =====\3",
            r'(?i)([\r\n]) *<h6> *([^<]+?) *</h6> *([\r\n])':  r"\1====== \2 ======\3",
            # TODO: maybe we can make the bot replace <p> tags with \r\n's.
        }
    },
    # Grammar fixes for German language
    'grammar-de': {
        'regex': True,
        'exceptions':  ['sic!'],
        'msg': {
               'de':u'Bot: korrigiere Grammatik',
              },
        'replacements': {
            u'([Ss]owohl) ([^,\.]+?), als auch':              r'\1 \2 als auch',
            #u'([Ww]eder) ([^,\.]+?), noch':                   r'\1 \2 noch',
            u'(?=\W)(\d[\d\.\,]*\d|\d)($|€|DM|mg|g|kg|l|t|ms|s|min|h|µm|mm|cm|dm|m|km|°C|K|kB|MB|TB)(?=\W)': r'\1 \2',
            u'(\d+)\.(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)':   r'\1. \2',
        }
    },
    
}

def read_pages_from_sql_dump(sqlfilename, replacements, exceptions, regex, namespace):
    '''
    Generator which will yield PageLinks to pages that might contain text to
    replace. These pages will be retrieved from a local sql dump file
    (cur table).

    Arguments:
        * sqlfilename  - the dump's path, either absolute or relative
        * replacements - a dictionary where old texts are keys and new texts
                         are values
        * exceptions   - a list of strings; pages which contain one of these
                         won't be changed.
        * regex        - if the entries of replacements and exceptions should
                         be interpreted as regular expressions
    '''
    import sqldump
    dump = sqldump.SQLdump(sqlfilename, wikipedia.myencoding())
    for entry in dump.entries():
        skip_page = False
        if namespace != -1 and namespace != entry.namespace:
            continue
        else:
            for exception in exceptions:
                if regex:
                    exception = re.compile(exception)
                    if exception.search(entry.text):
                        skip_page = True
                        break
                else:
                    if entry.text.find(exception) != -1:
                        skip_page = True
                        break
        if not skip_page:
            for old in replacements.keys():
                if regex:
                    old = re.compile(old)
                    if old.search(entry.text):
                        yield wikipedia.PageLink(wikipedia.mylang, entry.full_title())
                        break
                else:
                    if entry.text.find(old) != -1:
                        yield wikipedia.PageLink(wikipedia.mylang, entry.full_title())
                        break

def read_pages_from_text_file(textfilename):
    '''
    Generator which will yield pages that are listed in a text file created by
    the bot operator. Will regard everything inside [[double brackets]] as a
    page name, and yield PageLinks for these pages.

    Arguments:
        * textfilename - the textfile's path, either absolute or relative
    '''
    f = open(textfilename, 'r')
    # regular expression which will find [[wiki links]]
    R = re.compile(r'.*\[\[([^\]]*)\]\].*')
    m = False
    for line in f.readlines():
        # BUG: this will only find one link per line.
        # TODO: use findall() instead.
        m=R.match(line)
        if m:
            yield wikipedia.PageLink(wikipedia.mylang, m.group(1))
    f.close()

# TODO: Make MediaWiki's search feature available.
def generator(source, replacements, exceptions, regex, namespace, textfilename = None, sqlfilename = None, pagenames = None):
    '''
    Generator which will yield PageLinks for pages that might contain text to
    replace. These pages might be retrieved from a local SQL dump file or a
    text file, or as a list of pages entered by the user.

    Arguments:
        * source       - where the bot should retrieve the page list from.
                         can be 'sqldump', 'textfile' or 'userinput'.
        * replacements - a dictionary where keys are original texts and values
                         are replacement texts.
        * exceptions   - a list of strings; pages which contain one of these
                         won't be changed.
        * regex        - if the entries of replacements and exceptions should
                         be interpreted as regular expressions
        * namespace    - namespace to process in case of a SQL dump
        * textfilename - the textfile's path, either absolute or relative, which
                         will be used when source is 'textfile'.
        * sqlfilename  - the dump's path, either absolute or relative, which
                         will be used when source is 'sqldump'.
        * pagenames    - a list of pages which will be used when source is
                         'userinput'.
    '''
    if source == 'sqldump':
        for pl in read_pages_from_sql_dump(sqlfilename, replacements, exceptions, regex, namespace):
            yield pl
    elif source == 'textfile':
        for pl in read_pages_from_text_file(textfilename):
            yield pl
    elif source == 'userinput':
        for pagename in pagenames:
            yield wikipedia.PageLink(wikipedia.mylang, pagename)

# How we want to retrieve information on which pages need to be changed.
# Can either be 'sqldump', 'textfile' or 'userinput'.
source = None
# Array which will collect commandline parameters.
# First element is original text, second element is replacement text.
commandline_replacements = []
# A dictionary where keys are original texts and values are replacement texts.
replacements = {}
# Don't edit pages which contain certain texts.
exceptions = []
# Should the elements of 'replacements' and 'exceptions' be interpreted
# as regular expressions?
regex = False
# Predefined fixes from dictionary 'fixes' (see above).
fix = None
# the dump's path, either absolute or relative, which will be used when source
# is 'sqldump'.
sqlfilename = ''
# the textfile's path, either absolute or relative, which will be used when
# source is 'textfile'.
textfilename = ''
# a list of pages which will be used when source is 'userinput'.
pagenames = []
# will become True when the user presses a ('yes to all') or uses the -always
# commandline paramater.
acceptall = False
# Which namespace should be processed when using a SQL dump
# default to -1 which means all namespaces will be processed
namespace = -1
# Load default summary message.
wikipedia.setAction(wikipedia.translate(wikipedia.mylang, msg))

# Read commandline parameters.
for arg in sys.argv[1:]:
    arg = wikipedia.argHandler(arg)
    if arg:
        if arg == '-regex':
            regex = True
        elif arg.startswith('-file'):
            if len(arg) == 5:
                textfilename = wikipedia.input(u'Please enter the filename:')
            else:
                textfilename = arg[6:]
            source = 'textfile'
        elif arg.startswith('-sql'):
            if len(arg) == 4:
                sqlfilename = wikipedia.input(u'Please enter the SQL dump\'s filename:')
            else:
                sqlfilename = arg[5:]
            source = 'sqldump'
        elif arg.startswith('-page'):
            if len(arg) == 5:
                pagenames.append(wikipedia.input(u'Which page do you want to chage?'))
            else:
                pagenames.append(arg[6:])
            source = 'userinput'
        elif arg.startswith('-except:'):
            exceptions.append(arg[8:])
        elif arg.startswith('-fix:'):
            fix = arg[5:]
        elif arg == '-always':
            acceptall = True
        elif arg.startswith('-namespace:'):
            namespace = int(arg[11:])
        else:
            commandline_replacements.append(arg)

if source == None or len(commandline_replacements) not in [0, 2]:
    # syntax error, show help text from the top of this file
    wikipedia.output(__doc__, 'utf-8')
    sys.exit()
if (len(commandline_replacements) == 2 and fix == None):
    replacements[commandline_replacements[0]] = commandline_replacements[1]
    wikipedia.setAction(wikipedia.translate(wikipedia.mylang, msg )+ ' (-' + commandline_replacements[0] + ' +' + commandline_replacements[1] + ')')
elif fix == None:
    old = wikipedia.input(u'Please enter the text that should be replaced:')
    new = wikipedia.input(u'Please enter the new text:')
    change = '(-' + old + ' +' + new
    replacements[old] = new
    while True:
        old = wikipedia.input(u'Please enter another text that should be replaced, or press Enter to start:')
        if old == '':
            change = change + ')'
            break
        new = wikipedia.input(u'Please enter the new text:')
        change = change + ' & -' + old + ' +' + new
        replacements[old] = new
    default_summary_message =  wikipedia.translate(wikipedia.mylang, msg) % change
    wikipedia.output(u'The summary message will default to: %s' % default_summary_message)
    summary_message = wikipedia.input(u'Press Enter to use this default message, or enter a description of the changes your bot will make:')
    if summary_message == '':
        summary_message = default_summary_message
    wikipedia.setAction(summary_message)
else:
    # Perform one of the predefined actions.
    try:
        fix = fixes[fix]
    except KeyError:
        wikipedia.output(u'Available predefined fixes are: %s' % fixes.keys())
        sys.exit()
    if fix.has_key('regex'):
        regex = fix['regex']
    if fix.has_key('msg'):
        wikipedia.setAction(wikipedia.translate(wikipedia.mylang, fix['msg']))
    if fix.has_key('exceptions'):
        exceptions = fix['exceptions']
    replacements = fix['replacements']

# Run the generator which will yield PageLinks to pages which might need to be
# changed.
for pl in generator(source, replacements, exceptions, regex, namespace, textfilename, sqlfilename, pagenames):
    print ''
    try:
        # Load the page's text from the wiki
        original_text = pl.get()
    except wikipedia.NoPage:
        wikipedia.output(u'Page %s not found' % pl.linkname())
        continue
    except wikipedia.LockedPage:
        wikipedia.output(u'Skipping locked page %s' % pl.linkname())
        continue
    except wikipedia.IsRedirectPage:
        continue
    
    skip_page = False
    # skip all pages that contain certain texts
    for exception in exceptions:
        if regex:
            exception = re.compile(exception)
            hit = exception.search(original_text)
            if hit:
                wikipedia.output(u'Skipping %s because it contains %s' % (pl.linkname(), hit.group(0)))
                # Does anyone know how to break out of the _outer_ loop?
                # Then we wouldn't need the skip_page variable.
                skip_page = True
                break
        else:
            hit = original_text.find(exception)
            if hit != -1:
                wikipedia.output(u'Skipping %s because it contains %s' % (pl.linkname(), original_text[hit:hit + len(exception)]))
                skip_page = True
                break
    if not skip_page:
        # create a copy of the original text to work on, so we can later compare
        # if any changes were made
        new_text = original_text
        for old, new in replacements.items():
            if regex:
                # TODO: compiling the regex each time might be inefficient
                old = re.compile(old)
                new_text = old.sub(new, new_text)
            else:
                new_text = new_text.replace(old, new)
        if new_text == original_text:
            try:
                # Sometime the bot crashes when it can't decode a character.
                # Let's not let it crash
                print 'No changes were necessary in %s' % pl.linkname()
            except UnicodeEncodeError:
                print 'Error decoding pl.linkname()'
                continue
        else:
            wikipedia.showDiff(original_text, new_text)
            if not acceptall:
                choice = wikipedia.input(u'Do you want to accept these changes? [y|n|a(ll)]')
                if choice in ['a', 'A']:
                    acceptall = True
            if acceptall or choice in ['y', 'Y']:
                pl.put(new_text)
