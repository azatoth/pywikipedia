#!/usr/bin/python
# -*- coding: utf-8  -*-

__version__='$Id$'

# Standard library imports
import re, codecs, sys
import urllib, time

# Application specific imports
import wikipedia, date, catlib
import config

class AllpagesPageGenerator:
    '''
    Using the Allpages special page, retrieves all articles, loads them (60 at
    a time) using XML export, and yields title/text pairs.
    '''
    def __init__(self, start ='!', namespace = None):
        self.start = start
        if namespace==None:
            self.namespace = wikipedia.Page(wikipedia.getSite(),start).namespace()
        else:
            self.namespace = namespace

    def __iter__(self):
        for page in wikipedia.getSite().allpages(start = self.start, namespace = self.namespace):
            yield page

class PrefixingPageGenerator:
    '''
    Gets all pages starting with a certain text. This is the same functionality as
    the prefixindex special page, but it actually uses allpages because that was
    easier to program
    '''
    def __init__(self, prefix):
        self.prefix = prefix

    def __iter__(self):
        for page in AllpagesPageGenerator(self.prefix):
            if page.title().startswith(self.prefix):
                yield page
            else:
                break

class NewpagesPageGenerator:
    '''
    Gets the latest pages. If repeat is true, after having gotten the last
    <number> pages, it loads the newpages page again to see if there are
    any new pages.
    '''
    def __init__(self, number = 100, repeat = False, site = None):
        self.number = number
        self.repeat = repeat
        if site:
            self.site = site
        else:
            self.site = wikipedia.getSite()

    def __iter__(self):
        for page in self.site.newpages(number = self.number, repeat = self.repeat):
            yield page[0]

class FileLinksGenerator:
    def __init__(self, referredPage):
        self.referredPage = referredPage

    def __iter__(self):
        for page in self.referredPage.getFileLinks():
            yield page

class ReferringPageGenerator:
    '''
    Yields all pages referring to a specific page.
    '''
    def __init__(self, referredPage, followRedirects = False, withTemplateInclusion = True, onlyTemplateInclusion = False):
        self.referredPage = referredPage
        self.followRedirects = followRedirects
        self.withTemplateInclusion = withTemplateInclusion
        self.onlyTemplateInclusion = onlyTemplateInclusion

    def __iter__(self):
        for page in self.referredPage.getReferences(follow_redirects = self.followRedirects, withTemplateInclusion = self.withTemplateInclusion, onlyTemplateInclusion = self.onlyTemplateInclusion):
            yield page

class ReferringPagesGenerator:
    '''
    Yields all pages referring to a list of specific pages.
    '''
    def __init__(self, referredPages, followRedirects = False, withTemplateInclusion = True, onlyTemplateInclusion = False):
        self.referredPages = referredPages
        self.followRedirects = followRedirects
        self.withTemplateInclusion = withTemplateInclusion
        self.onlyTemplateInclusion = onlyTemplateInclusion

    def __iter__(self):
	allPages = []
	for referredPage in self.referredPages:
            for page in referredPage.getReferences(follow_redirects = self.followRedirects, withTemplateInclusion = self.withTemplateInclusion, onlyTemplateInclusion = self.onlyTemplateInclusion):
		allPages.append(page)

	#Remove duplicate pages.
	allPages = list(set(allPages))
        wikipedia.output(u'Page generator found %s pages.' % len(allPages))

	for page in allPages:
            yield page


class CategorizedPageGenerator:
    '''
    Yields all pages in a specific category.
    If recurse is True, pages in subcategories are included as well.
    If start has a value, only pages whose title comes after start
    alphabetically are included.
    '''
    def __init__(self, category, recurse = False, start='!'):
        self.category = category
        self.recurse = recurse
        self.start = start

    def __iter__(self):
        for page in self.category.articles(recurse = self.recurse):
            if page.title() >= self.start:
                yield page

class CategoryPartPageGenerator:
    '''
    Yields 200 pages in a category; for categories with 1000s of articles
    CategorizedPageGenerator is too slow.
    '''
    # The code is based on _make_catlist in catlib.py; probably the two should
    # be merged, with this generator being moved to catlib.py and _make_catlist
    # using it.
    def __init__(self, category, start = None):
        self.category = category
        self.start = start
        self.site = category.site()

    def __iter__(self):
        if self.site.version() < "1.4":
            Rtitle = re.compile('title\s?=\s?\"([^\"]*)\"')
        else:
            Rtitle = re.compile('/\S*(?: title\s?=\s?)?\"([^\"]*)\"')
        RLinkToNextPage = re.compile('&amp;from=(.*?)" title="');
        while True:
            self.path = self.site.get_address(self.category.urlname())
            if self.start:
                self.path = self.path + '&from=%s'%urllib.quote(self.start)
                wikipedia.output(u'Getting [[%s]] starting at %s...' % (self.category.title(), self.start))
            else:
                wikipedia.output(u'Getting [[%s]...' % self.category.title())
            txt = self.site.getUrl(self.path)
            self_txt = txt
            # index where subcategory listing begins
            # this only works for the current version of the MonoBook skin
            ibegin = txt.index('"clear:both;"')
            # index where article listing ends
            try:
                iend = txt.index('<div class="printfooter">')
            except ValueError:
                try:
                    iend = txt.index('<div id="catlinks">')
                except ValueError:
                    iend = txt.index('<!-- end content -->')
            txt = txt[ibegin:iend]
            for title in Rtitle.findall(txt):
                page = wikipedia.Page(self.site, title)
                if page.namespace() != 14:
                    yield page
            matchObj = RLinkToNextPage.search(txt)
            if matchObj:
                self.start = matchObj.group(1)
            else:
                break

class LinkedPageGenerator:
    '''
    Yields all pages linked from a specific page.
    '''
    def __init__(self, linkingPage):
        self.linkingPage = linkingPage

    def __iter__(self):
        for page in self.linkingPage.linkedPages():
            yield page

class TextfilePageGenerator:
    '''
    Read a file of page links between double-square-brackets, and return
    them as a list of Page objects. filename is the name of the file that
    should be read. If no name is given, the generator prompts the user.
    '''
    def __init__(self, filename = None):
        self.filename = filename or wikipedia.input(u'Please enter the filename:')

    def __iter__(self):
        site = wikipedia.getSite()
        f = codecs.open(self.filename, 'r', config.textfile_encoding)
        R = re.compile(ur'\[\[(.+?)\]\]')
        for pageTitle in R.findall(f.read()):
            parts = pageTitle.split(':')
            i = 0
            try:
                fam = wikipedia.Family(parts[i], fatal = False)
                i += 1
            except:
                fam = site.family
            if parts[i] in fam.langs:
                code = parts[i]
                i += 1
            else:
                code = site.lang
            pagename = ':'.join(parts[i:])
            site = wikipedia.getSite(code = code, fam = fam)
            yield wikipedia.Page(site, pagename)
        f.close()

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

class MySQLPageGenerator:
    '''

    '''
    def __init__(self, query):
        self.query = query
    
    def __iter__(self):
        import MySQLdb as mysqldb
        mysite = wikipedia.getSite()
        conn = mysqldb.connect(config.db_hostname, db = mysite.dbName(), user = config.db_username, passwd = config.db_password)
        cursor = conn.cursor()
        print repr(self.query)
        wikipedia.output(u'Executing query:\n%s' % self.query)
        self.query = self.query.encode(wikipedia.getSite().encoding())
        cursor.execute(self.query)
        while True:
            try:
                namespaceNumber, pageName = cursor.fetchone()
                print namespaceNumber, pageName
            except TypeError:
                # Limit reached or no more results
                break
            #print pageName
            if pageName:
                namespace = mysite.namespace(namespaceNumber)
                pageName = unicode(pageName, mysite.encoding())
                if namespace:
                    pageTitle = '%s:%s' % (namespace, pageName)
                else:
                    pageTitle = pageName
                page = wikipedia.Page(mysite, pageTitle)
                yield page

class YearPageGenerator:
    def __init__(self, start = 1, end = 2050):
        self.start = start
        self.end = end

    def __iter__(self):
        wikipedia.output(u"Starting with year %i" % self.start)
        for i in range(self.start, self.end + 1):
            if i % 100 == 0:
                wikipedia.output(u'Preparing %i...' % i)
            # There is no year 0
            if i != 0:
                current_year = date.formatYear(wikipedia.getSite().lang, i )
                yield wikipedia.Page(wikipedia.getSite(), current_year)

class DayPageGenerator:
    def __init__(self, startMonth = 1, endMonth = 12):
        self.startMonth = startMonth
        self.endMonth = endMonth

    def __iter__(self):
        fd = date.FormatDate(wikipedia.getSite())
        firstPage = wikipedia.Page(wikipedia.getSite(), fd(self.startMonth, 1))
        wikipedia.output(u"Starting with %s" % firstPage.aslink())
        for month in range(self.startMonth, self.endMonth+1):
            for day in range(1, date.getNumberOfDaysInMonth(month)+1):
                yield wikipedia.Page(wikipedia.getSite(), fd(month, day))

class NamespaceFilterPageGenerator:
    """
    Wraps around another generator. Yields only those pages that are in a list
    of specific namespace.
    """
    def __init__(self, generator, namespaces):
        """
        Parameters:
            * generator - the page generator around which this filter is
                          wrapped.
            * namespace - a list of namespace numbers.
        """
        self.generator = generator
        self.namespaces = namespaces

    def __iter__(self):
        for page in self.generator:
            if page.namespace() in self.namespaces:
                yield page

class RedirectFilterPageGenerator:
    """
    Wraps around another generator. Yields only those pages that are not redirects.
    """
    def __init__(self, generator):
        self.generator = generator

    def __iter__(self):
        for page in self.generator:
            if not page.isRedirectPage():
                yield page

class CombinedPageGenerator:
    """
    Wraps around a list of other generators. Yields all pages generated by the
    first generator; when the first generator stops yielding pages, yields those
    generated by the second generator, etc.
    """
    def __init__(self, generators):
        self.generators = generators

    def __iter__(self):
        for generator in self.generators:
            for page in generator:
                yield page

class CategoryGenerator:
    """
    Wraps around another generator. Yields the same pages, but as Category
    objects instead of Page objects. Makes sense only if it is ascertained
    that only categories are being retrieved.
    """
    def __init__(self, generator):
        self.generator = generator
    def __iter__(self):
        for page in self.generator:
            yield catlib.Category(page.site(),page.title())

class PreloadingGenerator:
    """
    Wraps around another generator. Retrieves as many pages as stated by pageNumber
    from that generator, loads them using Special:Export, and yields them one after
    the other. Then retrieves more pages, etc.
    """
    def __init__(self, generator, pageNumber=60):
        self.generator = generator
        self.pageNumber = pageNumber

    def preload(self, pages):
        try:
            site = pages[0].site()
            wikipedia.getall(site, pages, throttle=False)
        except IndexError:
            # Can happen if the pages list is empty. Don't care.
            pass
        except wikipedia.SaxError:
            # Ignore this error, and get the pages the traditional way later.
            pass

    def __iter__(self):
        # this array will contain up to pageNumber pages and will be flushed
        # after these pages have been preloaded and yielded.
        somePages = []
        i = 0
        for page in self.generator:
            i += 1
            somePages.append(page)
            # We don't want to load too many pages at once using XML export.
            # We only get a maximum number at a time.
            if i >= self.pageNumber:
                self.preload(somePages)
                for refpage in somePages:
                    yield refpage
                i = 0
                somePages = []
        if len(somePages) > 0:
            # preload remaining pages
            self.preload(somePages)
            for refpage in somePages:
                yield refpage

class CommandLineGenerator(object):
    """Make a generator by parsing command line arguments."""
    def __init__(self):
        self.genclass = None

    def setClass(self, newclass, **kw):
        if self.genclass != None:
            print "ERROR: More than one page generator specified on command line"
            sys.exit(1)
        self.genclass = (newclass, kw)
        self.start = None
              
    def handleArgs(self, args):
        unhandledArgs = []
        for arg in args:
            if args == '-newpages':
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
    clg = CommandLineGenerator()
    args = wikipedia.handleArgs()
    args = clg.handleArgs(args)
    for arg in args:
        wikipedia.output("WARNING: Unhandled argument %s" % arg)
    g = clg.get()
    i = 0
    for p in g:
        i += 1
        if i > 100:
            break
        print p
        
