#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
With this tool you can add the template {{commonscat}} to categories.
The tool works by following the interwiki links. If the template is present on
another langauge page, the bot will use it.

You could probably use it at articles as well, but this isnt tested.

This bot uses pagegenerators to get a list of pages. For example to go through all categories:
commonscat.py -start:Category:!

Commonscat bot:

Take a page. Follow the interwiki's and look for the commonscat template
*Found zero templates. Done.
*Found one template. Add this template
*Found more templates. Ask the user <- still have to implement this

TODO:
*Update interwiki's at commons
*Collect all possibilities also if local wiki already has link.
*Better support for other templates (translations) / redundant templates.
*Check mode, only check pages which already have the template
*More efficient like interwiki.py
*Possibility to update other languages in the same run

"""

#
# (C) Multichill, 2008
#
# Distributed under the terms of the MIT license.
#

import wikipedia, config, pagegenerators, add_text

commonscatTemplates = {
    '_default': u'Commonscat',
    'af' : u'CommonsKategorie',
    'ar' : u'تصنيف كومنز',
    'als' : u'Commonscat',
    'az' : u'CommonsKat',
    'bg' : u'Commonscat',
    'ca' : u'Commonscat',
    'cs' : u'Commonscat',
    'da' : u'Commonscat',
    'de' : u'Commonscat',
    'en' : u'Commons cat',
    'eo' : u'Commonscat',
    'es' : u'Commonscat',
    'eu' : u'Commonskat',
    'fi' : u'Commonscat',
    'fr' : u'Commonscat',
    'hr' : u'Commonscat',
    'hu' : u'Közvagyonkat',
    'id' : u'Commonscat',
    'io' : u'Commonscat',
    'is' : u'CommonsCat',
    'it' : u'Commonscat',
    'ja' : u'Commonscat',
    'ko' : u'Commonscat',
    'lt' : u'Commonscat',
    'lv' : u'Commonscat',
    'mk' : u'Ризница-врска',
    'ms' : u'Commonscat',
    'nl' : u'Commonscat',
    'nn' : u'Commonscat',
    'no' : u'Commonscat',
    'oc' : u'Commonscat',
    'os' : u'Commonscat',
    'pl' : u'Commonscat',
    'pt' : u'Commonscat',
    'ro' : u'Commonscat',
    'ru' : u'Commonscat',
    'scn' : u'Commonscat',
    'sh' : u'Commonscat',
    'simple' : u'Commonscat',
    'sk' : u'Commonscat',
    'sl' : u'Kategorija v Zbirki',
    'sr' : u'Commonscat',
    'su' : u'Commonscat',
    'sv' : u'Commonscat',
    'th' : u'Commonscat',
    'tr' : u'CommonsKat',
    'uk' : u'Commonscat',
    'vi' : u'Commonscat',
    'zh' : u'Commonscat',
    'zh-yue' : u'同享類'
}

ignoreTemplates = {    
    'en' : [u'Category redirect', u'Commons', u'Commonscat1A', u'Commoncats', u'Commonscat4Ra', u'Sisterlinks', u'Sisterlinkswp', u'Tracking category', u'Template category', u'Wikipedia category'],
    'nl' : [u'Commons']
}

def getTemplate (lang = None):
    '''
    Get the template name in a language. Expects the language code, returns the translation.
    '''
    if commonscatTemplates.has_key(lang):
        return commonscatTemplates[lang]
    else:
        return u'Commonscat'

def skipPage(page):
    '''
    Do we want to skip this page?
    '''
    if ignoreTemplates.has_key(page.site().language()):
        for template in page.templates():
            if template in ignoreTemplates[page.site().language()]:                
                return True
    return False    

def updateInterwiki (wikipediaPage = None, commonsPage = None):
    '''
    Update the interwiki's at commons from a wikipedia page. The bot just replaces the interwiki links at the commons page with the interwiki's from the wikipedia page.
    This should probably be more intelligent. We could use add all the interwiki's and remove duplicates. Or only remove language links if multiple language links to the same language exist.

    This function is disabled for the moment untill i figure out what the best way is to update the interwiki's.
    '''
    interwikis = {}
    comment= u''
    interwikilist = wikipediaPage.interwiki()
    interwikilist.append(wikipediaPage)

    for interwikiPage in interwikilist:
        interwikis[interwikiPage.site()]=interwikiPage
    oldtext = commonsPage.get()
    # The commonssite object doesnt work with interwiki's
    newtext = wikipedia.replaceLanguageLinks(oldtext, interwikis, wikipedia.getSite(u'nl'))    
    comment = u'Updating interwiki\'s from [[' + wikipediaPage.site().language()  + u':' + wikipediaPage.title() + u']]'    

    if newtext != oldtext:
        #This doesnt seem to work. Newtext has some trailing whitespace
        wikipedia.showDiff(oldtext, newtext)
        commonsPage.put(newtext=newtext, comment=comment)
    

def addCommonscat (page = None, summary = None, always = False):
    '''
    Take a page. Go to all the interwiki page looking for a commonscat template.
    When all the interwiki's links are checked and a proper category is found add it to the page.
    '''
    commonscat = ""
    commonscatpage = None
    commonscats = []
    
    wikipedia.output("Working on " + page.title());
    if getTemplate(page.site().language()) in page.templates():
        wikipedia.output("Commonscat template is already on " + page.title());
        #for template in page.templatesWithParams():
        #    if ((template[0]==getTemplate(page.site().language())) and (len(template[1]) > 0)):
        #       commonscatpage = getCommonscat(template[1][0])
        #       if commonscatpage != None:
        #            updateInterwiki (page, commonscatpage)
        #        #Should remove the template if something is wrong
    elif skipPage(page):
        wikipedia.output("Found a template in the skip list. Skipping " + page.title());                
    else:
        #Follow the interwiki's
        for ipage in page.interwiki():
            #See if commonscat is present
            if getTemplate(ipage.site().language()) in ipage.templates():
                #Go through all the templates at the page
                for template in ipage.templatesWithParams():
                   #We found the template and it has the parameter set.
                   if ((template[0]==getTemplate(ipage.site().language())) and (len(template[1]) > 0)):
                        commonscatpage = getCommonscat(template[1][0])
                        if commonscatpage != None:
                            commonscats.append(commonscatpage);
                            wikipedia.output("Found link for " + page.title() + " at [[" + ipage.site().language() + ":" + ipage.title() + "]] to " + commonscatpage.title() + ".");
                            commonscatpage = None
        if len(commonscats) > 0:
            commonscatpage = commonscats.pop();
            commonscat = commonscatpage.titleWithoutNamespace()
            #We found one or more commonscat links, build the template and add it to our page
            #TODO: We should check if we found more than one different link.            
            commonscat = "{{" + getTemplate(page.site().language()) + "|" + commonscat + "}}";
            (success, always) = add_text.add_text(page, commonscat, summary, None, None, always);
            #updateInterwiki(page, commonscatpage)
    return (True, always);

def getCommonscat (name = ""):
    '''
    This function will retun a page object of the commons page
    If the page is a redirect this function tries to follow it.
    If the page doesnt exists the function will return None
    '''
    #wikipedia.output("getCommonscat: " + name );
    result = wikipedia.Page(wikipedia.getSite("commons", "commons"), "Category:" + name);
    if not result.exists():
        #wikipedia.output("getCommonscat : The category doesnt exist.");
        return None
    elif result.isRedirectPage():
        #wikipedia.output("getCommonscat : The category is a redirect");
        return result.getRedirectTarget();
    elif "Category redirect" in result.templates():
        #wikipedia.output("getCommonscat : The category is a category redirect");
        for template in result.templatesWithParams():
            if ((template[0]=="Category redirect") and (len(template[1]) > 0)):
                return getCommonscat(template[1][0])                 
    elif result.isDisambig():
        #wikipedia.output("getCommonscat : The category is disambigu");
        return None
    else:
        return result

def main():
    '''
    Parse the command line arguments and get a pagegenerator to work on.
    Iterate through all the pages.
    '''
    summary = None; generator = None; always = False
    # Load a lot of default generators
    genFactory = pagegenerators.GeneratorFactory()

    for arg in wikipedia.handleArgs():
        if arg.startswith('-summary'):
            if len(arg) == 8:
                summary = wikipedia.input(u'What summary do you want to use?')
            else:
                summary = arg[9:]
        elif arg.startswith('-page'):
            if len(arg) == 5:
                generator = [wikipedia.Page(wikipedia.getSite(), wikipedia.input(u'What page do you want to use?'))]
            else:
                generator = [wikipedia.Page(wikipedia.getSite(), arg[6:])]
        elif arg == '-always':
            always = True
        else:
            generator = genFactory.handleArg(arg)
    if not generator:
        raise add_text.NoEnoughData('You have to specify the generator you want to use for the script!')

    pregenerator = pagegenerators.PreloadingGenerator(generator)

    for page in pregenerator:    
        (status, always) = addCommonscat(page, summary, always)        

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
