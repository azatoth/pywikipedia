#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This module offers a wide variety of page generators. A page generator is an
object that is iterable (see http://www.python.org/dev/peps/pep-0255/ ) and
that yields page objects on which other scripts can then work.

In general, there is no need to run this script directly. It can, however,
be run for testing purposes.
"""
__version__='$Id$'

# Standard library imports
import re, codecs, sys
import urllib, time

# Application specific imports
import wikipedia, date, catlib
import config

def AllpagesPageGenerator(start ='!', namespace = None, includeredirects = True):
    """
    Using the Allpages special page, retrieve all articles' titles, and yield
    page objects.
    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.
    """
    if namespace==None:
        namespace = wikipedia.Page(wikipedia.getSite(), start).namespace()
    for page in wikipedia.getSite().allpages(start=start, namespace=namespace, includeredirects = includeredirects):
        yield page
    
def PrefixingPageGenerator(prefix, namespace=None):
    for page in AllpagesPageGenerator(prefix, namespace):
        if page.titleWithoutNamespace().startswith(prefix):
            yield page
        else:
            break

def NewpagesPageGenerator(number = 100, get_redirect = False, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.newpages(number=number, get_redirect=get_redirect, repeat=repeat):
        yield page[0]
        
def FileLinksGenerator(referredPage):
    for page in referredPage.getFileLinks():
        yield page

def ImagesPageGenerator(pageWithImages):
    for page in pageWithImages.imagelinks(followRedirects = False, loose = True):
        yield page

def UnusedFilesGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.unusedfiles(number=number, repeat=repeat):
        yield wikipedia.ImagePage(page.site(), page.title()) 

def ReferringPageGenerator(referredPage, followRedirects=False,
                           withTemplateInclusion=True,
                           onlyTemplateInclusion=False):
    '''Yields all pages referring to a specific page.'''
    for page in referredPage.getReferences(followRedirects,
                                           withTemplateInclusion,
                                           onlyTemplateInclusion):
        yield page

def ReferringPagesGenerator(referredPages, followRedirects=False,
                            withTemplateInclusion=True,
                            onlyTemplateInclusion=False):
    """Yields all unique pages referring to a list of specific pages."""
    allPages = []
    for referredPage in referredPages:
        for page in referredPage.getReferences(followRedirects,
                                               withTemplateInclusion,
                                               onlyTemplateInclusion):
            allPages.append(page)

    #Remove duplicate pages.
    allPages = list(set(allPages))
    wikipedia.output(u'Page generator found %s pages.' % len(allPages))

    for page in allPages:
        yield page

def CategorizedPageGenerator(category, recurse = False, start = None):
    '''
    Yields all pages in a specific category.

    If recurse is True, pages in subcategories are included as well.
    If start is a string value, only pages whose title comes after start
    alphabetically are included.
    '''
    for page in category.articles(recurse = recurse, startFrom = start):
        if page.title() >= start:
            yield page

def UnCategorizedPageGenerator(number = 100, repeat = False, site = None):
    if site is None:
        site = wikipedia.getSite()
    for page in site.uncategorizedpages(number=number, repeat=repeat):
        yield page

def LinkedPageGenerator(linkingPage):
    """Yields all pages linked from a specific page."""
    for page in linkingPage.linkedPages():
        yield page

def TextfilePageGenerator(filename=None):
    '''
    Read a file of page links between double-square-brackets, and return
    them as a list of Page objects. filename is the name of the file that
    should be read. If no name is given, the generator prompts the user.
    '''
    if filename is None:
        filename = wikipedia.input(u'Please enter the filename:')
    site = wikipedia.getSite()
    f = codecs.open(filename, 'r', config.textfile_encoding)
    R = re.compile(ur'\[\[(.+?)(?:\]\]|\|)') # title ends either before | or before ]]
    for pageTitle in R.findall(f.read()):
        site = wikipedia.getSite()
        # If the link doesn't refer to this site, the Page constructor
        # will automatically choose the correct site.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield wikipedia.Page(site, pageTitle)
    f.close()

def PagesFromTitlesGenerator(iterable):
    """Generates pages from the titles (unicode strings) yielded by iterable"""
    for title in iterable:
        if not isinstance(title, basestring):
            break
        yield wikipedia.Page(wikipedia.getSite(), title)

def LinksearchGenerator(site, link, step=500):
    """Yields all pages that include a specified link, according to [[Special:Linksearch]].
    Retrieves in chunks of size "step" (default 500).
    Does not guarantee that resulting pages are unique."""
    elRX = re.compile('<a .* class="external ?" .*</a>.*<a .*>(.*)</a>') #TODO: de-uglify?
    offset = 0
    found = step
    while found == step:
        found = 0
        url = site.linksearch_address(link,limit=step,offset=offset)
        wikipedia.output(u'Querying [[Special:Linksearch]]...')
        data = site.getUrl(url)
        for elM in elRX.finditer(data):
            found += 1
            yield wikipedia.Page(site,elM.group(1))
        offset += step

class GoogleSearchPageGenerator:
    '''
    To use this generator, you must install the pyGoogle module from
    http://pygoogle.sf.net/ and get a Google Web API license key from
    http://www.google.com/apis/index.html . The google_key must be set to your
    license key in your configuration.
    '''
    def __init__(self, query = None):
        self.query = query or wikipedia.input(u'Please enter the search query:')
    
    def queryGoogle(self, query):
        import google
        google.LICENSE_KEY = config.google_key
        offset = 0
        estimatedTotalResultsCount = None
        while not estimatedTotalResultsCount or offset < estimatedTotalResultsCount:
            while (True):
                # Google often yields 502 errors. 
                try:
                    wikipedia.output(u'Querying Google, offset %i' % offset)
                    data = google.doGoogleSearch(query, start = offset, filter = False)
                    break
                except:
                    # SOAPpy.Errors.HTTPError or SOAP.HTTPError (502 Bad Gateway)
                    # can happen here, depending on the module used. It's not easy
                    # to catch this properly because pygoogle decides which one of
                    # the soap modules to use.
                    wikipedia.output(u"An error occured. Retrying in 10 seconds...")
                    time.sleep(10)
                    continue

            for result in data.results:
                #print 'DBG: ', result.URL
                yield result.URL
            # give an estimate of pages to work on, but only once.
            if not estimatedTotalResultsCount:
                wikipedia.output(u'Estimated total result count: %i pages.' % data.meta.estimatedTotalResultsCount)
            estimatedTotalResultsCount = data.meta.estimatedTotalResultsCount
            #print 'estimatedTotalResultsCount: ', estimatedTotalResultsCount
            offset += 10
        
    def __iter__(self):
        site = wikipedia.getSite()
        # restrict query to local site
        localQuery = '%s site:%s' % (self.query, site.hostname())
        base = 'http://%s%s' % (site.hostname(), site.nice_get_address(''))
        for url in self.queryGoogle(localQuery):
            if url[:len(base)] == base:
                title = url[len(base):]
                page = wikipedia.Page(site, title)
                yield page

def MySQLPageGenerator(query):
    '''

    '''
    import MySQLdb as mysqldb
    site = wikipedia.getSite()
    conn = mysqldb.connect(config.db_hostname, db = site.dbName(),
                           user = config.db_username,
                           passwd = config.db_password)
    cursor = conn.cursor()
    wikipedia.output(u'Executing query:\n%s' % query)
    query = query.encode(site.encoding())
    cursor.execute(query)
    while True:
        try:
            namespaceNumber, pageName = cursor.fetchone()
            print namespaceNumber, pageName
        except TypeError:
            # Limit reached or no more results
            break
        #print pageName
        if pageName:
            namespace = site.namespace(namespaceNumber)
            pageName = unicode(pageName, site.encoding())
            if namespace:
                pageTitle = '%s:%s' % (namespace, pageName)
            else:
                pageTitle = pageName
            page = wikipedia.Page(site, pageTitle)
            yield page

def YearPageGenerator(start = 1, end = 2050):
    wikipedia.output(u"Starting with year %i" % start)
    for i in xrange(start, end + 1):
        if i % 100 == 0:
            wikipedia.output(u'Preparing %i...' % i)
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(wikipedia.getSite().lang, i )
            yield wikipedia.Page(wikipedia.getSite(), current_year)

def DayPageGenerator(startMonth=1, endMonth=12):
    fd = date.FormatDate(wikipedia.getSite())
    firstPage = wikipedia.Page(wikipedia.getSite(), fd(startMonth, 1))
    wikipedia.output(u"Starting with %s" % firstPage.aslink())
    for month in xrange(startMonth, endMonth+1):
        for day in xrange(1, date.getNumberOfDaysInMonth(month)+1):
            yield wikipedia.Page(wikipedia.getSite(), fd(month, day))

def NamespaceFilterPageGenerator(generator, namespaces):
    """
    Wraps around another generator. Yields only those pages that are in a list
    of specific namespace.
    """
    for page in generator:
        if page.namespace() in namespaces:
            yield page

def RedirectFilterPageGenerator(generator):
    """
    Wraps around another generator. Yields only those pages that are not redirects.
    """
    for page in generator:
        if not page.isRedirectPage():
            yield page

def CombinedPageGenerator(generators):
    """
    Wraps around a list of other generators. Yields all pages generated by the
    first generator; when the first generator stops yielding pages, yields those
    generated by the second generator, etc.
    """
    for generator in generators:
        for page in generator:
            yield page

def CategoryGenerator(generator):
    """
    Wraps around another generator. Yields the same pages, but as Category
    objects instead of Page objects. Makes sense only if it is ascertained
    that only categories are being retrieved.
    """
    for page in generator:
        yield catlib.Category(page.site(), page.title())

def PageWithTalkPageGenerator(generator):
    """
    Wraps around another generator. Yields the same pages, but for non-talk pages, it
    also includes associated talk pages.
    This generator does not check if the talk page in fact exists.
    """
    for page in generator:
        yield page
        if not page.isTalkPage():
            yield page.toggleTalkPage()

def PreloadingGenerator(generator, pageNumber=60):
    """
    Yields the same pages as generator generator. Retrieves 60 pages (or another
    number specified by Page Number), loads them using Special:Export, and yields
    them one after the other. Then retrieves more pages, etc. Thus, it is not necessary
    to load each page separately.
    """

    def preload(pages):
        try:
            site = pages[0].site()
            wikipedia.getall(site, pages, throttle=False)
        except IndexError:
            # Can happen if the pages list is empty. Don't care.
            pass
        except wikipedia.SaxError:
            # Ignore this error, and get the pages the traditional way later.
            pass

    # this array will contain up to pageNumber pages and will be flushed
    # after these pages have been preloaded and yielded.
    somePages = []
    for page in generator:
        somePages.append(page)
        # We don't want to load too many pages at once using XML export.
        # We only get a maximum number at a time.
        if len(somePages) >= pageNumber:
            preload(somePages)
            for refpage in somePages:
                yield refpage
            somePages = []
    if somePages:
        # preload remaining pages
        preload(somePages)
        for refpage in somePages:
            yield refpage

class GeneratorFactory:
    """
    This factory is responsible for processing command line arguments
    that are used many scripts and that determine on which pages
    to work on.
    """
    def __init__(self):
        pass

    def handleArg(self, arg):
        if arg.startswith('-filelinks'):
            if len(arg) == 10:
                fileLinksPageTitle = wikipedia.input(u'Links to which image page should be processed?')
            else:
                fileLinksPageTitle = arg[11:]
            fileLinksPage = wikipedia.Page(wikipedia.getSite(), 'Image:' + fileLinksPageTitle)
            return FileLinksGenerator(fileLinksPage)
        elif arg.startswith('-unusedfiles'):
            if len(arg) == 12:
                return UnusedFilesGenerator()
            else:
                return UnusedFilesGenerator(number = int(arg[13:]))
        elif arg.startswith('-file'):
            if len(arg) == 5:
                textfilename = wikipedia.input(u'Please enter the local file name:')
            else:
                textfilename = arg[6:]
            return TextfilePageGenerator(textfilename)
        elif arg.startswith('-cat'):
            if len(arg) == 4:
                categoryname = wikipedia.input(u'Please enter the category name:')
            else:
                categoryname = arg[5:]
            cat = catlib.Category(wikipedia.getSite(), 'Category:%s' % categoryname)
            return CategorizedPageGenerator(cat)
        elif arg.startswith('-subcat'):
            if len(arg) == 7:
                categoryname = wikipedia.input(u'Please enter the category name:')
            else:
                categoryname = arg[8:]
            cat = catlib.Category(wikipedia.getSite(), 'Category:%s' % categoryname)
            return CategorizedPageGenerator(cat, recurse = True)
        elif arg.startswith('-ref'):
            if len(arg) == 4:
                referredPageTitle = wikipedia.input(u'Links to which page should be processed?')
            else:
                referredPageTitle = arg[5:]
            referredPage = wikipedia.Page(wikipedia.getSite(), referredPageTitle)
            return ReferringPageGenerator(referredPage)
        elif arg.startswith('-links'):
            if len(arg) == 6:
                linkingPageTitle = wikipedia.input(u'Links from which page should be processed?')
            else:
                linkingPageTitle = arg[7:]
            linkingPage = wikipedia.Page(wikipedia.getSite(), linkingPageTitle)
            return LinkedPageGenerator(linkingPage)
        elif arg.startswith('-start'):
            if len(arg) == 6:
                firstPageTitle = wikipedia.input(u'At which page do you want to start?')
            else:
                firstPageTitle = arg[7:]
            namespace = wikipedia.Page(wikipedia.getSite(), firstPageTitle).namespace()
            firstPageTitle = wikipedia.Page(wikipedia.getSite(), firstPageTitle).titleWithoutNamespace()
            return AllpagesPageGenerator(firstPageTitle, namespace)
        elif arg.startswith('-new'):
            if len(arg) >=5:
              return NewpagesPageGenerator(number = int(arg[5:]))
            else:
              return NewpagesPageGenerator(number = 60)
        elif arg.startswith('-uncat'):
            if len(arg) >=7:
              return UnCategorizedPageGenerator(number = int(arg[7:]))
            else:
              return UnCategorizedPageGenerator(number = 60)
        elif arg.startswith('-google'):
            if len(arg) == 8:
                googleQuery = wikipedia.input(u'What do you want to search for?')
            else:
                googleQuery = arg[8:]
            return GoogleSearchPageGenerator(googleQuery)
        else:
            return None

# This class was written before GeneratorFactory. It was intended for the same
# purpose, but it is not used anywhere.
class CommandLineGenerator(object):
    """Make a generator by parsing command line arguments."""
    def __init__(self):
        self.genclass = None
        self.start = None

    def setClass(self, newclass, **kw):
        if self.genclass != None:
            print "ERROR: More than one page generator specified on command line"
            sys.exit(1)
        self.genclass = (newclass, kw)
        self.start = None

    def handleArgs(self, args):
        unhandledArgs = []
        for arg in args:
            if arg == '-newpages':
                self.setClass(NewpagesPageGenerator)
            elif arg == '-allpages':
                self.setClass(AllpagesPageGenerator)
            elif arg.startswith('-start:'):
                self.start = arg[7:]
            elif arg.startswith('-pageprefix:'):
                self.setClass(PrefixingPageGenerator, prefix=arg[12:])
            elif arg.startswith('-filelinks:'):
                page = wikipedia.Page(None, arg[11:])
                self.setClass(FileLinksGenerator, referredPage=page)
            elif arg.startswith('-incat:'):
                cat = catlib.Category(None, arg[7:])
                self.setClass(CategorizedPageGenerator, cat=cat, recurse=False)
            elif arg.startswith('-insubcat:'):
                cat = catlib.Category(None, arg[10:])
                self.setClass(CategorizedPageGenerator, cat=cat, recurse=True)
            elif arg.startswith('-referringto:'):
                page = wikipedia.Page(None, arg[13:])
                self.setClass(ReferringPageGenerator, referredPage=page)
            elif arg.startswith('-google:'):
                self.setClass(GoogleSearchPageGenerator, query = arg[8:])
            else:
                unhandledArgs.append(arg)
        return unhandledArgs

    def get(self):
        """Generate an instance of the class"""
        if self.genclass:
            cl = self.genclass[0]
            kw = self.genclass[1]
        else:
            cl = None
            kw = {}
        # Add the start argument to the keyword arguments
        if self.start:
            kw['start'] = self.start
            # The start argument can be used without an explicit
            # class. In that case use the allpages generator.
            if cl is None:
                cl = AllpagesPageGenerator
        if cl:
            return cl(**kw)
        else:
            return None

if __name__ == "__main__":
    try:
        genFactory = GeneratorFactory()
        for arg in wikipedia.handleArgs():
            generator = genFactory.handleArg(arg)
            if generator:
                gen = generator
        for page in gen:
            wikipedia.output(page.title(), toStdout = True)
        # This test code did not work. --Daniel
        #clg = CommandLineGenerator()
        #args = wikipedia.handleArgs()
        #args = clg.handleArgs(args)
        #for arg in args:
            #wikipedia.output("WARNING: Unhandled argument %s" % arg)
        #g = clg.get()
        #i = 0
        #for p in g:
            #i += 1
            #if i > 100:
                #break
            #print p
    finally:
        wikipedia.stopme()

