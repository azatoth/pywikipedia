#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This is a Bot written by Filnik to add a text in a given category.

--- GenFactory Generator is used ---
-start              Define from which page should the Bot start
-ref                Use the ref as generator
-cat                Use a category as generator
-filelinks          Use all the links to an image as generator
-unusedfiles
-unwatched
-withoutinterwiki
-interwiki
-file
-uncatfiles
-uncatcat
-uncat
-subcat
-transcludes        Use all the page that transclude a certain page as generator
-weblink            Use the pages with a certain web link as generator
-links              Use the links from a certain page as generator
-regex              Only work on pages whose titles match the given regex

--- Other parameters ---
-page               Use a page as generator
-text               Define which text add
-summary            Define the summary to use
-except             Use a regex to understand if the template is already in the page
-excepturl          Use the html page as text where you want to see if there's the text, not the wiki-page.
-newimages          Add text in the new images
-untagged           Add text in the images that doesn't have any license template
-always             If used, the bot won't asked if it should add the text specified
-up                 If used, put the text above and not below

--- Example ---

python add_text.py -start:! -summary:"Bot: Adding a template" -text:"{{Something}}" -except:"\{\{(?:[Tt]emplate:|)[Ss]omething" -up

# Command used on it.wikipedia to put the template in the page without any category.
python add_text.py -excepturl:"<p class='catlinks'>" -uncat -text:"{{Categorizzare}}"
-except:"\{\{(?:[Tt]emplate:|)[Cc]ategorizzare" -summary:"Bot: Aggiungo template Categorizzare"

--- Credits and Help ---
This script has been written by Botwiki's stuff, if you want to help us
or you need some help regarding this script, you can find us here:

* http://botwiki.sno.cc

"""

#
# (C) Filnik, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: AddText.py,v 1.0 2007/11/27 17:08:30 filnik Exp$'
#

import re, pagegenerators, urllib2, urllib
import wikipedia, catlib

msg = {
    'en': u'Bot: Adding %s',
    'pt': u'Bot: Adicionando %s',
    }

class NoEnoughData(wikipedia.Error):
    """ Error class for when the user doesn't specified all the data needed """

class NothingFound(wikipedia.Error):
	""" An exception indicating that a regex has return [] instead of results."""

# Useful for the untagged function
def pageText(url):
    """ Function to load HTML text of a URL """
    try:
        request = urllib2.Request(url)
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7'
        request.add_header("User-Agent", user_agent)
        response = urllib2.urlopen(request)
        text = response.read()
        response.close()
        # When you load to many users, urllib2 can give this error.
    except urllib2.HTTPError:
        wikipedia.output(u"Server error. Pausing for 10 seconds... " + time.strftime("%d %b %Y %H:%M:%S (UTC)", time.gmtime()) )
        time.sleep(10)
        request = urllib2.Request(url)
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7'
        request.add_header("User-Agent", user_agent)
        response = urllib2.urlopen(request)
        text = response.read()
        response.close()
    return text

def untaggedGenerator(untaggedProject, limit = 500):
    """ Function to get the pages returned by this tool: http://tools.wikimedia.de/~daniel/WikiSense/UntaggedImages.php """
    lang = untaggedProject.split('.', 1)[0]
    project = '.' + untaggedProject.split('.', 1)[1]
    if lang == 'commons':
        link = 'http://tools.wikimedia.de/~daniel/WikiSense/UntaggedImages.php?wikifam=commons.wikimedia.org&since=-100d&until=&img_user_text=&order=img_timestamp&max=100&order=img_timestamp&format=html'
    else:
        link = 'http://tools.wikimedia.de/~daniel/WikiSense/UntaggedImages.php?wikilang=' + lang + '&wikifam=' + project + '&order=img_timestamp&max=' + str(limit) + '&ofs=0&max=' + str(limit)         
    text = pageText(link)
    #print text
    regexp = r"""<td valign='top' title='Name'><a href='http://.*?\.org/w/index\.php\?title=(.*?)'>.*?</a></td>"""
    results = re.findall(regexp, text)
    if results == []:
        print link
        raise NothingFound('Nothing found! Try to use the tool by yourself to be sure that it works!')
    else:
        for result in results:
            yield wikipedia.Page(self.site, result)

def add_text(generator = None, addText = None, summary = None, regexSkip = None, regexSkipUrl = None,
             always = False, exceptUrl = False, up = False):
    # When a page is tagged as "really well written" it has a star in the interwiki links.
    # This is a list of all the templates used (in regex format) to make the stars appear.
    starsList = ['link[ _]fa', 'link[ _]adq', 'enllaç[ _]ad',
                 'link[ _]ua', 'legătură[ _]af', 'destacado',
                 'ua', 'liên k[ _]t[ _]chọn[ _]lọc']

    errorCount = 0
    site = wikipedia.getSite()
    # /wiki/ is not always the right path in non-wiki projects
    pathWiki = site.family.nicepath(site.lang)
    # Check if there are the minimal settings
    if not generator:
        raise NoEnoughData('You have to specify the generator you want to use for the script!')
    if not addText:
        raise NoEnoughData('You have to specify what text you want to add!')
    if not summary:
        summary = wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), msg) % addText)

    # Main Loop
    for page in generator:
        wikipedia.output(u'Loading %s...' % page.title())
        try:
            text = page.get()
        except wikipedia.NoPage:
            wikipedia.output(u"%s doesn't exist, skip!" % page.title())
            continue
        except wikipedia.IsRedirectPage:
            wikipedia.output(u"%s is a redirect, skip!" % page.title())
            continue
        # Understand if the bot has to skip the page or not
        # In this way you can use both -except and -excepturl
        if regexSkipUrl != None:          
            url = '%s%s' % (pathWiki, page.urlname())
            result = re.findall(regexSkipUrl, site.getUrl(url))
            if result != []:
                wikipedia.output(u'Exception! regex (or word) used with -exceptUrl is in the page. Skip!')
                continue            
        if regexSkip != None:
            result = re.findall(regexSkip, text)
            if result != []:
                wikipedia.output(u'Exception! regex (or word) used with -except is in the page. Skip!')
                continue
        # If not up, text put below
        if not up:
            newtext = text
            categoryNamespace = site.namespace(14)
            # Getting the categories
            regexpCat = re.compile(r'\[\[((?:category|%s):.*?)\]\]' % categoryNamespace.lower(), re.I)
            categorieInside = regexpCat.findall(text)
            # Deleting the categories
            newtext = wikipedia.removeCategoryLinks(newtext, site)
            # Getting the interwiki
            interwikiInside = page.interwiki()
            interwikiList = list()
            for paginetta in interwikiInside:
                nome = str(paginetta).split('[[')[1].split(']]')[0]
                interwikiList.append(nome)
                lang = nome.split(':')[0]
            # Removing the interwiki
            newtext = wikipedia.removeLanguageLinks(newtext, site)
            # Sorting the interwiki
            interwikiList.sort()
            newtext += "\n%s" % addText
            # Reputting the categories
            for paginetta in categorieInside:
                try:
                    newtext += '\n[[%s]]' % paginetta.decode('utf-8')
                except UnicodeEncodeError:
                    try:
                        newtext += '\n[[%s]]' % paginetta.decode('Latin-1')
                    except UnicodeEncodeError:
                        newtext += '\n[[%s]]' % paginetta
            newtext += '\n'
            # Dealing the stars' issue
            starsListInPage = list()
            for star in starsList:
                regex = re.compile('(\{\{(?:template:|)%s\|.*?\}\}\n)' % star, re.I)
                risultato = regex.findall(newtext)
                if risultato != []:
                    newtext = regex.sub('', newtext)
                    for element in risultato:
                        newtext += '\n%s' % element
            # Adding the interwiki
            for paginetta in interwikiList:
                try:
                    newtext += '\n[[%s]]' % paginetta.decode('utf-8')
                except UnicodeEncodeError:
                    try:
                        newtext += '\n[[%s]]' % paginetta.decode('Latin-1')
                    except UnicodeEncodeError:
                        newtext += '\n[[%s]]' % paginetta
        # If instead the text must be added above...
        else:
            newtext = addText + '\n' + text
        wikipedia.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % page.title())
        wikipedia.showDiff(text, newtext)
        choice = ''
        # Let's put the changes.
        while 1:
            if not always:
                choice = wikipedia.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No', 'All'], ['y', 'N', 'a'], 'N')
            if choice.lower() in ['a', 'all']:
                always = True
            if choice.lower() in ['n', 'no']:
                break
            if choice.lower() in ['y', 'yes'] or always:
                try:
                    page.put(newtext, summary)
                except wikipedia.EditConflict:
                    wikipedia.output(u'Edit conflict! skip!')
                    break
                except wikipedia.ServerError:
                    errorCount += 1
                    if errorCount < 5:
                        wikipedia.output(u'Server Error! Wait..')
                        time.sleep(3)
                        continue
                    else:
                        raise wikipedia.ServerError(u'Fifth Server Error!')
                except wikipedia.SpamfilterError, e:
                    wikipedia.output(u'Cannot change %s because of blacklist entry %s' % (page.title(), e.url))
                    break
                except wikipedia.PageNotSaved, error:
                    wikipedia.output(u'Error putting page: %s' % (error.args,))
                    break
                except wikipedia.LockedPage:
                    wikipedia.output(u'Skipping %s (locked page)' % (page.title(),))
                    break
                else:
                    # Break only if the errors are one after the other...
                    errorCount = 0
                    break
def main():
    # If none, the var is setted only for check purpose.
    summary = None; addText = None; regexSkip = None; regexSkipUrl = None;
    generator = None; always = False; exceptUrl = False
    # Load a lot of default generators
    genFactory = pagegenerators.GeneratorFactory()
    # Put the text above or below the text?
    up = False
    # Loading the arguments
    for arg in wikipedia.handleArgs():
        if arg.startswith('-text'):
            if len(arg) == 5:
                addText = wikipedia.input(u'What text do you want to add?')
            else:
                addText = arg[6:]
        elif arg.startswith('-summary'):
            if len(arg) == 8:
                summary = wikipedia.input(u'What summary do you want to use?')
            else:
                summary = arg[9:]
        elif arg.startswith('-page'):
            if len(arg) == 5:
                generator = [wikipedia.Page(wikipedia.getSite(), wikipedia.input(u'What page do you want to use?'))]
            else:
                generator = [wikipedia.Page(wikipedia.getSite(), arg[6:])]
        elif arg.startswith('-excepturl'):
            if len(arg) == 10:
                regexSkipUrl = wikipedia.input(u'What text should I skip?')
            else:
                regexSkipUrl = arg[11:]
        elif arg.startswith('-except'):
            if len(arg) == 7:
                regexSkip = wikipedia.input(u'What text should I skip?')
            else:
                regexSkip = arg[8:]
        elif arg.startswith('-untagged'):
            if len(arg) == 9:
                untaggedProject = wikipedia.input(u'What project do you want to use?')
            else:
                untaggedProject = arg[10:]
            generator = untaggedGenerator(untaggedProject)
        elif arg == '-up':
            up = True
        elif arg == '-always':
            always = True
        else:
            generator = genFactory.handleArg(arg)
    add_text(generator, addText, summary, regexSkip, regexSkipUrl, always, exceptUrl, up)
    
if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
