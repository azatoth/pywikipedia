#coding: utf-8
"""
This bot takes its input from a file that contains a number of
pages to be put on the wiki. The pages should all have the same
begin and end text (which may not overlap).

By default the text should have the intended title of the page
as the first text in bold (that is, between ''' and '''),
you can modify this behavior with command line options.

The default is not to include the begin and
end text in the page, if you want to include that text, use
the -include option.

Specific arguments:
-start:xxx      Specify the text that is the beginning of a page
-end:xxx        Specify the text that is the end of a page
-file:xxx       Give the filename we are getting our material from
-include        The beginning and end text should be included
                in the page.
-titlestart:xxx Use xxx in place of ''' for identifying the
                beginning of page title
-titleend:xxx   Use xxx in place of ''' for identifying the
                end of page title
-summary:xxx    Use xxx as the summary for the upload

If the page to be uploaded already exists:
-safe           do nothing (default)
-appendtop      add the text to the top of it
-appendbottom   add the text to the bottom of it
-force          overwrite the existing page
"""
#
# (C) Andre Engels, 2004
#
# Distributed under the terms of the MIT license.
#

__version__='$Id$'

import wikipedia, config
import re, sys, codecs

msg={
    'de': u'Automatischer Import von Artikeln',
    'en': u'Automated import of articles',
    'he': u'ייבוא ערכים אוטומטי',
    'ia': u'Importation automatic de articulos',
    'it': u'Caricamento automatico',
    'ksh': u'Automatesch aanjelaat',
    'nl': u'Geautomatiseerde import',
    'pt': u'Importação automática de artigos'
    }

# The following messages are added to topic when the page already exists
msg_top={
    'en': u'append on top',
    'he': u'הצמד בהתחלה',
    'it': u'aggiungo in cima',
    'ksh': u'Automatesch füürjesaz'
    }
msg_bottom={
    'en': u'append on bottom',
    'he': u'הצמד בסוף',
    'it': u'aggiungo in fondo',
    'ksh': u'Automatesch aanjehange'
    }
msg_force={
    'en': u'existing text overwritten',
    'he': u'הטקסט הקיים נדרס',
    'it': u'sovrascritto il testo esistente',
    'ksh': u'Automatesch ußjetuusch'
    }

# Adapt these to the file you are using. 'starttext' and 'endtext' are
# the beginning and end of each entry. Take text that should be included
# and does not occur elsewhere in the text.
# TODO: Why not use the entire file contents?
starttext = "{{-start-}}"
endtext = "{{-stop-}}"
filename = "dict.txt"
include = False
#exclude = False
titlestart = u"'''"
titleend = u"'''"
search_string = u""
force = False
append = "False"

def findpage(t):
    search_string = titlestart + "(.*?)" + titleend
    try:
        location = re.search(starttext+"([^\Z]*?)"+endtext,t)
        if include:
            contents = location.group()
        else:
            contents = location.group(1)
    except AttributeError:
        print 'Start or end marker not found.'
        return
    try:
        title = re.search(search_string, contents).group(1)
    except AttributeError:
        wikipedia.output(u"No title found - skipping a page.")
        return
    else:
        page = wikipedia.Page(mysite, title)
        wikipedia.output(page.title())
        if page.exists():
            if append == "Top":
                old_text = page.get()
                contents = contents + old_text
                commenttext_top = commenttext + " - " + wikipedia.translate(mysite,msg_top)
                wikipedia.output(u"Page %s already exists, appending on top!"%title)
                page.put(contents, comment = commenttext_top, minorEdit = False)
            elif append == "Bottom":
                old_text = page.get()
                contents = old_text + contents
                commenttext_bottom = commenttext + " - " + wikipedia.translate(mysite,msg_bottom)
                wikipedia.output(u"Page %s already exists, appending on bottom!"%title)
                page.put(contents, comment = commenttext_bottom, minorEdit = False)
            elif force:
                commenttext_force = commenttext + " *** " + wikipedia.translate(mysite,msg_force) + " ***"
                wikipedia.output(u"Page %s already exists, ***overwriting!"%title)
                page.put(contents, comment = commenttext_force, minorEdit = False)
            else:
                wikipedia.output(u"Page %s already exists, not adding!"%title)
        else:
            page.put(contents, comment = commenttext, minorEdit = False)
    findpage(t[location.end()+1:])
    return

def main():
    text = []
    f = codecs.open(filename,'r', encoding = config.textfile_encoding)
    text = f.read()
    findpage(text)

mysite = wikipedia.getSite()
commenttext = wikipedia.translate(mysite,msg)
for arg in sys.argv[1:]:
    arg = wikipedia.argHandler(arg, 'pagefromfile')
    if arg:
        if arg.startswith("-start:"):
            starttext=arg[7:]
        elif arg.startswith("-end:"):
            endtext=arg[5:]
        elif arg.startswith("-file:"):
            filename=arg[6:]
        elif arg=="-include":
            include = True
        #elif arg=="-exclude":
            #exclude = True
        elif arg=="-appendtop":
            append = "Top"
        elif arg=="-appendbottom":
            append = "Bottom"
        elif arg=="-force":
            force=True
        elif arg=="-safe":
            force=False
            append="False"
        elif arg.startswith("-titlestart:"):
            titlestart=arg[12:]
        elif arg.startswith("-titleend:"):
            titleend=arg[10:]
        elif arg.startswith("-summary:"):
            commenttext=arg[9:]
        else:
            wikipedia.output(u"Disregarding unknown argument %s."%arg)

try:
    main()
except:
    wikipedia.stopme()
    raise
else:
    wikipedia.stopme()


 	  	 
