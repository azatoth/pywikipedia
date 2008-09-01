# -*- coding: utf-8 -*-
"""This bot will move pages out of redirected categories

Usage: category-redirect.py [options]

"""
__version__ = '$Id$'

import wikipedia, catlib
import pagegenerators
import simplejson
import cPickle
import math
import re
import sys, traceback
import threading, Queue
import time
from datetime import datetime, timedelta


class APIError(Exception):
    """The wiki API returned an error message."""

    def __init__(self, errordict):
        """Save error dict returned by MW API."""
        self.errors = errordict

    def __str__(self):
        return "%(code)s: %(info)s" % self.errors


class ThreadList(list):
    """A simple threadpool class to limit the number of simultaneous threads.

    Any threading.Thread object can be added to the pool using the append()
    method.  If the maximum number of simultaneous threads has not been
    reached, the Thread object will be started immediately; if not, the
    append() call will block until the thread is able to start.

    >>> pool = ThreadList(limit=10)
    >>> def work():
    ...     time.sleep(1)
    ...
    >>> for x in xrange(20):
    ...     pool.append(threading.Thread(target=work))
    ...

    """
    def __init__(self, limit=sys.maxint, *args):
        self.limit = limit
        list.__init__(self, *args)
        for item in list(self):
            if not isinstance(threading.Thread, item):
                raise TypeError("Cannot add '%s' to ThreadList" % type(item))

    def active_count(self):
        """Return the number of alive threads, and delete all non-alive ones."""
        count = 0
        for item in list(self):
            if item.isAlive():
                count += 1
            else:
                self.remove(item)
        return count

    def append(self, thd):
        if not isinstance(thd, threading.Thread):
            raise TypeError("Cannot append '%s' to ThreadList" % type(thd))
        while self.active_count() >= self.limit:
            time.sleep(2)
        list.append(self, thd)
        thd.start()


class CategoryRedirectBot(object):
    def __init__(self):
        self.cooldown = 7 # days
        self.site = wikipedia.getSite()
        self.catprefix = self.site.namespace(14)+":"
        self.result_queue = Queue.Queue()
        self.log_text = []
        self.edit_requests = []

        # Localization:

        # Category that contains all redirected category pages
        self.cat_redirect_cat = {
            'wikipedia': {
                'en': "Category:Wikipedia category redirects",
                'ar': "تصنيف:تحويلات تصنيفات ويكيبيديا",
                'no': "Kategori:Wikipedia omdirigertekategorier",
                'ja': "Category:移行中のカテゴリ",
                'simple': "Category:Category redirects",
            },
            'commons': {
                'commons': "Category:Category redirects"
            }
        }

        # List of all templates that are used to mark category redirects
        # (put the most preferred form first)
        self.redir_templates = {
            'wikipedia': {
                'en': ("Category redirect",
                       "Category redirect3",
                       "Categoryredirect",
                       "Empty category",
                       "CR",
                       "Catredirect",
                       "Emptycat",
                       "Emptycategory",
                       "Empty cat",
                       "Seecat",),
                'ar': ("تحويل تصنيف",
                       "Category redirect",
                       "تحويلة تصنيف",),
                'no': ("Kategoriomdirigering",),
                'ja': ("Category redirect",),
                'simple': ("Category redirect",
                           "Catredirect"),
                },
            'commons': {
                'commons': (u'Category redirect',
                            u'Categoryredirect',
                            u'See cat',
                            u'Seecat',
                            u'Catredirect',
                            u'Cat redirect',
                            u'CatRed',
                            u'Catredir',),
                }
            }

        self.move_comment = {
            '_default':
u"Robot: moving pages out of redirected category",
            'ar':
u"روبوت: نقل الصفحات من تصنيف محول",
            'no':
u"Robot: Flytter sider ut av omdirigeringskategori",
            'ja':
u"ロボットによる: 移行中のカテゴリからのカテゴリ変更",
            'commons':
u'Robot: Changing category link (following [[Template:Category redirect|category redirect]])'
        }

        self.redir_comment = {
            '_default':
u"Robot: adding category redirect template for maintenance",
            'ar':
u"روبوت: إضافة قالب تحويل تصنيف للصيانة",
            'ja':
u"ロボットによる: 移行中のカテゴリとしてタグ付け",
            'no':
u"Robot: Legger til vedlikeholdsmal for kategoriomdirigering",
        }

        self.dbl_redir_comment = {
            '_default': u"Robot: fixing double-redirect",
            'ar': u"روبوت: تصليح تحويلة مزدوجة",
            'ja': u"ロボットによる: 二重リダイレクト修正",
            'no': u"Robot: Ordner doble omdirigeringer",
        }

        self.maint_comment = {
            '_default': u"Category redirect maintenance bot",
            'ar': u"بوت صيانة تحويل التصنيف",
            'ja': u"移行中のカテゴリのメンテナンス・ボット",
            'no': u"Bot for vedlikehold av kategoriomdirigeringer",
        }

        self.edit_request_text = wikipedia.translate(self.site.lang,
            {'_default': u"""\
{{editprotected}}
The following protected pages have been detected as requiring updates to \
category links:
%s
--~~~~
""",
            })

        self.edit_request_item = wikipedia.translate(self.site.lang,
            {'_default': u"* %s is in %s, which is a redirect to %s",
            })


    def change_category(self, article, oldCat, newCat, comment=None,
                        sortKey=None):
        """Given an article in category oldCat, moves it to category newCat.
        Moves subcategories of oldCat as well. oldCat and newCat should be
        Category objects. If newCat is None, the category will be removed.

        This is a copy of portions of catlib.change_category() with the
        added capability to post a talk page message on pages that cannot be
        fixed due to protection.

        """
        oldtext = article.get(get_redirect=True, force=True)
        newtext = wikipedia.replaceCategoryInPlace(oldtext, oldCat, newCat)
        if newtext == oldtext:
            wikipedia.output(
                u'No changes in made in page %s.' % article.aslink())
            return False
        try:
            article.put(newtext, comment)
            return True
        except wikipedia.EditConflict:
            wikipedia.output(
                u'Skipping %s because of edit conflict' % article.aslink())
        except wikipedia.LockedPage:
            wikipedia.output(u'Skipping locked page %s' % article.aslink())
            self.edit_requests.append((article.aslink(),
                                       oldCat.aslink(textlink=True),
                                       newCat.aslink(textlink=True)))
        except wikipedia.SpamfilterError, error:
            wikipedia.output(
                u'Changing page %s blocked by spam filter (URL=%s)'
                             % (article.aslink(), error.url))
        except wikipedia.NoUsername:
            wikipedia.output(
                u"Page %s not saved; sysop privileges required."
                             % article.aslink())
            self.edit_requests.append((article.aslink(),
                                       oldCat.aslink(textlink=True),
                                       newCat.aslink(textlink=True)))
        except wikipedia.PageNotSaved, error:
            wikipedia.output(u"Saving page %s failed: %s"
                             % (article.aslink(), error.message))
        return False

    def move_contents(self, oldCatTitle, newCatTitle, editSummary):
        """The worker function that moves pages out of oldCat into newCat"""
        while True:
            try:
                oldCat = catlib.Category(self.site,
                                         self.catprefix + oldCatTitle)
                newCat = catlib.Category(self.site,
                                         self.catprefix + newCatTitle)

                # Move articles
                found, moved = 0, 0
                for result in self.query_results(list="categorymembers",
                                                 cmtitle=oldCat.title(),
                                                 cmprop="title|sortkey",
                                                 cmlimit="max"):
                    found += len(result['categorymembers'])
                    for item in result['categorymembers']:
                        article = wikipedia.Page(self.site, item['title'])
                        changed = self.change_category(article, oldCat, newCat,
                                                       comment=editSummary)
                        if changed: moved += 1

                # pass 2: look for template doc pages
                for result in self.query_results(list="categorymembers",
                                                 cmtitle=oldCat.title(),
                                                 cmprop="title|sortkey",
                                                 cmnamespace="10",
                                                 cmlimit="max"):
                    for item in result['categorymembers']:
                        doc = wikipedia.Page(self.site, item['title']+"/doc")
                        try:
                            old_text = doc.get()
                        except wikipedia.Error:
                            continue
                        changed = self.change_category(doc, oldCat, newCat,
                                                       comment=editSummary)
                        if changed: moved += 1

                if found:
                    wikipedia.output(u"%s: %s found, %s moved"
                                     % (oldCat.title(), found, moved))
                self.result_queue.put((oldCatTitle, found, moved))
                return
            except wikipedia.ServerError:
                wikipedia.output(u"Server error: retrying in 5 seconds...")
                time.sleep(5)
                continue
            except:
                self.result_queue.put((oldCatTitle, None, None))
                raise

    def readyToEdit(self, cat):
        """Return True if cat not edited during cooldown period, else False."""
        dateformat ="%Y%m%d%H%M%S"
        today = datetime.now()
        deadline = today + timedelta(days=-self.cooldown)
        if cat.editTime() is None:
            raise RuntimeError
        return (deadline.strftime(dateformat) > cat.editTime())

    def query_results(self, **data):
        """Iterate results from API action=query, using data as parameters."""
        addr = self.site.apipath()
        querydata = {'action': 'query',
                     'format': 'json',
                     'maxlag': str(wikipedia.config.maxlag)}
        querydata.update(data)
        if not querydata.has_key("action")\
                or not querydata['action'] == 'query':
            raise ValueError(
                "query_results: 'action' set to value other than 'query'"
                )
        waited = 0
        while True:
            response, data = self.site.postForm(addr, querydata)
            if data.startswith(u"unknown_action"):
                e = {'code': data[:14], 'info': data[16:]}
                raise APIError(e)
            try:
                result = simplejson.loads(data)
            except ValueError:
                # if the result isn't valid JSON, there must be a server
                # problem.  Wait a few seconds and try again
                # TODO: warn user; if the server is down, this could
                # cause an infinite loop
                wikipedia.output("Invalid API response received; retrying...")
                time.sleep(5)
                continue
            if type(result) is dict and result.has_key("error"):
                if result['error']['code'] == "maxlag":
                    print "Pausing due to server lag.\r",
                    time.sleep(5)
                    waited += 5
                    if waited % 30 == 0:
                        wikipedia.output(
                            u"(Waited %i seconds due to server lag.)"
                             % waited)
                    continue
                else:
                    # raise error
                    raise APIError(result['error'])
            waited = 0
            if type(result) is list:
                # query returned no results
                return
            assert type(result) is dict, \
                   "Unexpected result of type '%s' received." % type(result)
            assert result.has_key("query"), \
                   "No 'query' response found, result keys = %s" % result.keys()
            yield result['query']
            if result.has_key("query-continue"):
                assert len(result['query-continue'].keys()) == 1, \
                       "More than one query-continue key returned: %s" \
                       % result['query-continue'].keys()
                query_type = result['query-continue'].keys()[0]
                assert (query_type in querydata.keys()
                        or query_type in querydata.values()), \
                       "Site returned unknown query-continue type '%s'"\
                       % query_type
                querydata.update(result['query-continue'][query_type])
            else:
                return

    def run(self):
        """Run the bot"""
        user = self.site.loggedInAs()
        redirect_magicwords = ["redirect"]
        other_words = self.site.redirect()
        if other_words:
            redirect_magicwords.extend(other_words)
        problems = []

        l = time.localtime()
        today = "%04d-%02d-%02d" % l[:3]
        log_page = wikipedia.Page(self.site,
                        u"User:%(user)s/category redirect logs/%(today)s"
                          % locals())
        problem_page = wikipedia.Page(self.site,
                        u"User:%(user)s/category redirect problems" % locals())
        edit_request_page = wikipedia.Page(self.site,
                        u"User:%(user)s/category edit requests" % locals())
        datafile = wikipedia.config.datafilepath(
                        "%s-catmovebot-data" % self.site.dbName())
        try:
            inp = open(datafile, "rb")
            record = cPickle.load(inp)
            inp.close()
        except IOError:
            record = {}
        if record:
            cPickle.dump(record, open(datafile + ".bak", "wb"))

        # Set up regexes for later scanning
        template_list = self.redir_templates[self.site.family.name
                                             ][self.site.lang]
        # regex to match soft category redirects
        #  note that any templates containing optional "category:" are
        #  incorrect and will be fixed by the bot
        template_regex = re.compile(
            ur"""{{\s*(?:%(prefix)s\s*:\s*)?  # optional "template:"
                      (?:%(template)s)\s*\|   # catredir template name
                      (\s*%(catns)s\s*:\s*)?  # optional "category:"
                      ([^|}]+)                # redirect target cat
                      (?:\|[^|}]*)*}}         # optional arguments 2+, ignored
              """ % {'prefix': self.site.namespace(10).lower(),
                     'template': "|".join(item.replace(" ", "[ _]+")
                                          for item in template_list),
                     'catns': self.site.namespace(14)},
            re.I|re.X)
        # regex to match hard redirects to category pages
        catredir_regex = re.compile(
            ur'\s*#(?:%(redir)s)\s*:?\s*\[\[\s*:?%(catns)s\s*:(.*?)\]\]\s*'
                             % {'redir': "|".join(redirect_magicwords),
                                'catns': self.site.namespace(14)},
                            re.I)
        # regex to match all other hard redirects
        redir_regex = re.compile(ur"(?i)\s*#(?:%s)\s*:?\s*\[\[(.*?)\]\]"
                                  % "|".join(redirect_magicwords),
                                 re.I)

        # check for hard-redirected categories that are not already marked
        # with an appropriate template
        comment = wikipedia.translate(self.site.lang, self.redir_comment)
        for result in self.query_results(list='allpages',
                                         apnamespace='14', # Category:
                                         apfrom='!',
                                         apfilterredir='redirects',
                                         aplimit='max'):
            gen = (wikipedia.Page(self.site, page_item['title'])
                   for page_item in result['allpages'])
            for page in pagegenerators.PreloadingGenerator(gen, 120):
                text = page.get(get_redirect=True)
                if re.search(template_regex, text):
                    # this is already a soft-redirect, so skip it (for now)
                    continue
                m = catredir_regex.match(text)
                if m:
                    # this is a hard-redirect to a category page
                    newtext = (u"{{%(template)s|%(cat)s}}"
                               % {'cat': m.group(1),
                                  'template': template_list[0]})
                    try:
                        page.put(newtext, comment, minorEdit=True)
                        self.log_text.append(u"* Added {{tl|%s}} to %s"
                                         % (template_list[0],
                                            page.aslink(textlink=True)))
                    except wikipedia.Error, e:
                        self.log_text.append(
                            u"* Failed to add {{tl|%s}} to %s (%s)"
                             % (template_list[0],
                                page.aslink(textlink=True),
                                e))
                else:
                    r = redir_regex.match(text)
                    if r:
                        problems.append(
                            u"# %s is a hard redirect to [[:%s]]"
                             % (page.aslink(textlink=True),
                                r.group(1)))
                    else:
                        problems.append(
                    u"# %s is a hard redirect; unable to extract target."
                             % page.aslink(textlink=True))

        wikipedia.output("Done checking hard-redirect category pages.")

        comment = wikipedia.translate(self.site.lang, self.move_comment)
        scan_data = {
            u'action': 'query',
            u'list': 'embeddedin',
            u'einamespace': '14',   # Category:
            u'eilimit': 'max',
            u'format': 'json'
        }
        counts, destmap, catmap = {}, {}, {}
        catlist, catpages, nonemptypages = [], [], []
        target = self.cat_redirect_cat[self.site.family.name][self.site.lang]

        # get a list of all members of the category-redirect category
        for result in self.query_results(generator=u'categorymembers',
                                         gcmtitle=target,
                                         gcmnamespace=u'14', # CATEGORY
                                         gcmlimit=u'max',
                                         prop='info|categoryinfo'):
            for catdata in result['pages'].values():
                thispage = wikipedia.Page(self.site, catdata['title'])
                catpages.append(thispage)
                if 'categoryinfo' in catdata \
                        and catdata['categoryinfo']['size'] != "0":
                    # save those categories that have contents
                    nonemptypages.append(thispage)

        # preload the category pages for redirected categories
        wikipedia.output(u"")
        wikipedia.output(u"Preloading %s category redirect pages"
                         % len(catpages))
        for cat in pagegenerators.PreloadingGenerator(catpages, 120):
            cat_title = cat.titleWithoutNamespace()
            if "category redirect" in cat_title:
                self.log_text.append("* Ignoring %s%s" % (self.catprefix, cat_title))
                continue
            try:
                text = cat.get(get_redirect=True)
            except wikipedia.Error:
                self.log_text.append(u"* Could not load %s%s; ignoring"
                                 % (self.catprefix, cat_title))
                continue
            match = template_regex.search(text)
            if match is None:
                self.log_text.append(u"* False positive: %s" % cat_title)
                continue
            catlist.append(cat)
            destination = match.group(2)
            target = catlib.Category(self.site, self.catprefix+destination)
            destmap.setdefault(target, []).append(cat)
            catmap[cat] = destination
            if match.group(1):
                # category redirect target starts with "Category:" - fix it
                text = text[ :match.start(1)] + text[match.end(1): ]
                cat.put(text,
                        u"Robot: fixing category redirect parameter format")
                self.log_text.append(
                    u"* Removed category prefix from parameter in %s"
                     % cat.aslink(textlink=True))

        wikipedia.output(u"")
        wikipedia.output(u"Checking %s destination categories" % len(destmap))
        for dest in pagegenerators.PreloadingGenerator(destmap.keys(), 120):
            if not dest.exists():
                for d in destmap[dest]:
                    problems.append("# %s redirects to %s"
                                    % (d.aslink(textlink=True),
                                       dest.aslink(textlink=True)))
                    catlist.remove(d)
                    # do a null edit on d to make it appear in the
                    # "needs repair" category (if this wiki has one)
                    try:
                        d.put(d.get(get_redirect=True))
                    except:
                        pass
            if dest in catlist:
                for d in destmap[dest]:
                    # is catmap[dest] also a redirect?
                    newcat = catlib.Category(self.site,
                                             self.catprefix+catmap[dest])
                    while newcat in catlist:
                        if newcat == d or newcat == dest:
                            self.log_text.append(u"* Redirect loop from %s"
                                             % newcat.aslink(textlink=True))
                            break
                        newcat = catlib.Category(self.site,
                                                 self.catprefix+catmap[newcat])
                    else:
                        self.log_text.append(
                            u"* Fixed double-redirect: %s -> %s -> %s"
                                % (d.aslink(textlink=True),
                                   dest.aslink(textlink=True),
                                   newcat.aslink(textlink=True)))
                        oldtext = d.get(get_redirect=True)
                        # remove the old redirect from the old text,
                        # leaving behind any non-redirect text
                        oldtext = template_regex.sub("", oldtext)
                        newtext = (u"{{category redirect|%(ncat)s}}"
                                    % {'ncat': newcat.titleWithoutNamespace()})
                        newtext = newtext + oldtext.strip()
                        try:
                            d.put(newtext,
                                  wikipedia.translate(self.site.lang,
                                                      self.dbl_redir_comment),
                                  minorEdit=True)
                        except wikipedia.Error, e:
                            self.log_text.append("** Failed: %s" % str(e))

        # only scan those pages that have contents (nonemptypages)
        # and that haven't been removed from catlist as broken redirects
        cats_to_empty = set(catlist) & set(nonemptypages)
        wikipedia.output(u"")
        wikipedia.output(u"Moving pages out of %s redirected categories."
                         % len(cats_to_empty))
        thread_limit = int(math.log(len(cats_to_empty), 8) + 1)
        threadpool = ThreadList(limit=1) # temporarily disabling multi-threads

        for cat in cats_to_empty:
            cat_title = cat.titleWithoutNamespace()
            if not self.readyToEdit(cat):
                counts[cat_title] = None
                self.log_text.append(
                    u"* Skipping %s; in cooldown period."
                     % cat.aslink(textlink=True))
                continue
            threadpool.append(
                threading.Thread(target=self.move_contents,
                                 args=(cat_title, catmap[cat]),
                                 kwargs=dict(editSummary=comment)))
        while len(counts) < len(cats_to_empty):
            title, found, moved = self.result_queue.get()
            if found is None:
                self.log_text.append(
                    u"* [[:%s%s]]: error in move_contents thread"
                    % (self.catprefix, title))
            else:
                if found:
                    self.log_text.append(
                        u"* [[:%s%s]]: %d found, %d moved"
                        % (self.catprefix, title, found, moved))
            counts[title] = found

        for cat in record.keys():
            if cat not in counts.keys():
                del record[cat]
        for cat in counts.keys():
            if counts[cat] is not None:
                if counts[cat]:
                    record.setdefault(cat, {})[today] = counts[cat]
                else:
                    record.setdefault(cat, {})
        cPickle.dump(record, open(datafile, "wb"))

        wikipedia.setAction(wikipedia.translate(self.site.lang,
                                                self.maint_comment))
        log_page.put("\n".join(self.log_text))
        problem_page.put("\n".join(problems))
        if self.edit_requests:
            edit_request_page.put(self.edit_request_text
                                 % "\n".join((self.edit_request_item % item)
                                             for item in self.edit_requests))


def main(*args):
    try:
        a = wikipedia.handleArgs(*args)
        if len(a) == 1:
            raise RuntimeError('Unrecognized argument "%s"' % a[0])
        elif a:
            raise RuntimeError('Unrecognized arguments: ' +
                               " ".join(('"%s"' % arg) for arg in a))
        bot = CategoryRedirectBot()
        bot.run()
    finally:
        wikipedia.stopme()


if __name__ == "__main__":
    main()
