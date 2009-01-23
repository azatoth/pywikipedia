# -*- coding: utf-8 -*-
"""
Program to (re)categorize images at commons.

The program uses commonshelper for category suggestions.
It takes the suggestions and the current categories. Put the categories through some filters and add the result

"""
__version__ = '$Id$'
#
#  (C) Multichill 2008
#  (tkinter part loosely based on imagecopy.py)
# Distributed under the terms of the MIT license.
#
#
import os, sys, re, codecs
import urllib, httplib, urllib2
import catlib
import time
import wikipedia, config
import pagegenerators, StringIO
import socket

category_blacklist = []
countries = []

def initLists():
    '''
    Get the list of countries & the blacklist from Commons.
    '''
    global category_blacklist
    global countries

    blacklistPage = wikipedia.Page(wikipedia.getSite(), u'User:Multichill/Category_blacklist')
    for cat in blacklistPage.linkedPages():
        category_blacklist.append(cat.titleWithoutNamespace())

    countryPage = wikipedia.Page(wikipedia.getSite(), u'User:Multichill/Countries')
    for country in countryPage.linkedPages():
        countries.append(country.titleWithoutNamespace())
    return

def categorizeImages(generator, onlyfilter):
    '''
    Loop over all images in generator and try to categorize them. Get category suggestions from CommonSense.
    '''
    for page in generator:
        if page.exists() and (page.namespace() == 6) and (not page.isRedirectPage()):
            imagepage = wikipedia.ImagePage(page.site(), page.title())
            #imagepage.get()
            wikipedia.output(u'Working on ' + imagepage.title());
            currentCats = getCurrentCats(imagepage)
            if(onlyfilter):
                commonshelperCats = []
                usage = []
                galleries = []
            else:
                (commonshelperCats, usage, galleries) = getCommonshelperCats(imagepage)
            newcats = applyAllFilters(commonshelperCats+currentCats)

            if (len(newcats) > 0 and not(set(currentCats)==set(newcats))):
                for cat in newcats:
                    wikipedia.output(u' Found new cat: ' + cat);
                saveImagePage(imagepage, newcats, usage, galleries, onlyfilter)


def getCurrentCats(imagepage):
    '''
    Get the categories currently on the image
    '''
    result = []
    for cat in imagepage.categories():
        result.append(cat.titleWithoutNamespace())
    return list(set(result))


def getCommonshelperCats(imagepage):
    '''
    Get category suggestions from CommonSense. Parse them and return a list of suggestions.
    '''
    commonshelperCats = []
    usage = []
    galleries = []
    
    parameters = urllib.urlencode({'i' : imagepage.titleWithoutNamespace().encode('utf-8'), 'r' : 'on', 'go-clean' : 'Find+Categories', 'cl' : 'li'})
    commonsenseRe = re.compile('^#COMMONSENSE(.*)#USAGE(\s)+\((?P<usagenum>(\d)+)\)\s(?P<usage>(.*))\s#KEYWORDS(\s)+\((?P<keywords>(\d)+)\)(.*)#CATEGORIES(\s)+\((?P<catnum>(\d)+)\)\s(?P<cats>(.*))\s#GALLERIES(\s)+\((?P<galnum>(\d)+)\)\s(?P<gals>(.*))\s(.*)#EOF$', re.MULTILINE + re.DOTALL)

    gotInfo = False;

    while(not gotInfo):
        try:
            commonsHelperPage = urllib.urlopen("http://toolserver.org/~daniel/WikiSense/CommonSense.php?%s" % parameters)
            matches = commonsenseRe.search(commonsHelperPage.read().decode('utf-8'))
            gotInfo = True
        except IOError:
            wikipedia.output(u'Got an IOError, let\'s try again')
        except socket.timeout:
            wikipedia.output(u'Got a timeout, let\'s try again')

    if matches:
        if(matches.group('usagenum') > 0):
            used = matches.group('usage').splitlines()
            for use in used:
                usage= usage + getUsage(use)
                #wikipedia.output(use)
        if(matches.group('catnum') > 0):
            cats = matches.group('cats').splitlines()
            for cat in cats:
                commonshelperCats.append(cat.replace('_',' '))
                wikipedia.output(u'category : ' + cat)
        if(matches.group('galnum') > 0):
            gals = matches.group('gals').splitlines()
            for gal in gals:
                galleries.append(gal.replace('_',' '))
                wikipedia.output(u'gallery : ' + gal)
    commonshelperCats = list(set(commonshelperCats))
    galleries = list(set(galleries))
    for (lang, project, article) in usage:
        wikipedia.output(lang + project + article)
        
    return (commonshelperCats, usage, galleries)

def getUsage(use):
    result = []
    lang = ''
    project = ''
    article = ''
    usageRe = re.compile('^(?P<lang>([\w]+))\.(?P<project>([\w]+))\.org:(?P<articles>\s(.*))')
    matches = usageRe.search(use)
    if matches:
        if(matches.group('lang')):
            lang = matches.group('lang')
            #wikipedia.output(lang)
        if(matches.group('project')):
            project = matches.group('project')
            #wikipedia.output(project)
        if(matches.group('articles')):
            articles = matches.group('articles')
            #wikipedia.output(articles)
    for article in articles.split():
        result.append((lang, project, article))

    return result
    
                         

def applyAllFilters(categories):
    result = []
    result = filterBlacklist(categories)
    result = filterDisambiguation(result)
    result = followRedirects(result)
    result = filterCountries(result)
    result = filterParents(result)
    return result


def filterBlacklist(categories):
    '''
    Filter out categories which are on the blacklist.
    '''
    result = []
    for cat in categories:
        cat = cat.replace('_', ' ')
        if (cat not in category_blacklist):
            result.append(cat)
    return list(set(result))


def filterDisambiguation(categories):
    '''
    Filter out disambiguation categories.
    '''
    result = []
    for cat in categories:
        if(not wikipedia.Page(wikipedia.getSite(), u'Category:' + cat).isDisambig()):
            result.append(cat)
    return result

def followRedirects(categories):
    '''
    If a category is a redirect, replace the category with the target.
    '''
    result = []
    for cat in categories:
        categoryPage = wikipedia.Page(wikipedia.getSite(), u'Category:' + cat)
        if u'Category redirect' in categoryPage.templates() or u'Seecat' in categoryPage.templates():
            for template in categoryPage.templatesWithParams():
                if ((template[0]==u'Category redirect' or template[0]==u'Seecat') and (len(template[1]) > 0)):
                    result.append(template[1][0])
        else:
            result.append(cat)
    return result


def filterCountries(categories):
    '''
    Try to filter out ...by country categories.
    First make a list of any ...by country categories and try to find some countries.
    If a by country category has a subcategoy containing one of the countries found, add it.
    The ...by country categories remain in the set and should be filtered out by filterParents.
    '''
    result = categories
    listByCountry = []
    listCountries = []
    for cat in categories:
        if (cat.endswith(u'by country')):
            listByCountry.append(cat)

        #If cat contains 'by country' add it to the list
        #If cat contains the name of a country add it to the list
        else:
            for country in countries:
                if not(cat.find(country)==-1):
                    listCountries.append(country)

    if(len(listByCountry) > 0):
        for bc in listByCountry:
            category = catlib.Category(wikipedia.getSite(), u'Category:' + bc)
            for subcategory in category.subcategories():
                for country in listCountries:
                    if (subcategory.titleWithoutNamespace().endswith(country)):
                        result.append(subcategory.titleWithoutNamespace())

    return list(set(result))


def filterParents(categories):
    '''
    Remove all parent categories from the set to prevent overcategorization.
    '''
    result = []
    toFilter = u''

    for cat in categories:
        cat = cat.replace('_',' ')
        toFilter = toFilter + "[[Category:" + cat + "]]\n"
    #try:
    parameters = urllib.urlencode({'source' : toFilter.encode('utf-8'), 'bot' : '1'})
    filterCategoriesRe = re.compile('\[\[Category:([^\]]*)\]\]')
    try:
        filterCategoriesPage = urllib.urlopen("http://toolserver.org/~multichill/filtercats.php?%s" % parameters)
        result = filterCategoriesRe.findall(filterCategoriesPage.read().decode('utf-8'))
    except IOError:
        #Something is wrong, forget about this filter and just return the input
        return categories
        
    if not result:
        #Is empty, dont want to remove all categories
        return categories
    return result


def saveImagePage(imagepage, newcats, usage, galleries, onlyfilter):
    '''
    Remove the old categories and add the new categories to the image.
    '''
    newtext = wikipedia.removeCategoryLinks(imagepage.get(), imagepage.site())    

    if not(onlyfilter):
        newtext = removeTemplates(newtext)
        newtext = newtext + getCheckCategoriesTemplate(usage, galleries, len(newcats))
    for category in newcats:
        newtext = newtext + u'[[Category:' + category + u']]\n'

    if(onlyfilter):
        comment = u'Filtering categories'
    else:
        comment = u'Image is categorized by a bot using data from [[Commons:Tools#CommonSense|CommonSense]]'

    wikipedia.showDiff(imagepage.get(), newtext)
    imagepage.put(newtext, comment)
    return


def removeTemplates(oldtext = u''):
    '''
    Remove {{Uncategorized}} and {{Check categories}} templates
    '''
    result = u''
    result = re.sub(u'\{\{\s*([Uu]ncat(egori[sz]ed( image)?)?|[Nn]ocat|[Nn]eedscategory)[^}]*\}\}', u'', oldtext)
    result = re.sub(u'<!-- Remove this line once you have added categories -->', u'', result)
    result = re.sub(u'\{\{\s*[Cc]heck categories[^}]*\}\}', u'', result)
    return result

def getCheckCategoriesTemplate(usage, galleries, ncats):
    result = u'{{Check categories|year={{subst:CURRENTYEAR}}|month={{subst:CURRENTMONTHNAME}}|day={{subst:CURRENTDAY}}\n'

    usageCounter = 1
    for (lang, project, article) in usage:
        result = result + u'|lang' + str(usageCounter) + u'=' + lang
        result = result + u'|wiki' + str(usageCounter) + u'=' + project
        result = result + u'|article' + str(usageCounter) + u'=' + article
        result = result + u'\n'
        usageCounter = usageCounter + 1
    
    galleryCounter = 1
    for gallery in galleries:
        result = result + u'|gallery' + str(galleryCounter) + u'=' + gallery.replace('_', ' ') + u'\n'
        galleryCounter = galleryCounter + 1
    
    result = result + u'|ncats='+ str(ncats) + u'\n'
    result = result + u'}}\n'
    return result    


def main(args):
    '''
    Main loop. Get a generator. Set up the 3 threads and the 2 queue's and fire everything up.
    '''
    generator = None
    onlyfilter = False
    genFactory = pagegenerators.GeneratorFactory()

    site = wikipedia.getSite(u'commons', u'commons')
    wikipedia.setSite(site)
    for arg in wikipedia.handleArgs():
        if arg == '-onlyfilter':
            onlyfilter = True
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if not generator:
        generator = pagegenerators.CategorizedPageGenerator(catlib.Category(site, u'Category:Media needing categories'), recurse=True)

    initLists()
    categorizeImages(generator, onlyfilter)

    wikipedia.output(u'All done')

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    finally:
        wikipedia.stopme()
