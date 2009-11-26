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
__version__ = '$Id$'

import wikipedia, config, pagegenerators, add_text, re

#Primary template, list of alternatives
commonscatTemplates = {
    '_default': (u'Commonscat', []),
    'af' : (u'CommonsKategorie', [u'commonscat']),
    'als' : (u'Commonscat', []),
    'an' : (u'Commonscat', []),
    'ang' : (u'Commonscat', []),
    'ar' : (u'تصنيف كومنز', [u'Commonscat', u'تصنيف كومونز', u'Commons cat', u'CommonsCat']),
    'ast' : (u'Commonscat', []), # No alternatives found
    'az' : (u'CommonsKat', []),
    'bar' : (u'Commonscat', []),
    'bat-smg' : (u'Commonscat', []),
    'be' : (u'Commonscat', []), # No alternatives found
    'bg' : (u'Commonscat', []),
    'bn' : (u'কমন্সক্যাট', [u'Commonscat']),
    'br' : (u'Commonscat', []), # No alternatives found
    'ca' : (u'Commonscat', []),
    'cbk-zam' : (u'Commonscat', []), # No alternatives found
    'chr' : (u'Commonscat', []), # No alternatives found
    'crh' : (u'CommonsKat', [u'Commonscat']),
    'cs' : (u'Commonscat', [u'Commons cat']),
    'cu' : (u'Commonscat', []), # No alternatives found
    'cv' : (u'Commonscat', []), # No alternatives found
    'da' : (u'Commonscat', [u'Commons cat', u'Commonskat', u'Commonscat2']),
    'de' : (u'Commonscat', []), # No alternatives found
    'diq' : (u'Commonscat', []), # No alternatives found
    'dv' : (u'Commonscat', []), # No alternatives found
    'el' : (u'Commonscat', []), # No alternatives found
    'en' : (u'Commons category', [u'Commoncat', u'Commons2', u'Cms-catlist-up', u'Catlst commons', u'Commonscategory', u'Commonscat', u'Commons cat']),
    'eo' : (u'Commonscat', []), # No alternatives found
    'es' : (u'Commonscat', [u'Ccat', u'Commons cat', u'Categoría Commons', u'Commonscat-inline']),
    'eu' : (u'Commonskat', [u'Commonscat']),
    'fa' : (u'انبار-رده', [u'Commonscat', u'Commons cat', u'انبار رده', u'Commons category']),
    'fi' : (u'Commonscat', []), # No alternatives found
    'fr' : (u'Commonscat', [u'CommonsCat', u'Commons cat', u'Commons category']),
    'frp' : (u'Commonscat', [u'CommonsCat']), 
    'fy' : (u'Commonscat', []),
    'ga' : (u'Catcómhaoin', [u'Commonscat']),
    'gd' : (u'Commonscat', []), # No alternatives found
    'gv' : (u'Commonscat', []), # No alternatives found
    'ha' : (u'Commonscat', []),
    'he' : (u'Commonscat', []),
    'hi' : (u'Commonscat', [u'Commons2', u'Commons cat', u'Commons category']),
    'hr' : (u'Commonscat', []),
    'hu' : (u'Közvagyonkat', []),
    'hy' : (u'Commons cat', [u'Commonscat']),
    'ia' : (u'Commonscat', []),
    'id' : (u'Commonscat', [u'Commons cat', u'Commons2', u'CommonsCat', u'Commons category']),
    'io' : (u'Commonscat', []),
    'is' : (u'CommonsCat', []),
    'it' : (u'Commonscat', []),
    'ja' : (u'Commonscat', [u'Commons cat', u'Commons category']),
    'jv' : (u'Commonscat', [u'Commons cat']),
    'ka' : (u'Commonscat', []),
    'kaa' : (u'Commons cat', [u'Commonscat']),
    'kg' : (u'Commonscat', []), # No alternatives found
    'kk' : (u'Commonscat', [u'Commons2']),
    'km' : (u'Commonscat', []),
    'kn' : (u'Commonscat', []), # No alternatives found
    'ko' : (u'Commonscat', [u'Commons cat', u'공용분류']),
    'la' : (u'CommuniaCat', []),
    'lad' : (u'Commonscat', []),
    'lbe' : (u'Commonscat', []), # No alternatives found
    'li' : (u'Commonscat', []),
    'lo' : (u'Commonscat', []),
    'lt' : (u'Commonscat', []),
    'lv' : (u'Commonscat', []),
    'mi' : (u'Commonscat', []),
    'mk' : (u'Ризница-врска', [u'Commonscat', u'Commons cat', u'CommonsCat', u'Commons2', u'Commons category']),
    'ml' : (u'Commonscat', [u'Commons cat', u'Commons2']),
    'mn' : (u'Commonscat', []),
    'ms' : (u'Commonscat', []),
    'nah' : (u'Commonscat', []),
    'nds-nl' : (u'Commonscat', []),
    'new' : (u'Commonscat', []), # No alternatives found
    'nl' : (u'Commonscat', []), # No alternatives found
    'nn' : (u'Commonscat', [u'Commons cat']),
    'no' : (u'Commonscat', []), # No alternatives found
    'oc' : (u'Commonscat', []),
    'om' : (u'Commonscat', []),
    'os' : (u'Commonscat', [u'Commons cat']),
    'pam' : (u'Commonscat', []),
    'pl' : (u'Commonscat', []), # No alternatives found
    'pt' : (u'Commonscat', [u'Commons cat']),
    'qu' : (u'Commonscat', []),
    'ro' : (u'Commonscat', [u'Commons cat']),
    'ru' : (u'Commonscat', [u'Викисклад-кат']),
    'sah' : (u'Commonscat', []),
    'scn' : (u'Commonscat', []),
    'sd' : (u'Commonscat', []), # No alternatives found
    'se' : (u'Commonscat', []),
    'sh' : (u'Commonscat', []),
    'si' : (u'Commonscat', []),
    'simple' : (u'Commonscat', []),
    'sk' : (u'Commonscat', []), # No alternatives found
    'sl' : (u'Kategorija v Zbirki', [u'Commonscat', u'Kategorija v zbirki', u'Commons cat', u'Katzbirke']),
    'so' : (u'Commonscat', []),
    'sr' : (u'Commonscat', []),
    'su' : (u'Commonscat', []),
    'sv' : (u'Commonscat', [u'Commonscat-rad', u'Commonskat', u'Commons cat']),
    'sw' : (u'Commonscat', [u'Commons2', u'Commons cat']),
    'ta' : (u'Commonscat', []),
    'te' : (u'Commonscat', [u'Commons cat']),
    'th' : (u'Commonscat', []),
    'tl' : (u'Commonscat', []),
    'tr' : (u'CommonsKat', [u'Commonscat', u'Commons cat']),
    'tt' : (u'Commonscat', []),
    'udm' : (u'Commonscat', []),
    'uk' : (u'Commonscat', [u'Commons cat', u'Category', u'Commonscat-inline']),
    'uz' : (u'Commonscat', []),
    'vi' : (u'Commonscat', [u'Commons2', u'Commons cat', u'Commons category', u'Commons+cat']),
    'vls' : (u'Commonscat', []),
    'war' : (u'Commonscat', []),
    'xal' : (u'Commonscat', []),
    'zea' : (u'Commonscat', []),
    'zh' : (u'Commonscat', [u'Commons cat']),
    'zh-classical' : (u'共享類', [u'Commonscat']),
    'zh-yue' : (u'同享類', [u'Commonscat', u'共享類 ', u'Commons cat']),
}

ignoreTemplates = {
    'af' : [u'commons'],
    'ar' : [u'تحويلة تصنيف', u'كومنز', u'كومونز', u'Commons'],
    'cs' : [u'Commons', u'Sestřičky', u'Sisterlinks'],
    'da' : [u'Commons', u'Commons left', u'Commons2', u'Commonsbilleder', u'Commonscat left', u'Commonscat2', u'GalleriCommons', u'Søsterlinks'],
    'de' : [u'Commons'],
    'en' : [u'Category redirect', u'Commons', u'Commonscat1A', u'Commoncats', u'Commonscat4Ra', u'Sisterlinks', u'Sisterlinkswp', u'Tracking category', u'Template category', u'Wikipedia category'],
    'eo' : [u'Commons', (u'Projekto/box', 'commons='), (u'Projekto', 'commons='), (u'Projektoj', 'commons='), (u'Projektoj', 'commonscat=')],
    'es' : [u'Commons', u'IprCommonscat'],
    'eu' : [u'Commons'],
    'fa' : [u'Commons', u'ویکی‌انبار'],
    'fi' : [u'Commonscat-rivi', u'Commons-rivi', u'Commons'],
    'fr' : [u'Commons', u'Commons-inline', (u'Autres projets', 'commons=')],
    'fy' : [u'Commons', u'CommonsLyts'],
    'hr' : [u'Commons', (u'WProjekti', 'commonscat=')],
    'it' : [(u'Ip', 'commons='), (u'Interprogetto', 'commons=')],
    'ja' : [u'CommonscatS', u'SisterlinksN', u'Interwikicat'],
    'nds-nl' : [u'Commons'],
    'nl' : [u'Commons', u'Commonsklein', u'Commonscatklein', u'Catbeg', u'Catsjab', u'Catwiki'],
    'om' : [u'Commons'],
    'ru' : [u'Навигация'],
}

def getCommonscatTemplate (lang = None):
    '''
    Get the template name in a language. Expects the language code.
    Return as tuple containing the primary template and it's alternatives
    '''
    if lang in commonscatTemplates:
        return  commonscatTemplates[lang]
    else:
        return commonscatTemplates[u'_default']

def skipPage(page):
    '''
    Do we want to skip this page?
    '''
    if page.site().language() in ignoreTemplates:
        templatesInThePage = page.templates()
        templatesWithParams = page.templatesWithParams()
        for template in ignoreTemplates[page.site().language()]:
            if type(template) != tuple:
                if template in templatesInThePage:
                    return True
            else:
                for (inPageTemplate, param) in templatesWithParams:
                    if inPageTemplate == template[0] and template[1] in param[0]:
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
    wikipedia.output(u'Working on ' + page.title());
    #Get the right templates for this page
    primaryCommonscat, commonscatAlternatives=getCommonscatTemplate(page.site().language())
    commonscatLink = getCommonscatLink (page)
    if commonscatLink:
        wikipedia.output(u'Commonscat template is already on ' + page.title());
        (currentCommonscatTemplate, currentCommonscatTarget) = commonscatLink
        checkedCommonscatTarget = checkCommonscatLink(currentCommonscatTarget)
        if (currentCommonscatTarget==checkedCommonscatTarget):
            #The current commonscat link is good
            wikipedia.output(u'Commonscat link at ' + page.title() + u' to Category:' + currentCommonscatTarget + u' is ok');
            return (True, always)
        elif checkedCommonscatTarget!=u'':
            #We have a new Commonscat link, replace the old one
            changeCommonscat (page, currentCommonscatTemplate, currentCommonscatTarget, primaryCommonscat, checkedCommonscatTarget)
            return (True, always)
        else:
            #Commonscat link is wrong
            commonscatLink = findCommonscatLink(page)
            if (commonscatLink!=u''):
                changeCommonscat (page, currentCommonscatTemplate, currentCommonscatTarget, primaryCommonscat, commonscatLink)
            #else
            #Should i remove the commonscat link?

    elif skipPage(page):
        wikipedia.output("Found a template in the skip list. Skipping " + page.title());
    else:
        commonscatLink = findCommonscatLink(page)
        if (commonscatLink!=u''):
            textToAdd = u'{{' + primaryCommonscat + u'|' + commonscatLink + u'}}'
            (success, status, always) = add_text.add_text(page, textToAdd, summary, None, None, always);
            return (True, always);

    return (True, always);

def changeCommonscat (page = None, oldtemplate = u'', oldcat = u'', newtemplate = u'', newcat = u''):
    '''
    Change the current commonscat template and target. 
    '''
    newtext = re.sub(u'(?i)\{\{' + oldtemplate + u'\|?[^}]*\}\}',  u'{{' + newtemplate + u'|' + newcat + u'}}', page.get())
    comment = u'Changing commonscat link from [[:Commons:Category:' + oldcat + u'|' + oldcat + u']] to [[:Commons:Category:' + newcat + u'|' + newcat + u']]'
    wikipedia.showDiff(page.get(), newtext)
    page.put(newtext, comment)

def findCommonscatLink (page=None):
    for ipage in page.interwiki():
        try:
            if(ipage.exists() and not ipage.isRedirectPage() and not ipage.isDisambig()):
                commonscatLink = getCommonscatLink (ipage)
                if commonscatLink:
                    (currentCommonscatTemplate, possibleCommonscat) = commonscatLink
                    checkedCommonscat = checkCommonscatLink(possibleCommonscat)
                    if (checkedCommonscat!= u''):
                        wikipedia.output("Found link for " + page.title() + " at [[" + ipage.site().language() + ":" + ipage.title() + "]] to " + checkedCommonscat + ".")
                        return checkedCommonscat
        except wikipedia.BadTitle:
            #The interwiki was incorrect
            return u''
    return u''


def getCommonscatLink (wikipediaPage=None):
    '''
    Go through the page and return a tuple of (<templatename>, <target>)
    '''
    primaryCommonscat, commonscatAlternatives=getCommonscatTemplate(wikipediaPage.site().language())
    commonscatTemplate =u''
    commonscatTarget = u''
    #See if commonscat is present

    for template in wikipediaPage.templatesWithParams():
        if template[0]==primaryCommonscat or template[0] in commonscatAlternatives:
            commonscatTemplate = template[0]
            if (len(template[1]) > 0):
                commonscatTarget = template[1][0]
            else:
                commonscatTarget = wikipediaPage.titleWithoutNamespace()
            return (commonscatTemplate, commonscatTarget)

    return None

def checkCommonscatLink (name = ""):
    '''
    This function will retun the name of a valid commons category
    If the page is a redirect this function tries to follow it.
    If the page doesnt exists the function will return an empty string
    '''
    #wikipedia.output("getCommonscat: " + name );
    try:
        #This can throw a wikipedia.BadTitle
        commonsPage = wikipedia.Page(wikipedia.getSite("commons", "commons"), "Category:" + name);

        if not commonsPage.exists():
            #wikipedia.output("getCommonscat : The category doesnt exist.");
            return u''
        elif commonsPage.isRedirectPage():
            #wikipedia.output("getCommonscat : The category is a redirect");
            return checkCommonscatLink(commonsPage.getRedirectTarget().titleWithoutNamespace());
        elif "Category redirect" in commonsPage.templates():
            #wikipedia.output("getCommonscat : The category is a category redirect");
            for template in commonsPage.templatesWithParams():
                if ((template[0]=="Category redirect") and (len(template[1]) > 0)):
                    return checkCommonscatLink(template[1][0])
        elif commonsPage.isDisambig():
            #wikipedia.output("getCommonscat : The category is disambigu");
            return u''
        else:
            return commonsPage.titleWithoutNamespace()
    except wikipedia.BadTitle:
        #Funky title so not correct
        return u''        

def main():
    '''
    Parse the command line arguments and get a pagegenerator to work on.
    Iterate through all the pages.
    '''
    summary = None; generator = None; checkcurrent = False; always = False
    ns = []
    ns.append(14)
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
        elif arg.startswith('-checkcurrent'):
            checkcurrent = True
            primaryCommonscat, commonscatAlternatives = getCommonscatTemplate(wikipedia.getSite().language())
            generator = pagegenerators.NamespaceFilterPageGenerator(pagegenerators.ReferringPageGenerator(wikipedia.Page(wikipedia.getSite(), u'Template:' + primaryCommonscat), onlyTemplateInclusion=True), ns)

        elif arg == '-always':
            always = True
        else:
            genFactory.handleArg(arg)

    if not generator:
        generator = genFactory.getCombinedGenerator()
    if not generator:
        raise add_text.NoEnoughData('You have to specify the generator you want to use for the script!')

    pregenerator = pagegenerators.PreloadingGenerator(generator)

    for page in pregenerator:
        if(page.exists() and not page.isRedirectPage() and not page.isDisambig()):
            (status, always) = addCommonscat(page, summary, always)

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
