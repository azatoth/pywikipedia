# -*- coding: utf-8 -*-
"""
Very simple script to replace a template with another one,
and to convert the old MediaWiki boilerplate format to the new template format.

Syntax: python template.py [-newformat] oldTemplate [newTemplate]

Specify the template on the command line. The program will
pick up the template page, and look for all pages using it. It will
then automatically loop over them, and replace the template.

Command line options:

-oldformat - Use the old format {{msg:Stub}} instead of {{Stub}}.

-remove    - Remove every occurence of the template from every article

-sql       - retrieve information from a local dump (http://download.wikimedia.org).
             if this argument isn\'t given, info will be loaded from the maintenance
             page of the live wiki.
             argument can also be given as "-sql:filename.sql".

other:       First argument is the old template name, second one is the new
             name. If only one argument is given, the bot resolves the
             template by putting its text directly into the article.
             This is done by changing {{...}} or {{msg:...}} into {{subst:...}}
             
             If you want to address a template which has spaces, put quotation
             marks around it.
             
Example:

If you have a template called [[Template:Cities in Washington]] and want to
change it to [[Template:Cities in Washington state]], start

    python template.py "Cities in Washington" "Cities in Washington state"

Move the page [[Template:Cities in Washington]] manually afterwards.
"""
#
# (C) Daniel Herding, 2004
# (C) Rob W.W. Hooft, 2003
#
# Distribute under the terms of the PSF license.
#
__version__='$Id$'
#
import wikipedia, config
import replace
import re, sys, string

class TemplatePageGenerator:
    def __init__(self, templateName, sqlfilename = None):
        self.templateName = templateName
        self.sqlfilename = sqlfilename
        mysite = wikipedia.getSite()
    
        # get template namespace
        ns = mysite.template_namespace(fallback = None)
        # Download 'What links here' of the template page
        self.templatePl = wikipedia.Page(mysite, ns + ':' + templateName)

    def generate(self):
        # yield all pages using the template
        if self.sqlfilename == None:
            for ref in wikipedia.getReferences(self.templatePl):
                refpl=wikipedia.Page(wikipedia.getSite(), ref)
                yield refpl
        else:
            import sqldump
            dump = sqldump.SQLdump(self.sqlfilename, mysite.encoding())
            # regular expression to find the original template.
            # {{msg:vfd}} does the same thing as {{msg:Vfd}}, so both will be found.
            # The new syntax, {{vfd}}, will also be found.
            templateR=re.compile(r'\{\{([mM][sS][gG]:)?[' + templateName[0].upper() + templateName[0].lower() + ']' + templateName[1:] + '}}')
            for entry in dump.entries():
                if templateR.search(entry.text):
                    pl = wikipedia.Page(mysite, entry.full_title())
                    yield pl

class TemplateRobot:
    # Summary messages
    msg_change={
        'en':u'Robot: Changing template: %s',
        'de':u'Bot: Ändere Vorlage: %s',
        'pt':u'Bot: Alterando predefinição: %s',
        }
    
    msg_remove={
        'en':u'Robot: Removing template: %s',
        'de':u'Bot: Entferne Vorlage: %s',
        'pt':u'Bot: Removendo predefinição: %s',
        }

    def __init__(self, generator, old, new = None, remove = False, oldFormat = False):
        self.generator = generator
        self.old = old
        self.new = new
        self.remove = remove
        self.oldFormat = oldFormat
        # if only one argument is given, don't replace the template with another
        # one, but resolve the template by putting its text directly into the
        # article.
        self.resolve = (new == None)
        # get edit summary message
        mysite = wikipedia.getSite()
        if self.remove:
            wikipedia.setAction(wikipedia.translate(mysite, self.msg_remove) % old)
        else:
            wikipedia.setAction(wikipedia.translate(mysite, self.msg_change) % old)

    def run(self):
        # regular expression to find the original template.
        # {{msg:vfd}} does the same thing as {{msg:Vfd}}, so both will be found.
        # The new syntax, {{vfd}}, will also be found.
        # The group 'sortkey' will either match a sortkey led by a pipe, or an
        # empty string.
        templateR=re.compile(r'\{\{([mM][sS][gG]:)?[' + self.old[0].upper() + self.old[0].lower() + ']' + self.old[1:] + '(?P<sortkey>\|[^}]+|)}}')
        replacements = {}
        if self.remove:
            replacements[templateR] = ''
        elif self.resolve:
            replacements[templateR] = '{{subst:' + self.old + '}}'
        elif self.oldFormat:
            replacements[templateR] = '{{msg:' + self.new + '\g<sortkey>}}'
        else:
            replacements[templateR] = '{{' + self.new + '\g<sortkey>}}'
        replaceBot = replace.ReplaceRobot(self.generator, replacements, regex = True)
        replaceBot.run()
    
def main():
    oldFormat = False
    template_names = []
    resolve = False
    remove = False
    # If sqlfilename is None, references will be loaded from the live wiki.
    sqlfilename = None
    new = None
    # read command line parameters
    for arg in sys.argv[1:]:
        arg = wikipedia.argHandler(arg)
        if arg:
            if arg == '-remove':
                remove = True
            elif arg == '-oldformat':
                oldFormat = True
            elif arg.startswith('-sql'):
                if len(arg) == 4:
                    sqlfilename = wikipedia.input(u'Please enter the SQL dump\'s filename: ')
                else:
                    sqlfilename = arg[5:]
            else:
                template_names.append(arg)

    if len(template_names) == 0 or len(template_names) > 2:
        wikipedia.output(__doc__, 'utf-8')
        wikipedia.stopme()
        sys.exit()
    old = template_names[0]
    if len(template_names) == 2:
        new = template_names[1]

    gen = TemplatePageGenerator(old, sqlfilename)
    bot = TemplateRobot(gen, old, new, remove, oldFormat)
    bot.run()

try:
    main()
finally:
    wikipedia.stopme()
