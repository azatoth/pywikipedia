"""
Library to work with category pages on Wikipedia
"""
#
# (C) Rob W.W. Hooft, Andre Engels, 2004
#
# Distribute under the terms of the PSF license.
# 
__version__ = '$Id$'
#
import re, time
import wikipedia

class CatTitleRecognition(object):
    """Special object to recognize categories in a certain language.

       Purpose is to construct an object using a language code, and
       to call the object as a function to see whether a title represents
       a category page.
    """
    def __init__(self, site):
        self.ns = site.category_namespaces()

    def __call__(self, s):
        """True if s points to a category page."""
        # try different possibilities for namespaces
        # (first letter lowercase, English 'category')
        for ins in self.ns:
            if s.startswith(ins + ':'):
                return True
        return False
        
iscattitle = CatTitleRecognition(wikipedia.getSite())

def unique(l):
    """Given a list of hashable object, return an alphabetized unique list.
    """
    l=dict.fromkeys(l).keys()
    l.sort()
    return l
    
class _CatLink(wikipedia.PageLink):
    """Subclass of PageLink that has some special tricks that only work for
       category: pages"""
    
    def catlist(self, recurse = False):
        """Cache result of make_catlist for a second call

           This should not be used outside of this module.
        """
        if recurse:
            if not hasattr(self,'_catlistT'):
                self._catlistT = self._make_catlist(True)
            return self._catlistT
        else:
            if not hasattr(self,'_catlistF'):
                self._catlistF = self._make_catlist(False)
            return self._catlistF
            
    def _make_catlist(self, recurse = False, site = None):
        """Make a list of all articles and categories that are in this
           category. If recurse is set to True, articles and categories
           of any subcategories are also retrieved.

           Returns a non-unique list of page titles in random order.

           This should not be used outside of this module.
        """
        if site is None:
            site = wikipedia.getSite()
        import re
        Rtitle = re.compile('title=\n?\"([^\"]*)\"')
        ns = wikipedia.family.category_namespaces(site)
        catsdone = []
        catstodo = [self]
        pages = []
        while catstodo:
            cat = catstodo.pop()
            catsdone.append(cat)
            # this loop will run until the page could be retrieved
            # Try to retrieve the page until it was successfully loaded (just in case
            # the server is down or overloaded)
            # wait for retry_idle_time minutes (growing!) between retries.
            retry_idle_time = 1
            while True:
                try:
                    txt = wikipedia.getPage(cat.code(), cat.urlname(), get_edit_page = False)
                except:
                    # We assume that the server is down. Wait some time, then try again.
                    print "WARNING: There was a problem retrieving %s. Maybe the server is down. Retrying in %d minutes..." % (cat.linkname(), retry_idle_time)
                    time.sleep(retry_idle_time * 60)
                    # Next time wait longer, but not longer than half an hour
                    retry_idle_time *= 2
                    if retry_idle_time > 30:
                        retry_idle_time = 30
                    continue
                break
            
            # save a copy of this text to find out self's supercategory.
            # if recurse is true, this function should only return self's
            # supercategory, not the ones of its subcats.
            self_txt = txt
            # index where subcategory listing begins
            # this only works for the current version of the MonoBook skin
            ibegin = txt.index('"clear:both;"')
            # index where article listing ends
            iend = txt.index('<!-- end content -->')
            txt = txt[ibegin:iend]
            for title in Rtitle.findall(txt):
                if iscattitle(title):
                    ncat = _CatLink(self.code(), title)
                    if recurse and ncat not in catsdone:
                        catstodo.append(ncat)
                pages.append(title)
        # get supercategories
        supercats=[]
        try:
            ibegin = self_txt.index('<div id="catlinks">')
            iend = self_txt.index('<!-- end content -->')
        except ValueError:
            # no supercategories found
            pass
        else:
            self_txt = self_txt[ibegin:iend]
            Rsupercat = re.compile('title ="([^"]*)"')
            for title in Rsupercat.findall(self_txt):
                # There might be a link to Special:Categories we don't want
                if iscattitle(title):
                    supercats.append(title)
        
        return (pages, supercats)
    
    def subcategories(self, recurse = False):
        """Create a list of all subcategories of the current category.

           If recurse = True, also return subcategories of the subcategories.

           Returns a sorted, unique list of all subcategories.
        """
        subcats = []
        for title in self.catlist(recurse)[0]:
            if iscattitle(title):
                ncat = _CatLink(self.code(), title)
                subcats.append(ncat)
        return unique(subcats)
    
    #returns a list of all articles in this category
    def articles(self, recurse = False):
        """Create a list of all pages in the current category.

           If recurse = True, also return pages in all subcategories.

           Returns a sorted, unique list of all categories.
        """
        articles = []
        for title in self.catlist(recurse)[0]:
            if not iscattitle(title):
                npage = wikipedia.PageLink(self.code(), title)
                articles.append(npage)
        return unique(articles)

    def supercategories(self, recurse = False):
        """Create a list of all subcategories of the current category.

           If recurse = True, also return subcategories of the subcategories.

           Returns a sorted, unique list of all subcategories.
        """
        supercats = []
        for title in self.catlist(recurse)[1]:
            ncat = _CatLink(self.code(), title)
            supercats.append(ncat)
        return unique(supercats)
    
    
def CatLink(code, name):
    """Factory method to create category link objects from the category name"""
    # Standardized namespace
    ns = wikipedia.family.category_namespaces(code)[0]
    # Prepend it
    return _CatLink(code, "%s:%s" % (ns, name))

# Given an article which is in category old_cat, moves it to
# category new_cat. Moves subcategories of old_cat to new_cat
# as well.
# If new_cat_title is None, the category will be removed.
def change_category(article, old_cat_title, new_cat_title):
    print ''
    cats = article.categories()
    site = article.site()
    sort_key = ''
    removed = False
    for cat in cats:
        cattext = cat.linkname().split(':', 1)[1]
        if cattext == old_cat_title:
            # because a list element is removed, the iteration will skip the 
            # next element. this might lead to forgotten categories, but
            # usually each category should only appear once per article.
            cats.remove(cat)
            removed = True
        elif cattext.startswith(old_cat_title + '|'):
            sort_key = cat.catname().split('|', 1)[1]
            cats.remove(cat)
            removed = True
    if not removed:
        wikipedia.output(u'ERROR: %s is not in category %s!' % (article.aslink(), old_cat_title))
        return
    if new_cat_title != None:
        if sort_key == '':
            new_cat = CatLink(site, new_cat_title)
        else:
            new_cat = CatLink(site, new_cat_title + '|' + sort_key)
        cats.append(new_cat)
    text = article.get()
    text = wikipedia.replaceCategoryLinks(text, cats)
    article.put(text)


def test():
    site = wikipedia.getSite()
    
    pl=CatLink(site, 'Software')
    
    print pl.catlist(recurse = False)

    print pl.subcategories(recurse = False)

    print pl.articles(recurse = False)

if __name__=="__main__":
    import sys
    for arg in sys.argv[1:]:
        arg = wikipedia.argHandler(arg)
        if arg:
            print "Ignored argument", arg
    test()
