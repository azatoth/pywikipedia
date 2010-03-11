# -*- coding: utf-8  -*-
"""
Objects representing MediaWiki sites (wikis) and families (groups of wikis
on the same topic in different languages).
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot
from pywikibot import deprecate_arg
from pywikibot import config
from pywikibot import deprecated
from pywikibot import pagegenerators
from pywikibot.throttle import Throttle
from pywikibot.data import api
from pywikibot.exceptions import *

try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import logging
import os
import re
import sys
import threading
import time
import urllib

logger = logging.getLogger("pywiki.wiki.site")

class PageInUse(pywikibot.Error):
    """Page cannot be reserved for writing due to existing lock."""


def Family(fam=None, fatal=True):
    """Import the named family.

    @param fam: family name (if omitted, uses the configured default)
    @type fam: str
    @param fatal: if True, the bot will stop running if the given family is
        unknown. If False, it will only raise a ValueError exception.
    @param fatal: bool
    @return: a Family instance configured for the named family.

    """
    if fam == None:
        fam = config.family
    try:
        # first try the built-in families
        name = "pywikibot.families.%s_family" % fam
        __import__(name)
        myfamily = sys.modules[name]
    except ImportError:
        # next see if user has defined a local family module
        try:
            sys.path.append(config.datafilepath('families'))
            myfamily =  __import__("%s_family" % fam)
        except ImportError:
            if fatal:
                logger.exception(u"""\
Error importing the %s family. This probably means the family
does not exist. Also check your configuration file."""
                           % fam)
                sys.exit(1)
            else:
                raise Error("Family %s does not exist" % fam)
    return myfamily.Family()


class BaseSite(object):
    """Site methods that are independent of the communication interface."""
    # to implement a specific interface, define a Site class that inherits
    # from this

    def __init__(self, code, fam=None, user=None, sysop=None):
        """
        @param code: the site's language code
        @type code: str
        @param fam: wiki family name (optional)
        @type fam: str or Family
        @param user: bot user name (optional)
        @type user: str
        @param sysop: sysop account user name (optional)
        @type sysop: str

        """
        self.__code = code.lower()
        if isinstance(fam, basestring) or fam is None:
            self.__family = Family(fam, fatal=False)
        else:
            self.__family = fam

        # if we got an outdated language code, use the new one instead.
        if self.__code in self.__family.obsolete:
            if self.__family.obsolete[self.__code] is not None:
                self.__code = self.__family.obsolete[self.__code]
            else:
                # no such language anymore
                raise NoSuchSite("Language %s in family %s is obsolete"
                                 % (self.__code, self.__family.name))
        if self.__code not in self.languages():
            if self.__code == 'zh-classic' \
                    and 'zh-classical' in self.languages():
                self.__code = 'zh-classical'
                # database hack (database is varchar[10], so zh-classical
                # is cut to zh-classic)
            elif self.__family.name in self.__family.langs.keys() \
                    or len(self.__family.langs) == 1:
                oldcode = self.__code
                self.__code = self.__family.name
                if self.__family == pywikibot.config.family \
                        and oldcode == pywikibot.config.mylang:
                    pywikibot.config.mylang = self.__code
            else:
                raise NoSuchSite("Language %s does not exist in family %s"
                                 % (self.__code, self.__family.name))

        self._username = [user, sysop]
        self.nocapitalize = self.code in self.family.nocapitalize

        # following are for use with lock_page and unlock_page methods
        self._pagemutex = threading.Lock()
        self._locked_pages = []

    @property
    def throttle(self):
        """Return this Site's throttle.  Initialize a new one if needed."""

        if not hasattr(self, "_throttle"):
            self._throttle = Throttle(self, multiplydelay=True,
                                      verbosedelay=True)
        return self._throttle

    @property
    def family(self):
        """The Family object for this Site's wiki family."""

        return self.__family

    @property
    def code(self):
        """The identifying code for this Site."""

        return self.__code

    @property
    def lang(self):
        """The ISO language code for this Site.

        Presumed to be equal to the wiki prefix, but this can be overridden.

        """
        return self.__code

    def __cmp__(self, other):
        """Perform equality and inequality tests on Site objects."""

        if not isinstance(other, BaseSite):
            return 1
        if self.family == other.family:
            return cmp(self.code, other.code)
        return cmp(self.family.name, other.family.name)

    def user(self):
        """Return the currently-logged in bot user, or None."""

        if self.logged_in(True):
            return self._username[True]
        elif self.logged_in(False):
            return self._username[False]
        return None

    def username(self, sysop = False):
        return self._username[sysop]

    def __getattr__(self, attr):
        """Calls to methods not defined in this object are passed to Family."""

        if hasattr(self.__class__, attr):
            return getattr(self.__class__, attr)
        try:
            method = getattr(self.family, attr)
            f = lambda *args, **kwargs: \
                       method(self.code, *args, **kwargs)
            if hasattr(method, "__doc__"):
                f.__doc__ = method.__doc__
            return f
        except AttributeError:
            raise AttributeError("%s instance has no attribute '%s'"
                                 % (self.__class__.__name__, attr)  )

    def sitename(self):
        """Return string representing this Site's name and language."""

        return self.family.name+':'+self.code

    __str__ = sitename

    def __repr__(self):
        return 'Site("%s", "%s")' % (self.code, self.family.name)

    def __hash__(self):
        return hash(repr(self))

    def linktrail(self):
        """Return regex for trailing chars displayed as part of a link.

        Returns a string, not a compiled regular expression object.

        This reads from the family file, and ''not'' from
        [[MediaWiki:Linktrail]], because the MW software currently uses a
        built-in linktrail from its message files and ignores the wiki
        value.

        """
        return self.family.linktrail(self.code)

    def languages(self):
        """Return list of all valid language codes for this site's Family."""

        return self.family.langs.keys()

    def validLanguageLinks(self):
        """Return list of language codes that can be used in interwiki links."""

        nsnames = [name for name in self.namespaces().itervalues()]
        return [lang for lang in self.languages()
                     if lang[:1].upper() + lang[1:] not in nsnames]

    def ns_index(self, namespace):
        """Given a namespace name, return its int index, or None if invalid."""

        for ns in self.namespaces():
            if namespace.lower() in [name.lower()
                                     for name in self.namespaces()[ns]]:
                return ns
        return None

    getNamespaceIndex = ns_index  # for backwards-compatibility

    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""

        return self._namespaces

    def ns_normalize(self, value):
        """Return canonical local form of namespace name.

        @param value: A namespace name
        @type value: unicode

        """
        index = self.ns_index(value)
        return self.namespace(index)

    normalizeNamespace = ns_normalize  # for backwards-compatibility

    def redirect(self, default=True):
        """Return list of localized redirect tags for the site.

        If default is True, falls back to 'REDIRECT' if the site has no
        special redirect tag.

        """
        return [u"REDIRECT"]

    def pagenamecodes(self, default=True):
        """Return list of localized PAGENAME tags for the site."""
        return [u"PAGENAME"]

    def pagename2codes(self, default=True):
        """Return list of localized PAGENAMEE tags for the site."""
        return [u"PAGENAMEE"]

    def lock_page(self, page, block=True):
        """Lock page for writing.  Must be called before writing any page.

        We don't want different threads trying to write to the same page
        at the same time, even to different sections.

        @param page: the page to be locked
        @type page: pywikibot.Page
        @param block: if true, wait until the page is available to be locked;
            otherwise, raise an exception if page can't be locked

        """
        self._pagemutex.acquire()
        try:
            while page in self._locked_pages:
                if not block:
                    raise PageInUse
                time.sleep(.25)
            self._locked_pages.append(page.title(withSection=False))
        finally:
            self._pagemutex.release()

    def unlock_page(self, page):
        """Unlock page.  Call as soon as a write operation has completed.

        @param page: the page to be locked
        @type page: pywikibot.Page

        """
        self._pagemutex.acquire()
        try:
            self._locked_pages.remove(page.title(withSection=False))
        finally:
            self._pagemutex.release()

    def disambcategory(self):
        """Return Category in which disambig pages are listed."""

        try:
            name = self.namespace(14)+':'+self.family.disambcatname[self.code]
        except KeyError:
            raise Error(u"No disambiguation category name found for %(site)s"
                         % {'site': self})
        return pywikibot.Category(pywikibot.Link(name, self))

    @deprecated("pywikibot.Link")
    def linkto(self, title, othersite = None):
        """Return unicode string in the form of a wikilink to 'title'

        Use optional Site argument 'othersite' to generate an interwiki link.

        """
        return pywikibot.Link(title, self).astext(othersite)

    def isInterwikiLink(self, s):
        """Return True if s is in the form of an interwiki link.

        If a link object constructed using "s" as the link text parses as
        belonging to a different site, this method returns True.

        """
        return (pywikibot.Link(s, self).site != self)

    def redirectRegex(self, pattern=None):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        if pattern is None:
            pattern = "REDIRECT"
        # A redirect starts with hash (#), followed by a keyword, then
        # arbitrary stuff, then a wikilink. The wikilink may contain
        # a label, although this is not useful.
        return re.compile(r'\s*#%(pattern)s\s*:?\s*\[\[(.+?)(?:\|.*?)?\]\]'
                           % locals(),
                          re.IGNORECASE | re.UNICODE | re.DOTALL)

    # namespace shortcuts for backwards-compatibility

    def special_namespace(self):
        return self.namespace(-1)

    def image_namespace(self):
        return self.namespace(6)

    def mediawiki_namespace(self):
        return self.namespace(8)

    def template_namespace(self):
        return self.namespace(10)

    def category_namespace(self):
        return self.namespace(14)

    def category_namespaces(self):
        return self.namespace(14, all=True)

    # site-specific formatting preferences

    def category_on_one_line(self):
        """Return True if this site wants all category links on one line."""

        return self.code in self.family.category_on_one_line

    def interwiki_putfirst(self):
        """Return list of language codes for ordering of interwiki links."""

        return self.family.interwiki_putfirst.get(self.code, None)

    def interwiki_putfirst_doubled(self, list_of_links):
        # TODO: is this even needed?  No family in the framework has this
        # dictionary defined!
        if self.lang in self.family.interwiki_putfirst_doubled:
            if len(list_of_links) >= \
                        self.family.interwiki_putfirst_doubled[self.lang][0]:
                links2 = [lang.language() for lang in list_of_links]
                result = []
                for lang in self.family.interwiki_putfirst_doubled[self.lang][1]:
                    try:
                        result.append(list_of_links[links2.index(lang)])
                    except ValueError:
                        pass
                return result
            else:
                return False
        else:
            return False

    def getSite(self, code):
        """Return Site object for language 'code' in this Family."""

        return pywikibot.Site(code=code, fam=self.family, user=self.user())

    # deprecated methods for backwards-compatibility

    @deprecated("family attribute")
    def fam(self):
        """Return Family object for this Site."""
        return self.family

    @deprecated("urllib.urlencode()")
    def urlEncode(self, query):
        """DEPRECATED"""
        return urllib.urlencode(query)

    @deprecated("pywikibot.comms.http.request")
    def getUrl(self, path, retry=True, sysop=False, data=None,
               compress=True, no_hostname=False, cookie_only=False):
        """DEPRECATED.

        Retained for compatibility only. All arguments except path and data
        are ignored.

        """
        from pywikibot.comms import http
        if data:
            if not isinstance(data, basestring):
                data = urllib.urlencode(data)
            return http.request(self, path, method="PUT", body=data)
        else:
            return http.request(self, path)

    @deprecated()
    def postForm(self, address, predata, sysop=False, cookies=None):
        """DEPRECATED"""
        return self.getUrl(address, data=predata)

    @deprecated()
    def postData(self, address, data, contentType=None, sysop=False,
                 compress=True, cookies=None):
        """DEPRECATED"""
        return self.getUrl(address, data=data)

    # unsupported methods from version 1

    def checkCharset(self, charset):
        raise NotImplementedError
    def getToken(self, getalways=True, getagain=False, sysop=False):
        raise NotImplementedError
    def export_address(self):
        raise NotImplementedError
    def move_address(self):
        raise NotImplementedError
    def delete_address(self, s):
        raise NotImplementedError
    def undelete_view_address(self, s, ts=''):
        raise NotImplementedError
    def undelete_address(self):
        raise NotImplementedError
    def protect_address(self, s):
        raise NotImplementedError
    def unprotect_address(self, s):
        raise NotImplementedError
    def put_address(self, s):
        raise NotImplementedError
    def get_address(self, s):
        raise NotImplementedError
    def nice_get_address(self, s):
        raise NotImplementedError
    def edit_address(self, s):
        raise NotImplementedError
    def purge_address(self, s):
        raise NotImplementedError
    def block_address(self):
        raise NotImplementedError
    def unblock_address(self):
        raise NotImplementedError
    def blocksearch_address(self, s):
        raise NotImplementedError
    def linksearch_address(self, s, limit=500, offset=0):
        raise NotImplementedError
    def search_address(self, q, n=50, ns=0):
        raise NotImplementedError
    def allpages_address(self, s, ns = 0):
        raise NotImplementedError
    def log_address(self, n=50, mode = ''):
        raise NotImplementedError
    def newpages_address(self, n=50):
        raise NotImplementedError
    def longpages_address(self, n=500):
        raise NotImplementedError
    def shortpages_address(self, n=500):
        raise NotImplementedError
    def unusedfiles_address(self, n=500):
        raise NotImplementedError
    def categories_address(self, n=500):
        raise NotImplementedError
    def deadendpages_address(self, n=500):
        raise NotImplementedError
    def ancientpages_address(self, n=500):
        raise NotImplementedError
    def lonelypages_address(self, n=500):
        raise NotImplementedError
    def protectedpages_address(self, n=500):
        raise NotImplementedError
    def unwatchedpages_address(self, n=500):
        raise NotImplementedError
    def uncategorizedcategories_address(self, n=500):
        raise NotImplementedError
    def uncategorizedimages_address(self, n=500):
        raise NotImplementedError
    def uncategorizedpages_address(self, n=500):
        raise NotImplementedError
    def unusedcategories_address(self, n=500):
        raise NotImplementedError
    def withoutinterwiki_address(self, n=500):
        raise NotImplementedError
    def references_address(self, s):
        raise NotImplementedError
    def allmessages_address(self):
        raise NotImplementedError
    def upload_address(self):
        raise NotImplementedError
    def double_redirects_address(self, default_limit = True):
        raise NotImplementedError
    def broken_redirects_address(self, default_limit = True):
        raise NotImplementedError
    def login_address(self):
        raise NotImplementedError
    def captcha_image_address(self, id):
        raise NotImplementedError
    def watchlist_address(self):
        raise NotImplementedError
    def contribs_address(self, target, limit=500, offset=''):
        raise NotImplementedError


class APISite(BaseSite):
    """API interface to MediaWiki site.

    Do not use directly; use pywikibot.Site function.

    """
##    Site methods from version 1.0 (as these are implemented in this file,
##     or declared deprecated/obsolete, they will be removed from this list)
##########
##    cookies: return user's cookies as a string
##
##    urlEncode: Encode a query to be sent using an http POST request.
##    postForm: Post form data to an address at this site.
##    postData: Post encoded form data to an http address at this site.
##
##    shared_image_repository: Return tuple of image repositories used by this
##        site.
##    version: Return MediaWiki version string from Family file.
##    versionnumber: Return int identifying the MediaWiki version.
##    live_version: Return version number read from Special:Version.
##    checkCharset(charset): Warn if charset doesn't match family file.
##
##    linktrail: Return regex for trailing chars displayed as part of a link.
##    disambcategory: Category in which disambiguation pages are listed.
##
##    Methods that yield Page objects derived from a wiki's Special: pages
##    (note, some methods yield other information in a tuple along with the
##    Pages; see method docs for details) --
##
##        newpages(): Special:Newpages
##        newimages(): Special:Log&type=upload
##        longpages(): Special:Longpages
##        shortpages(): Special:Shortpages
##        deadendpages(): Special:Deadendpages
##        ancientpages(): Special:Ancientpages
##        lonelypages(): Special:Lonelypages
##        unwatchedpages(): Special:Unwatchedpages (sysop accounts only)
##        uncategorizedcategories(): Special:Uncategorizedcategories (yields
##            Category objects)
##        uncategorizedpages(): Special:Uncategorizedpages
##        uncategorizedimages(): Special:Uncategorizedimages (yields
##            ImagePage objects)
##        unusedcategories(): Special:Unusuedcategories (yields Category)
##        unusedfiles(): Special:Unusedimages (yields ImagePage)
##        withoutinterwiki: Special:Withoutinterwiki
##        linksearch: Special:Linksearch

    def __init__(self, code, fam=None, user=None, sysop=None):
        BaseSite.__init__(self, code, fam, user, sysop)
        self._namespaces = {
            # These are the MediaWiki built-in names, which always work.
            # Localized names are loaded later upon accessing the wiki.
            # Namespace prefixes are always case-insensitive, but the
            # canonical forms are capitalized
            -2: [u"Media"],
            -1: [u"Special"],
             0: [u""],
             1: [u"Talk"],
             2: [u"User"],
             3: [u"User talk"],
             4: [u"Project"],
             5: [u"Project talk"],
             6: [u"Image"],
             7: [u"Image talk"],
             8: [u"MediaWiki"],
             9: [u"MediaWiki talk"],
            10: [u"Template"],
            11: [u"Template talk"],
            12: [u"Help"],
            13: [u"Help talk"],
            14: [u"Category"],
            15: [u"Category talk"],
            }
        self.sitelock = threading.Lock()
        self._msgcache = {}
        # _loginstatus: -3 means login not yet attempted,
        #               -2 means login attempt in progress,
        #               -1 means not logged in (anon user),
        #               0 means logged in as user,
        #               1 means logged in as sysop
        self._loginstatus = -3
        return

    # ANYTHING BELOW THIS POINT IS NOT YET IMPLEMENTED IN __init__()
        # Calculating valid languages took quite long, so we calculate it once
        # in initialization instead of each time it is used.
        self._validlanguages = []
        for language in self.languages():
            if not language[:1].upper() + language[1:] in self.namespaces():
                self._validlanguages.append(language)

    def _generator(self, gen_class, type_arg=None, namespaces=None,
                   step=None, total=None, **args):
        """Convenience method that returns an API generator.

        All keyword args not listed below are passed to the generator's
        constructor unchanged.

        @param gen_class: the type of generator to construct (must be
            a subclass of pywikibot.data.api.QueryGenerator)
        @param type_arg: query type argument to be passed to generator's
            constructor unchanged (not all types require this)
        @type type_arg: str
        @param namespaces: if not None, limit the query to namespaces in this
            list
        @type namespaces: int, or list of ints
        @param step: if not None, limit each API call to this many items
        @type step: int
        @param total: if not None, limit the generator to yielding this many
            items in total
        @type total: int

        """
        if type_arg is not None:
            gen = gen_class(type_arg, site=self, **args)
        else:
            gen = gen_class(site=self, **args)
        if namespaces is not None:
            gen.set_namespace(namespaces)
        if step is not None and int(step) > 0:
            gen.set_query_increment(int(step))
        if total is not None and int(total) > 0:
            gen.set_maximum_items(int(total))
        return gen

    def logged_in(self, sysop=False):
        """Return True if logged in with specified privileges, otherwise False.

        @param sysop: if True, require sysop privileges.

        """
        if self.userinfo['name'] != self._username[sysop]:
            return False
        return (not sysop) or 'sysop' in self.userinfo['groups']

    @deprecated("Site.user()")
    def loggedInAs(self, sysop = False):
        """Return the current username if logged in, otherwise return None.

        DEPRECATED (use .user() method instead)

        """
        return self.logged_in(sysop) and self.user()

    def login(self, sysop=False):
        """Log the user in if not already logged in."""
        # check whether a login cookie already exists for this user
        self._loginstatus = -2
        if not hasattr(self, "_userinfo"):
            self.getuserinfo()
        if self.logged_in(sysop):
            return
        loginMan = api.LoginManager(site=self, sysop=sysop,
                                    user=self._username[sysop])
        if loginMan.login(retry = True):
            self._username[sysop] = loginMan.username
            if hasattr(self, "_userinfo"):
                del self._userinfo
            self.getuserinfo()
            self._loginstatus = sysop
        else:
            self._loginstatus = -1 # failure
        if not hasattr(self, "_siteinfo"):
            self._getsiteinfo()

    forceLogin = login  # alias for backward-compatibility

    def getuserinfo(self):
        """Retrieve userinfo from site and store in _userinfo attribute.

        self._userinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - name: username (if user is logged in)
          - anon: present if user is not logged in
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - message: present if user has a new message on talk page
          - blockinfo: present if user is blocked (dict)

        """
        if (not hasattr(self, "_userinfo")
                or "rights" not in self._userinfo
                or self._userinfo['name']
                   != self._username["sysop" in self._userinfo["groups"]]):
            uirequest = api.Request(
                                site=self,
                                action="query",
                                meta="userinfo",
                                uiprop="blockinfo|hasmsg|groups|rights"
                            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._userinfo = uidata['query']['userinfo']
        return self._userinfo

    userinfo = property(fget=getuserinfo, doc=getuserinfo.__doc__)

    def is_blocked(self, sysop=False):
        """Return true if and only if user is blocked.

        @param sysop: If true, log in to sysop account (if available)

        """
        if not self.logged_in(sysop):
            self.login(sysop)
        return 'blockinfo' in self._userinfo

    def isBlocked(self, sysop=False):
        """Deprecated synonym for is_blocked"""
        pywikibot.output(
            u"Site method 'isBlocked' should be changed to 'is_blocked'",
            level=pywikibot.DEBUG)
        return self.is_blocked(sysop)

    def checkBlocks(self, sysop = False):
        """Check if the user is blocked, and raise an exception if so."""
        if self.is_blocked(sysop):
            # User blocked
            raise UserBlocked('User is blocked in site %s' % self)

    def has_right(self, right, sysop=False):
        """Return true if and only if the user has a specific right.

        Possible values of 'right' may vary depending on wiki settings,
        but will usually include:

        * Actions: edit, move, delete, protect, upload
        * User levels: autoconfirmed, sysop, bot

        """
        if not self.logged_in(sysop):
            self.login(sysop)
        return right.lower() in self._userinfo['rights']

    @deprecated("Site.has_right()")
    def isAllowed(self, right, sysop=False):
        """Deprecated; retained for backwards-compatibility"""
        return self.has_right(right, sysop)

    def has_group(self, group, sysop=False):
        """Return true if and only if the user is a member of specified group.

        Possible values of 'group' may vary depending on wiki settings,
        but will usually include bot.

        """
        if not self.logged_in(sysop):
            self.login(sysop)
        return group.lower() in self._userinfo['groups']

    def messages(self, sysop=False):
        """Returns true if the user has new messages, and false otherwise."""
        if not self.logged_in(sysop):
            self.login(sysop)
        return 'hasmsg' in self._userinfo

    def mediawiki_message(self, key):
        """Return the MediaWiki message text for key "key" """
        if not key in self._msgcache:
            msg_query = api.QueryGenerator(site=self, meta="allmessages",
                                           amfilter=key)
            for msg in msg_query:
                if msg['name'] == key and not 'missing' in msg:
                    self._msgcache[key] = msg['*']
                    break
            else:
                raise KeyError("Site %(self)s has no message '%(key)s'"
                               % locals())
        return self._msgcache[key]

    def has_mediawiki_message(self, key):
        """Return True iff this site defines a MediaWiki message for 'key'."""
        try:
            v = self.mediawiki_message(key)
            return True
        except KeyError:
            return False

    def getcurrenttimestamp(self):
        """Return server time, {{CURRENTTIMESTAMP}}, as a string.

        Format is 'yyyymmddhhmmss'

        """
        r = api.Request(site=self,
                        action="parse",
                        text="{{CURRENTTIMESTAMP}}")
        result = r.submit()
        return re.search('\d+', result['parse']['text']['*']).group()

    def getcurrenttime(self):
        """Return a Timestamp object representing the current server time."""
        ts = self.getcurrenttimestamp()
        return pywikibot.Timestamp.fromtimestampformat(ts)

    def getmagicwords(self, word):
        """Return list of localized "word" magic words for the site."""
        if not hasattr(self, "_magicwords"):
            sirequest = api.Request(
                                site=self,
                                action="query",
                                meta="siteinfo",
                                siprop="magicwords"
                            )
            try:
                sidata = sirequest.submit()
                assert 'query' in sidata, \
                       "API siteinfo response lacks 'query' key"
                sidata = sidata['query']
                assert 'magicwords' in sidata, \
                       "API siteinfo response lacks 'magicwords' key"
                self._magicwords = dict((item["name"], item["aliases"])
                                        for item in sidata["magicwords"])

            except api.APIError:
                # hack for older sites that don't support 1.13 properties
                # probably should delete if we're not going to support pre-1.13
                self._magicwords = {}

        if word in self._magicwords:
            return self._magicwords[word]
        else:
            return [word]

    def redirect(self, default=True):
        """Return the preferred localized #REDIRECT keyword.

        Argument is ignored (but maintained for backwards-compatibility.

        """
        # return the magic word without the preceding '#' character
        return self.getmagicwords("redirect")[0].lstrip("#")

    def redirectRegex(self):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        #TODO: is this needed, since the API identifies redirects?
        #      (maybe, the API can give false positives)
        try:
            keywords = set(s.lstrip("#")
                           for s in self.getmagicwords("redirect"))
            keywords.add("REDIRECT") # just in case
            pattern = "(?:" + "|".join(keywords) + ")"
        except KeyError:
            # no localized keyword for redirects
            pattern = None
        return BaseSite.redirectRegex(self, pattern)

    def pagenamecodes(self, default=True):
        """Return list of localized PAGENAME tags for the site."""
        return self.getmagicwords("pagename")

    def pagename2codes(self, default=True):
        """Return list of localized PAGENAMEE tags for the site."""
        return self.getmagicwords("pagenamee")

    def _getsiteinfo(self):
        """Retrieve siteinfo and namespaces from site."""
        sirequest = api.Request(
                            site=self,
                            action="query",
                            meta="siteinfo",
                            siprop="general|namespaces|namespacealiases"
                        )
        try:
            sidata = sirequest.submit()
        except api.APIError:
            # hack for older sites that don't support 1.12 properties
            # probably should delete if we're not going to support pre-1.12
            sirequest = api.Request(
                                site=self,
                                action="query",
                                meta="siteinfo",
                                siprop="general|namespaces"
                            )
            sidata = sirequest.submit()

        assert 'query' in sidata, \
               "API siteinfo response lacks 'query' key"
        sidata = sidata['query']
        assert 'general' in sidata, \
               "API siteinfo response lacks 'general' key"
        assert 'namespaces' in sidata, \
               "API siteinfo response lacks 'namespaces' key"
        self._siteinfo = sidata['general']
        nsdata = sidata['namespaces']
        for nskey in nsdata:
            ns = int(nskey)
            if ns in self._namespaces:
                if nsdata[nskey]["*"] in self._namespaces[ns]:
                    continue
                # this is the preferred form so it goes at front of list
                self._namespaces[ns].insert(0, nsdata[nskey]["*"])
            else:
                self._namespaces[ns] = [nsdata[nskey]["*"]]
        if 'namespacealiases' in sidata:
            aliasdata = sidata['namespacealiases']
            for item in aliasdata:
                if item["*"] in self._namespaces[int(item['id'])]:
                    continue
                # this is a less preferred form so it goes at the end
                self._namespaces[int(item['id'])].append(item["*"])

    @property
    def siteinfo(self):
        """Site information dict."""

        if not hasattr(self, "_siteinfo"):
            self._getsiteinfo()
        return self._siteinfo

    def case(self):
        """Return this site's capitalization rule."""

        return self.siteinfo['case']

    def dbName(self):
        """Return this site's internal id."""

        return self.siteinfo['wikiid']

    def language(self):
        """Return the code for the language of this Site."""

        return self.siteinfo['lang']

    lang = property(fget=language, doc=language.__doc__)

    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""

        if not hasattr(self, "_siteinfo"):
            self._getsiteinfo()
        return self._namespaces

    def namespace(self, num, all=False):
        """Return string containing local name of namespace 'num'.

        If optional argument 'all' is true, return a list of all recognized
        values for this namespace.

        """
        if all:
            return self.namespaces()[num]
        return self.namespaces()[num][0]

    def live_version(self):
        """Return the 'real' version number found on [[Special:Version]]

        Return value is a tuple (int, int, str) of the major and minor
        version numbers and any other text contained in the version.

        """
        versionstring = self.siteinfo['generator']
        m = re.match(r"^MediaWiki ([0-9]+)\.([0-9]+)(.*)$", versionstring)
        if m:
            return (int(m.group(1)), int(m.group(2)), m.group(3))
        else:
            return None

    def loadpageinfo(self, page):
        """Load page info from api and save in page attributes"""
        title = page.title(withSection=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg="info",
                                titles=title.encode(self.encoding()),
                                inprop="protection")
        for pageitem in query:
            if pageitem['title'] != title:
                if pageitem['title'] in query.normalized \
                        and query.normalized[pageitem['title']] == title:
                    # page title was normalized by api
                    # this should never happen because the Link() constructor
                    # normalizes the title
                    pywikibot.output(
                        u"loadpageinfo: Page title '%s' was normalized to '%s'"
                         % (title, pageitem['title']),
                        level=pywikibot.ERROR)
                else:
                    pywikibot.output(
                        u"loadpageinfo: Query on %s returned data on '%s'"
                         % (page, pageitem['title']),
                        level=pywikibot.WARNING)
                continue
            api.update_page(page, pageitem)

    def loadimageinfo(self, page, history=False):
        """Load image info from api and save in page attributes

        @param history: if true, return the image's version history

        """
        title = page.title(withSection=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg="imageinfo",
                                titles=title.encode(self.encoding()),
                                iiprop=["timestamp", "user", "comment",
                                        "url", "size", "sha1", "mime",
                                        "metadata", "archivename"]
                               )
        if history:
            query.request["iilimit"] = "max"
        for pageitem in query:
            if pageitem['title'] != title:
                raise Error(
                    u"loadpageinfo: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            api.update_page(page, pageitem)
            if history:
                return pageitem['imageinfo']

    def page_exists(self, page):
        """Return True if and only if page is an existing page on site."""
        if not hasattr(page, "_pageid"):
            self.loadpageinfo(page)
        return page._pageid > 0

    def page_restrictions(self, page):
        """Returns a dictionary reflecting page protections"""
        if not self.page_exists(page):
            raise NoPage(page)
        if not hasattr(page, "_protection"):
            self.loadpageinfo(page)
        return page._protection

    def page_can_be_edited(self, page):
        """
        Returns True if and only if:
          - page is unprotected, and bot has an account for this site, or
          - page is protected, and bot has a sysop account for this site.

        """
        rest = self.page_restrictions(page)
        sysop_protected = "edit" in rest and rest['edit'][0] == 'sysop'
        try:
            api.LoginManager(site=self, sysop=sysop_protected)
        except NoUsername:
            return False
        return True

    def page_isredirect(self, page):
        """Return True if and only if page is a redirect."""
        if not hasattr(page, "_isredir"):
            self.loadpageinfo(page)
        return page._isredir

    def getredirtarget(self, page):
        """Return Page object for the redirect target of page."""
        if not self.page_isredirect(page):
            raise pywikibot.IsNotRedirectPage(page)
        if hasattr(page, '_redirtarget'):
            return page._redirtarget
        title = page.title(withSection=False)
        query = api.Request(site=self, action="query", property="info",
                            inprop="protection|talkid|subjectid",
                            titles=title.encode(self.encoding()),
                            redirects="")
        result = query.submit()
        if "query" not in result or "redirects" not in result["query"]:
            raise RuntimeError(
                "getredirtarget: No 'redirects' found for page %s."
                % title)
        redirmap = dict((item['from'], item['to'])
                            for item in result['query']['redirects'])
        if title not in redirmap:
            raise RuntimeError(
                "getredirtarget: 'redirects' contains no key for page %s."
                % title)
        target_title = redirmap[title]
        if target_title == title or "pages" not in result['query']:
            # no "pages" element indicates a circular redirect
            raise pywikibot.CircularRedirect(redirmap[title])
        pagedata = result['query']['pages'].values()[0]
            # there should be only one value in 'pages', and it is the target
        if pagedata['title'] == target_title:
            target = pywikibot.Page(self, pagedata['title'], pagedata['ns'])
            api.update_page(target, pagedata)
            page._redirtarget = target
        else:
            # double redirect; target is an intermediate redirect
            target = pywikibot.Page(self, target_title)
            page._redirtarget = target
        return page._redirtarget

    def preloadpages(self, pagelist, groupsize=50, templates=False,
            langlinks=False):
        """Return a generator to a list of preloaded pages.

        Note that [at least in current implementation] pages may be iterated
        in a different order than in the underlying pagelist.

        @param pagelist: an iterable that returns Page objects
        @param groupsize: how many Pages to query at a time
        @type groupsize: int
        @param templates: preload list of templates in the pages
        @param langlinks: preload list of language links found in the pages

        """
        from pywikibot.tools import itergroup
        for sublist in itergroup(pagelist, groupsize):
            pageids = [str(p._pageid) for p in sublist
                                      if hasattr(p, "_pageid")
                                         and p._pageid > 0]
            cache = dict((p.title(withSection=False), p) for p in sublist)

            props = "revisions|info|categoryinfo"
            if templates:
                props += '|templates'
            if langlinks:
                props += '|langlinks'
            rvgen = api.PropertyGenerator(props, site=self)
            rvgen.set_maximum_items(-1) # suppress use of "rvlimit" parameter
            if len(pageids) == len(sublist):
                # only use pageids if all pages have them
                rvgen.request["pageids"] = "|".join(pageids)
            else:
                rvgen.request["titles"] = "|".join(cache.keys())
            rvgen.request[u"rvprop"] = \
                    u"ids|flags|timestamp|user|comment|content"
            pywikibot.output(u"Retrieving %s pages from %s."
                           % (len(cache), self)
                        )
            for pagedata in rvgen:
                pywikibot.output(u"Preloading %s" % pagedata,
                                 level=pywikibot.DEBUG)
                try:
                    if pagedata['title'] not in cache:
                        pywikibot.output(
                        u"preloadpages: Query returned unexpected title '%s'"
                             % pagedata['title'],
                            level=pywikibot.WARNING
                        )
                        continue
                except KeyError:
                    pywikibot.output(u"No 'title' in %s" % pagedata,
                                     level=pywikibot.DEBUG)
                    pywikibot.output(u"pageids=%s" % pageids,
                                     level=pywikibot.DEBUG)
                    pywikibot.output(u"titles=%s" % cache.keys(),
                                     level=pywikibot.DEBUG)
                    continue
                page = cache[pagedata['title']]
                api.update_page(page, pagedata)
                yield page

    def token(self, page, tokentype):
        """Return token retrieved from wiki to allow changing page content.

        @param page: the Page for which a token should be retrieved
        @param tokentype: the type of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types

        """
        query = api.PropertyGenerator("info|revisions",
                                      titles=page.title(withSection=False),
                                      intoken=tokentype,
                                      site=self)
        for item in query:
            if item['title'] != page.title(withSection=False):
                raise Error(
                    u"token: Query on page %s returned data on page [[%s]]"
                     % (page.title(withSection=False, asLink=True),
                        item['title']))
            api.update_page(page, item)
            pywikibot.output(unicode(item),
                             level=pywikibot.DEBUG)
            return item[tokentype + "token"]

    # following group of methods map more-or-less directly to API queries

    def pagebacklinks(self, page, followRedirects=False, filterRedirects=None,
                      namespaces=None, step=None, total=None):
        """Iterate all pages that link to the given page.

        @param page: The Page to get links to.
        @param followRedirects: Also return links to redirects pointing to
            the given page.
        @param filterRedirects: If True, only return redirects to the given
            page. If False, only return non-redirect links. If None, return
            both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @param step: Limit on number of pages to retrieve per API query.
        @param total: Maximum number of pages to retrieve in total.

        """
        bltitle = page.title(withSection=False).encode(self.encoding())
        blgen = self._generator(api.PageGenerator, type_arg="backlinks",
                                gbltitle=bltitle, namespaces=namespaces,
                                step=step, total=total)
        if filterRedirects is not None:
            blgen.request["gblfilterredir"] = filterRedirects and "redirects"\
                                                              or "nonredirects"
        if followRedirects:
            # bug: see http://bugzilla.wikimedia.org/show_bug.cgi?id=7304
            # links identified by MediaWiki as redirects may not really be,
            # so we have to check each "redirect" page and see if it
            # really redirects to this page
            redirgen = self._generator(api.PageGenerator,
                                       type_arg="backlinks",
                                       gbltitle=bltitle,
                                       gblfilterredir="redirects")
            genlist = {None: blgen}
            for redir in redirgen:
                if redir == page:
                    # if a wiki contains pages whose titles contain
                    # namespace aliases that existed before those aliases
                    # were defined (example: [[WP:Sandbox]] existed as a
                    # redirect to [[Wikipedia:Sandbox]] before the WP: alias
                    # was created) they can be returned as redirects to
                    # themselves; skip these
                    continue
                if redir.getRedirectTarget() == page:
                    genlist[redir.title()] = self.pagebacklinks(
                                                redir, followRedirects=True,
                                                filterRedirects=filterRedirects,
                                                namespaces=namespaces)
            import itertools
            return itertools.chain(*genlist.values())
        return blgen

    def page_embeddedin(self, page, filterRedirects=None, namespaces=None,
                        step=None, total=None):
        """Iterate all pages that embedded the given page as a template.

        @param page: The Page to get inclusions for.
        @param filterRedirects: If True, only return redirects that embed
            the given page. If False, only return non-redirect links. If
            None, return both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.

        """
        eititle = page.title(withSection=False).encode(self.encoding())
        eigen = self._generator(api.PageGenerator, type_arg="embeddedin",
                                geititle=eititle, namespaces=namespaces,
                                step=step, total=total)
        if filterRedirects is not None:
            eigen.request["geifilterredir"] = filterRedirects and "redirects"\
                                                              or "nonredirects"
        return eigen

    def pagereferences(self, page, followRedirects=False, filterRedirects=None,
                       withTemplateInclusion=True, onlyTemplateInclusion=False,
                       namespaces=None, step=None, total=None):
        """Convenience method combining pagebacklinks and page_embeddedin."""

        if onlyTemplateInclusion:
            return self.page_embeddedin(page, namespaces=namespaces,
                                        step=step, total=total)
        if not withTemplateInclusion:
            return self.pagebacklinks(page, followRedirects,
                                      namespaces=namespaces,
                                      step=step, total=total)
        import itertools
        return itertools.islice(
                    itertools.chain(
                        self.pagebacklinks(
                            page, followRedirects, filterRedirects,
                            namespaces=namespaces, step=step),
                        self.page_embeddedin(
                            page, filterRedirects, namespaces=namespaces,
                            step=step)
                        ),
                    total)

    def pagelinks(self, page, namespaces=None, follow_redirects=False,
                  step=None, total=None):
        """Iterate internal wikilinks contained (or transcluded) on page.

        @param namespaces: Only iterate pages in these namespaces (default: all)
        @type namespaces: list of ints
        @param follow_redirects: if True, yields the target of any redirects,
            rather than the redirect page

        """
        plgen = self._generator(api.PageGenerator, type_arg="links",
                                namespaces=namespaces, step=step, total=total)
        if hasattr(page, "_pageid"):
            plgen.request['pageids'] = str(page._pageid)
        else:
            pltitle = page.title(withSection=False).encode(self.encoding())
            plgen.request['titles'] = pltitle
        if follow_redirects:
            plgen.request['redirects'] = ''
        return plgen

    @deprecate_arg("withSortKey", None) # Sortkey doesn't work with generator
    def pagecategories(self, page, step=None, total=None):
        """Iterate categories to which page belongs."""

        clgen = self._generator(api.CategoryPageGenerator,
                                type_arg="categories", step=step, total=total)
        if hasattr(page, "_pageid"):
            clgen.request['pageids'] = str(page._pageid)
        else:
            cltitle = page.title(withSection=False).encode(self.encoding())
            clgen.request['titles'] = cltitle
        return clgen

    def pageimages(self, page, step=None, total=None):
        """Iterate images used (not just linked) on the page."""

        imtitle = page.title(withSection=False).encode(self.encoding())
        imgen = self._generator(api.ImagePageGenerator, type_arg="images",
                                titles=imtitle, step=step, total=total)
        return imgen

    def pagetemplates(self, page, namespaces=None, step=None, total=None):
        """Iterate templates transcluded (not just linked) on the page."""

        tltitle = page.title(withSection=False).encode(self.encoding())
        tlgen = self._generator(api.PageGenerator, type_arg="templates",
                                titles=tltitle, namespaces=namespaces,
                                step=step, total=total)
        return tlgen

    def categorymembers(self, category, namespaces=None, step=None, total=None):
        """Iterate members of specified category.

        @param category: The Category to iterate.
        @param namespaces: If present, only return category members from
            these namespaces. For example, use namespaces=[14] to yield
            subcategories, use namespaces=[6] to yield image files, etc. Note,
            however, that the iterated values are always Page objects, even
            if in the Category or Image namespace.
        @type namespaces: list of ints

        """
        if category.namespace() != 14:
            raise Error(
                u"categorymembers: non-Category page '%s' specified"
                % category.title())
        cmtitle = category.title(withSection=False).encode(self.encoding())
        cmgen = self._generator(api.PageGenerator,
                                type_arg="categorymembers",
                                gcmtitle=cmtitle,
                                gcmprop="ids|title|sortkey",
#                                namespaces=namespaces,
                                step=step,
                                total=total)
#       workaround for https://bugzilla.wikimedia.org/show_bug.cgi?id=19640:
        if namespaces:
            if not isinstance(namespaces, list):
                namespaces = [namespaces]
            cmgen = pagegenerators.NamespaceFilterPageGenerator(
                        cmgen, namespaces, site=self)
        return cmgen

    def loadrevisions(self, page=None, getText=False, revids=None,
                      startid=None, endid=None, starttime=None,
                      endtime=None, rvdir=None, user=None, excludeuser=None,
                      section=None, sysop=False, step=None, total=None):
        """Retrieve and store revision information.

        By default, retrieves the last (current) revision of the page,
        I{unless} any of the optional parameters revids, startid, endid,
        starttime, endtime, rvdir, user, excludeuser, or limit are
        specified. Unless noted below, all parameters not specified
        default to False.

        If rvdir is False or not specified, startid must be greater than
        endid if both are specified; likewise, starttime must be greater
        than endtime. If rvdir is True, these relationships are reversed.

        @param page: retrieve revisions of this Page (required unless ids
            is specified)
        @param getText: if True, retrieve the wiki-text of each revision;
            otherwise, only retrieve the revision metadata (default)
        @param section: if specified, retrieve only this section of the text
            (getText must be True); section must be given by number (top of
            the article is section 0), not name
        @type section: int
        @param revids: retrieve only the specified revision ids (required
            unless page is specified)
        @type revids: list of ints
        @param startid: retrieve revisions starting with this revid
        @param endid: stop upon retrieving this revid
        @param starttime: retrieve revisions starting at this Timestamp
        @param endtime: stop upon reaching this Timestamp
        @param rvdir: if false, retrieve newest revisions first (default);
            if true, retrieve earliest first
        @param user: retrieve only revisions authored by this user
        @param excludeuser: retrieve all revisions not authored by this user
        @param sysop: if True, switch to sysop account (if available) to
            retrieve this page

        """
        latest = (revids is None and
                  startid is None and
                  endid is None and
                  starttime is None and
                  endtime is None and
                  rvdir is None and
                  user is None and
                  excludeuser is None and
                  step is None and
                  total is None)  # if True, retrieving current revision

        # check for invalid argument combinations
        if page is None and revids is None:
            raise ValueError(
                "loadrevisions:  either page or revids argument required")
        if (startid is not None or endid is not None) and \
                (starttime is not None or endtime is not None):
            raise ValueError(
                "loadrevisions: startid/endid combined with starttime/endtime")
        if starttime is not None and endtime is not None:
            if rvdir and starttime >= endtime:
                raise ValueError(
                    "loadrevisions: starttime > endtime with rvdir=True")
            if (not rvdir) and endtime >= starttime:
                raise ValueError(
                    "loadrevisions: endtime > starttime with rvdir=False")
        if startid is not None and endid is not None:
            if rvdir and startid >= endid:
                raise ValueError(
                    "loadrevisions: startid > endid with rvdir=True")
            if (not rvdir) and endid >= startid:
                raise ValueError(
                    "loadrevisions: endid > startid with rvdir=False")

        # assemble API request
        if revids is None:
            rvtitle = page.title(withSection=False).encode(self.encoding())
            rvgen = self._generator(api.PropertyGenerator,
                                    type_arg=u"info|revisions",
                                    titles=rvtitle, step=step, total=total)
        else:
            if isinstance(revids, (int, basestring)):
                ids = unicode(revids)
            else:
                ids = u"|".join(unicode(r) for r in revids)
            rvgen = self._generator(api.PropertyGenerator,
                                    type_arg=u"info|revisions", revids=ids,
                                    step=step, total=total)
        if getText:
            rvgen.request[u"rvprop"] = \
                    u"ids|flags|timestamp|user|comment|content"
            if section is not None:
                rvgen.request[u"rvsection"] = unicode(section)
        if latest or "revids" in rvgen.request:
            rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter
        if rvdir:
            rvgen.request[u"rvdir"] = u"newer"
        elif rvdir is not None:
            rvgen.request[u"rvdir"] = u"older"
        if startid:
            rvgen.request[u"rvstartid"] = startid
        if endid:
            rvgen.request[u"rvendid"] = endid
        if starttime:
            rvgen.request[u"rvstart"] = str(starttime)
        if endtime:
            rvgen.request[u"rvend"] = str(endtime)
        if user:
            rvgen.request[u"rvuser"] = user
        elif excludeuser:
            rvgen.request[u"rvexcludeuser"] = excludeuser
        # TODO if sysop: something
        rvgen.continuekey = "revisions"
        for pagedata in rvgen:
            if page is not None:
                if pagedata['title'] != page.title(withSection=False):
                    raise Error(
                        u"loadrevisions: Query on %s returned data on '%s'"
                        % (page, pagedata['title']))
                if "missing" in pagedata:
                    raise NoPage(page)
            else:
                page = Page(self, pagedata['title'])
            api.update_page(page, pagedata)

    def pageinterwiki(self, page):
        # No such function in the API (this method isn't called anywhere)
        raise NotImplementedError

    def pagelanglinks(self, page, step=None, total=None):
        """Iterate all interlanguage links on page, yielding Link objects."""
        lltitle = page.title(withSection=False)
        llquery = self._generator(api.PropertyGenerator,
                                  type_arg="langlinks",
                                  titles=lltitle.encode(self.encoding()),
                                  step=step, total=total)
        for pageitem in llquery:
            if pageitem['title'] != lltitle:
                raise Error(
                    u"getlanglinks: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            if 'langlinks' not in pageitem:
                continue
            for linkdata in pageitem['langlinks']:
                yield pywikibot.Link.langlinkUnsafe(linkdata['lang'],
                                                    linkdata['*'],
                                                    source=self)

    def page_extlinks(self, page, step=None, total=None):
        """Iterate all external links on page, yielding URL strings."""
        eltitle = page.title(withSection=False)
        elquery = self._generator(api.PropertyGenerator, type_arg="extlinks",
                                  titles=eltitle.encode(self.encoding()),
                                  step=step, total=total)
        for pageitem in elquery:
            if pageitem['title'] != eltitle:
                raise RuntimeError(
                    "getlanglinks: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            if 'extlinks' not in pageitem:
                continue
            for linkdata in pageitem['extlinks']:
                yield linkdata['*']

    def getcategoryinfo(self, category):
        """Retrieve data on contents of category."""
        cititle = category.title(withSection=False)
        ciquery = self._generator(api.PropertyGenerator,
                                  type_arg="categoryinfo",
                                  titles=cititle.encode(self.encoding()))
        for pageitem in ciquery:
            if pageitem['title'] != cititle:
                raise Error(
                    u"categoryinfo: Query on %s returned data on '%s'"
                    % (category, pageitem['title']))
            api.update_page(category, pageitem)

    def categoryinfo(self, category):
        if not hasattr(category, "_catinfo"):
            self.getcategoryinfo(category)
        if not hasattr(category, "_catinfo"):
            # a category that exists but has no contents returns no API result
            category._catinfo = {'size':0, 'pages':0, 'files':0, 'subcats':0}
        return category._catinfo

    @deprecate_arg("throttle", None)
    @deprecate_arg("limit", "total")
    def allpages(self, start="!", prefix="", namespace=0, filterredir=None,
                 filterlanglinks=None, minsize=None, maxsize=None,
                 protect_type=None, protect_level=None, reverse=False,
                 includeredirects=None, step=None, total=None):
        """Iterate pages in a single namespace.

        Note: parameters includeRedirects and throttle are deprecated and
        included only for backwards compatibility.

        @param start: Start at this title (page need not exist).
        @param prefix: Only yield pages starting with this string.
        @param namespace: Iterate pages from this (single) namespace
           (default: 0)
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        @param filterlanglinks: if True, only yield pages with language links;
            if False (and not None), only yield pages without language links
            (default: yield both)
        @param minsize: if present, only yield pages at least this many
            bytes in size
        @param maxsize: if present, only yield pages at most this many bytes
            in size
        @param protect_type: only yield pages that have a protection of the
            specified type
        @type protect_type: str
        @param protect_level: only yield pages that have protection at this
            level; can only be used if protect_type is specified
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        @param includeredirects: DEPRECATED, use filterredirs instead

        """
        if not isinstance(namespace, int):
            raise Error("allpages: only one namespace permitted.")
        if includeredirects is not None:
            pywikibot.output(
u"allpages: 'includeRedirects' argument is deprecated; use 'filterredirs'.",
                 level=pywikibot.DEBUG)
            if includeredirects:
                if includeredirects == "only":
                    filterredirs = True
                else:
                    filterredirs = None
            else:
                filterredirs = False

        apgen = self._generator(api.PageGenerator, type_arg="allpages",
                                gapnamespace=str(namespace),
                                gapfrom=start, step=step, total=total)
        if prefix:
            apgen.request["gapprefix"] = prefix
        if filterredir is not None:
            apgen.request["gapfilterredir"] = (filterredir
                                               and "redirects"
                                               or "nonredirects")
        if filterlanglinks is not None:
            apgen.request["gapfilterlanglinks"] = (filterlanglinks
                                                   and "withlanglinks"
                                                   or "withoutlanglinks")
        if isinstance(minsize, int):
            apgen.request["gapminsize"] = str(minsize)
        if isinstance(maxsize, int):
            apgen.request["gapmaxsize"] = str(maxsize)
        if isinstance(protect_type, basestring):
            apgen.request["gapprtype"] = protect_type
            if isinstance(protect_level, basestring):
                apgen.request["gapprlevel"] = protect_level
        if reverse:
            apgen.request["gapdir"] = "descending"
        return apgen

    @deprecated("Site.allpages()")
    def prefixindex(self, prefix, namespace=0, includeredirects=True):
        """Yield all pages with a given prefix. Deprecated.

        Use allpages() with the prefix= parameter instead of this method.

        """
        return self.allpages(prefix=prefix, namespace=namespace,
                             includeredirects=includeredirects)


    def alllinks(self, start="!", prefix="", namespace=0, unique=False,
                 fromids=False, step=None, total=None):
        """Iterate all links to pages (which need not exist) in one namespace.

        Note that, in practice, links that were found on pages that have
        been deleted may not have been removed from the links table, so this
        method can return false positives.

        @param start: Start at this title (page need not exist).
        @param prefix: Only yield pages starting with this string.
        @param namespace: Iterate pages from this (single) namespace
            (default: 0)
        @param unique: If True, only iterate each link title once (default:
            iterate once for each linking page)
        @param fromids: if True, include the pageid of the page containing
            each link (default: False) as the '_fromid' attribute of the Page;
            cannot be combined with unique

        """
        if unique and fromids:
            raise Error("alllinks: unique and fromids cannot both be True.")
        if not isinstance(namespace, int):
            raise Error("alllinks: only one namespace permitted.")
        algen = self._generator(api.ListGenerator, type_arg="alllinks",
                                alnamespace=str(namespace), alfrom=start,
                                step=step, total=total)
        if prefix:
            algen.request["alprefix"] = prefix
        if unique:
            algen.request["alunique"] = ""
        if fromids:
            algen.request["alprop"] = "title|ids"
        for link in algen:
            p = pywikibot.Page(self, link['title'], link['ns'])
            if fromids:
                p._fromid = link['fromid']
            yield p

    def allcategories(self, start="!", prefix="", step=None, total=None,
                      reverse=False):
        """Iterate categories used (which need not have a Category page).

        Iterator yields Category objects. Note that, in practice, links that
        were found on pages that have been deleted may not have been removed
        from the database table, so this method can return false positives.

        @param start: Start at this category title (category need not exist).
        @param prefix: Only yield categories starting with this string.
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)

        """
        acgen = self._generator(api.CategoryPageGenerator,
                                type_arg="allcategories", gacfrom=start,
                                step=step, total=total)
        if prefix:
            acgen.request["gacprefix"] = prefix
        if reverse:
            acgen.request["gacdir"] = "descending"
        return acgen

    @deprecated("Site.allcategories()")
    def categories(self, number=10, repeat=False):
        """Deprecated; retained for backwards-compatibility"""
        if repeat:
            limit = None
        else:
            limit = number
        return self.allcategories(total=limit)

    def allusers(self, start="!", prefix="", group=None, step=None,
                 total=None):
        """Iterate registered users, ordered by username.

        Iterated values are dicts containing 'name', 'editcount',
        'registration', and (sometimes) 'groups' keys. 'groups' will be
        present only if the user is a member of at least 1 group, and will
        be a list of unicodes; all the other values are unicodes and should
        always be present.

        @param start: start at this username (name need not exist)
        @param prefix: only iterate usernames starting with this substring
        @param group: only iterate users that are members of this group
        @type group: str

        """
        augen = self._generator(api.ListGenerator, type_arg="allusers",
                                auprop="editcount|groups|registration",
                                aufrom=start, step=step, total=total)
        if prefix:
            augen.request["auprefix"] = prefix
        if group:
            augen.request["augroup"] = group
        return augen

    def allimages(self, start="!", prefix="", minsize=None, maxsize=None,
                  reverse=False, sha1=None, sha1base36=None, step=None,
                  total=None):
        """Iterate all images, ordered by image title.

        Yields ImagePages, but these pages need not exist on the wiki.

        @param start: start at this title (name need not exist)
        @param prefix: only iterate titles starting with this substring
        @param minsize: only iterate images of at least this many bytes
        @param maxsize: only iterate images of no more than this many bytes
        @param reverse: if True, iterate in reverse lexigraphic order
        @param sha1: only iterate image (it is theoretically possible there
            could be more than one) with this sha1 hash
        @param sha1base36: same as sha1 but in base 36

        """
        aigen = self._generator(api.ImagePageGenerator,
                                type_arg="allimages", gaifrom=start,
                                step=step, total=total)
        if prefix:
            aigen.request["gaiprefix"] = prefix
        if isinstance(minsize, int):
            aigen.request["gaiminsize"] = str(minsize)
        if isinstance(maxsize, int):
            aigen.request["gaimaxsize"] = str(maxsize)
        if reverse:
            aigen.request["gaidir"] = "descending"
        if sha1:
            aigen.request["gaisha1"] = sha1
        if sha1base36:
            aigen.request["gaisha1base36"] = sha1base36
        return aigen

    def blocks(self, starttime=None, endtime=None, reverse=False,
               blockids=None, users=None, step=None, total=None):
        """Iterate all current blocks, in order of creation.

        Note that logevents only logs user blocks, while this method
        iterates all blocks including IP ranges.  The iterator yields dicts
        containing keys corresponding to the block properties (see
        http://www.mediawiki.org/wiki/API:Query_-_Lists for documentation).

        @param starttime: start iterating at this Timestamp
        @param endtime: stop iterating at this Timestamp
        @param reverse: if True, iterate oldest blocks first (default: newest)
        @param blockids: only iterate blocks with these id numbers
        @param users: only iterate blocks affecting these usernames or IPs

        """
        if starttime and endtime:
            if reverse:
                if starttime > endtime:
                    raise pywikibot.Error(
                "blocks: starttime must be before endtime with reverse=True")
            else:
                if endtime > starttime:
                    raise pywikibot.Error(
                "blocks: endtime must be before starttime with reverse=False")
        bkgen = self._generator(api.ListGenerator, type_arg="blocks",
                                step=step, total=total)
        bkgen.request["bkprop"] = \
                            "id|user|by|timestamp|expiry|reason|range|flags"
        if starttime:
            bkgen.request["bkstart"] = str(starttime)
        if endtime:
            bkgen.request["bkend"] = str(endtime)
        if reverse:
            bkgen.request["bkdir"] = "newer"
        if blockids:
            bkgen.request["bkids"] = blockids
        if users:
            bkgen.request["bkusers"] = users
        return bkgen

    def exturlusage(self, url, protocol="http", namespaces=None,
                    step=None, total=None):
        """Iterate Pages that contain links to the given URL.

        @param url: The URL to search for (without the protocol prefix);
            this many include a '*' as a wildcard, only at the start of the
            hostname
        @param protocol: The protocol prefix (default: "http")

        """
        eugen = self._generator(api.PageGenerator, type_arg="exturlusage",
                                geuquery=url, geuprotocol=protocol,
                                namespaces=namespaces, step=step,
                                total=total)
        return eugen

    def imageusage(self, image, namespaces=None, filterredir=None,
                   step=None, total=None):
        """Iterate Pages that contain links to the given ImagePage.

        @param image: the image to search for (ImagePage need not exist on
            the wiki)
        @type image: ImagePage
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)

        """
        iuargs = dict(giutitle=image.title(withSection=False))
        if filterredir is not None:
            iuargs["giufilterredir"] = (filterredir and "redirects"
                                                     or "nonredirects")
        iugen = self._generator(api.PageGenerator, type_arg="imageusage",
                                namespaces=namespaces, step=step,
                                total=total, **iuargs)
        return iugen

    def logevents(self, logtype=None, user=None, page=None,
                  start=None, end=None, reverse=False, step=None, total=None):
        """Iterate all log entries.

        @param logtype: only iterate entries of this type (see wiki
            documentation for available types, which will include "block",
            "protect", "rights", "delete", "upload", "move", "import",
            "patrol", "merge")
        @param user: only iterate entries that match this user name
        @param page: only iterate entries affecting this page
        @param start: only iterate entries from and after this Timestamp
        @param end: only iterate entries up to and through this Timestamp
        @param reverse: if True, iterate oldest entries first (default: newest)

        """
        if start and end:
            if reverse:
                if end < start:
                    raise Error(
                  "logevents: end must be later than start with reverse=True")
            else:
                if start < end:
                    raise Error(
                  "logevents: start must be later than end with reverse=False")
        legen = self._generator(api.LogEntryListGenerator, type_arg=logtype,
                                step=step, total=total)
        if logtype is not None:
            legen.request["letype"] = logtype
        if user is not None:
            legen.request["leuser"] = user
        if page is not None:
            legen.request["letitle"] = page.title(withSection=False)
        if start is not None:
            legen.request["lestart"] = str(start)
        if end is not None:
            legen.request["leend"] = str(end)
        if reverse:
            legen.request["ledir"] = "newer"
        return legen

    def recentchanges(self, start=None, end=None, reverse=False,
                      namespaces=None, pagelist=None, changetype=None,
                      showMinor=None, showBot=None, showAnon=None,
                      showRedirects=None, showPatrolled=None, step=None,
                      total=None):
        """Iterate recent changes.

        @param start: Timestamp to start listing from
        @param end: Timestamp to end listing at
        @param reverse: if True, start with oldest changes (default: newest)
        @param limit: iterate no more than this number of entries
        @param pagelist: iterate changes to pages in this list only
        @param pagelist: list of Pages
        @param changetype: only iterate changes of this type ("edit" for
            edits to existing pages, "new" for new pages, "log" for log
            entries)
        @param showMinor: if True, only list minor edits; if False (and not
            None), only list non-minor edits
        @param showBot: if True, only list bot edits; if False (and not
            None), only list non-bot edits
        @param showAnon: if True, only list anon edits; if False (and not
            None), only list non-anon edits
        @param showRedirects: if True, only list edits to redirect pages; if
            False (and not None), only list edits to non-redirect pages
        @param showPatrolled: if True, only list patrolled edits; if False
            (and not None), only list non-patrolled edits

        """
        if start and end:
            if reverse:
                if end < start:
                    raise Error(
            "recentchanges: end must be later than start with reverse=True")
            else:
                if start < end:
                    raise Error(
            "recentchanges: start must be later than end with reverse=False")
        rcgen = self._generator(api.ListGenerator, type_arg="recentchanges",
                                rcprop="user|comment|timestamp|title|ids"
                                       "|redirect|loginfo|flags",
                                namespaces=namespaces, step=step,
                                total=total)
        if start is not None:
            rcgen.request["rcstart"] = str(start)
        if end is not None:
            rcgen.request["rcend"] = str(end)
        if reverse:
            rcgen.request["rcdir"] = "newer"
        if pagelist:
            if self.versionnumber() > 14:
                pywikibot.output(
                    u"recentchanges: pagelist option is disabled",
                    level=pywikibot.ERROR)
            else:
                rcgen.request["rctitles"] = u"|".join(p.title(withSection=False)
                                                      for p in pagelist)
        if changetype:
            rcgen.request["rctype"] = changetype
        filters = {'minor': showMinor,
                   'bot': showBot,
                   'anon': showAnon,
                   'redirect': showRedirects,}
                   #'patrolled': showPatrolled}
        rcshow = []
        for item in filters:
            if filters[item] is not None:
                rcshow.append(filters[item] and item or ("!"+item))
        if rcshow:
            rcgen.request["rcshow"] = "|".join(rcshow)
        return rcgen

    @deprecate_arg("number", "limit")
    def search(self, searchstring, namespaces=None, where="text",
               getredirects=False, step=None, total=None):
        """Iterate Pages that contain the searchstring.

        Note that this may include non-existing Pages if the wiki's database
        table contains outdated entries.

        @param searchstring: the text to search for
        @type searchstring: unicode
        @param where: Where to search; value must be "text" or "titles" (many
            wikis do not support title search)
        @param namespaces: search only in these namespaces (defaults to 0)
        @type namespaces: list of ints
        @param getredirects: if True, include redirects in results

        """
        if not searchstring:
            raise Error("search: searchstring cannot be empty")
        if where not in ("text", "titles"):
            raise Error("search: unrecognized 'where' value: %s" % where)
        if not namespaces:
            pywikibot.output(u"search: namespaces cannot be empty; using [0].",
                             level=pywikibot.WARNING)
            namespaces = [0]
        srgen = self._generator(api.PageGenerator, type_arg="search",
                                gsrsearch=searchstring, gsrwhat=where,
                                namespaces=namespaces, step=step,
                                total=total)
        if getredirects:
            srgen.request["gsrredirects"] = ""
        return srgen

    def usercontribs(self, user=None, userprefix=None, start=None, end=None,
                     reverse=False, namespaces=None, showMinor=None,
                     step=None, total=None):
        """Iterate contributions by a particular user.

        Iterated values are in the same format as recentchanges.

        @param user: Iterate contributions by this user (name or IP)
        @param userprefix: Iterate contributions by all users whose names
            or IPs start with this substring
        @param start: Iterate contributions starting at this Timestamp
        @param end: Iterate contributions ending at this Timestamp
        @param reverse: Iterate oldest contributions first (default: newest)
        @param showMinor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)

        """
        if not (user or userprefix):
            raise Error(
                "usercontribs: either user or userprefix must be non-empty")
        if start and end:
            if reverse:
                if end < start:
                    raise Error(
                "usercontribs: end must be later than start with reverse=True")
            else:
                if start < end:
                    raise Error(
                "usercontribs: start must be later than end with reverse=False")
        ucgen = self._generator(api.ListGenerator, type_arg="usercontribs",
                                ucprop="ids|title|timestamp|comment|flags",
                                namespaces=namespaces, step=step,
                                total=total)
        if user:
            ucgen.request["ucuser"] = user
        if userprefix:
            ucgen.request["ucuserprefix"] = userprefix
        if start is not None:
            ucgen.request["ucstart"] = str(start)
        if end is not None:
            ucgen.request["ucend"] = str(end)
        if reverse:
            ucgen.request["ucdir"] = "newer"
        if showMinor is not None:
            ucgen.request["ucshow"] = showMinor and "minor" or "!minor"
        return ucgen

    def watchlist_revs(self, start=None, end=None, reverse=False,
                       namespaces=None, showMinor=None, showBot=None,
                       showAnon=None, step=None, total=None):
        """Iterate revisions to pages on the bot user's watchlist.

        Iterated values will be in same format as recentchanges.

        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param showMinor: if True, only list minor edits; if False (and not
            None), only list non-minor edits
        @param showBot: if True, only list bot edits; if False (and not
            None), only list non-bot edits
        @param showAnon: if True, only list anon edits; if False (and not
            None), only list non-anon edits

        """
        if start and end:
            if reverse:
                if end < start:
                    raise Error(
            "watchlist_revs: end must be later than start with reverse=True")
            else:
                if start < end:
                    raise Error(
            "watchlist_revs: start must be later than end with reverse=False")
        wlgen = self._generator(api.ListGenerator, type_arg="watchlist",
                                wlprop="user|comment|timestamp|title|ids|flags",
                                wlallrev="", namespaces=namespaces,
                                step=step, total=total)
        #TODO: allow users to ask for "patrol" as well?
        if start is not None:
            wlgen.request["wlstart"] = str(start)
        if end is not None:
            wlgen.request["wlend"] = str(end)
        if reverse:
            wlgen.request["wldir"] = "newer"
        filters = {'minor': showMinor,
                   'bot': showBot,
                   'anon': showAnon}
        wlshow = []
        for item in filters:
            if filters[item] is not None:
                wlshow.append(filters[item] and item or ("!"+item))
        if wlshow:
            wlgen.request["wlshow"] = "|".join(wlshow)
        return wlgen

    def deletedrevs(self, page, start=None, end=None, reverse=None,
                    get_text=False, step=None, total=None):
        """Iterate deleted revisions.

        Each value returned by the iterator will be a dict containing the
        'title' and 'ns' keys for a particular Page and a 'revisions' key
        whose value is a list of revisions in the same format as
        recentchanges (plus a 'content' element if requested). If get_text
        is true, the toplevel dict will contain a 'token' key as well.

        @param page: The page to check for deleted revisions
        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param get_text: If True, retrieve the content of each revision and
            an undelete token

        """
        if start and end:
            if reverse:
                if end < start:
                    raise Error(
"deletedrevs: end must be later than start with reverse=True")
            else:
                if start < end:
                    raise Error(
"deletedrevs: start must be later than end with reverse=False")
        if not self.logged_in():
            self.login()
        if "deletedhistory" not in self.userinfo['rights']:
            try:
                self.login(True)
            except NoUsername:
                pass
            if "deletedhistory" not in self.userinfo['rights']:
                raise Error(
"deletedrevs: User:%s not authorized to access deleted revisions."
                        % self.user())
        if get_text:
            if "undelete" not in self.userinfo['rights']:
                try:
                    self.login(True)
                except NoUsername:
                    pass
                if "undelete" not in self.userinfo['rights']:
                    raise Error(
"deletedrevs: User:%s not authorized to view deleted content."
                            % self.user())

        drgen = self._generator(api.ListGenerator, type_arg="deletedrevs",
                                titles=page.title(withSection=False),
                                drprop="revid|user|comment|minor",
                                step=step, total=total)
        if get_text:
            drgen.request['drprop'] = drgen.request['drprop'] + "|content|token"
        if start is not None:
            drgen.request["drstart"] = str(start)
        if end is not None:
            drgen.request["drend"] = str(end)
        if reverse:
            drgen.request["drdir"] = "newer"
        return drgen

    def users(self, usernames):
        """Iterate info about a list of users by name or IP.

        @param usernames: a list of user names
        @type usernames: list, or other iterable, of unicodes

        """
        if not isinstance(usernames, basestring):
            usernames = u"|".join(usernames)
        usgen = api.ListGenerator(
                        "users", ususers=usernames, site=self,
                        usprop="blockinfo|groups|editcount|registration")
        return usgen

    def randompages(self, step=None, total=1, namespaces=None,
                    redirects=False):
        """Iterate a number of random pages.

        Pages are listed in a fixed sequence, only the starting point is
        random.

        @param total: the maximum number of pages to iterate (default: 1)
        @param namespaces: only iterate pages in these namespaces.
        @param redirects: if True, include only redirect pages in results
            (default: include only non-redirects)

        """
        rngen = self._generator(api.PageGenerator, type_arg="random",
                                namespaces=namespaces, step=step, total=total)
        if redirects:
            rngen.request["grnredirect"] = ""
        return rngen

    # catalog of editpage error codes, for use in generating messages
    _ep_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied":
"User %(user)s is not authorized to edit on %(site)s wiki",
        "protectedtitle":
"Title %(title)s is protected against creation on %(site)s",
        "cantcreate":
"User %(user)s not authorized to create new pages on %(site)s wiki",
        "cantcreate-anon":
"""Bot is not logged in, and anon users are not authorized to create new pages
on %(site)s wiki""",
        "articleexists": "Page %(title)s already exists on %(site)s wiki",
        "noimageredirect-anon":
"""Bot is not logged in, and anon users are not authorized to create image
redirects on %(site)s wiki""",
        "noimageredirect":
"User %(user)s not authorized to create image redirects on %(site)s wiki",
        "spamdetected":
"Edit to page %(title)s rejected by spam filter due to content:\n",
        "filtered": "%(info)s",
        "contenttoobig": "%(info)s",
        "noedit-anon":
"""Bot is not logged in, and anon users are not authorized to edit on
%(site)s wiki""",
        "noedit": "User %(user)s not authorized to edit pages on %(site)s wiki",
        "pagedeleted":
"Page %(title)s has been deleted since last retrieved from %(site)s wiki",
        "editconflict": "Page %(title)s not saved due to edit conflict.",
    }

    def editpage(self, page, summary, minor=True, notminor=False,
                 recreate=True, createonly=False, watch=False, unwatch=False):
        """Submit an edited Page object to be saved to the wiki.

        @param page: The Page to be saved; its .text property will be used
            as the new text to be saved to the wiki
        @param token: the edit token retrieved using Site.token()
        @param summary: the edit summary (required!)
        @param minor: if True (default), mark edit as minor
        @param notminor: if True, override account preferences to mark edit
            as non-minor
        @param recreate: if True (default), create new page even if this
            title has previously been deleted
        @param createonly: if True, raise an error if this title already
            exists on the wiki
        @param watch: if True, add this Page to bot's watchlist
        @param unwatch: if True, remove this Page from bot's watchlist if
            possible
        @return: True if edit succeeded, False if it failed

        """
        text = page.text
        if not text:
            raise Error("editpage: no text to be saved")
        try:
            lastrev = page.latestRevision()
        except NoPage:
            lastrev = None
            if not recreate:
                raise
        token = self.token(page, "edit")
        # getting token also updates the 'lastrevid' value, which allows us to
        # detect if page has been changed since last time text was retrieved.

        # note that the server can still return an 'editconflict' error
        # if the page is updated after the token is retrieved but
        # before the page is saved.
        self.lock_page(page)
        if lastrev is not None and page.latestRevision() != lastrev:
            raise EditConflict(
                "editpage: Edit conflict detected; saving aborted.")
        req = api.Request(site=self, action="edit",
                          title=page.title(withSection=False),
                          text=text, token=token, summary=summary)
        if lastrev is not None:
            req["basetimestamp"] = page._revisions[lastrev].timestamp
        if minor:
            req['minor'] = ""
        elif notminor:
            req['notminor'] = ""
        if 'bot' in self.userinfo['groups']:
            req['bot'] = ""
        if recreate:
            req['recreate'] = ""
        if createonly:
            req['createonly'] = ""
        if watch:
            req['watch'] = ""
        elif unwatch:
            req['unwatch'] = ""
## FIXME: API gives 'badmd5' error
##        md5hash = md5()
##        md5hash.update(urllib.quote_plus(text.encode(self.encoding())))
##        req['md5'] = md5hash.digest()
        while True:
            try:
                result = req.submit()
                pywikibot.output(u"editpage response: %s" % result,
                                 level=pywikibot.DEBUG)
            except api.APIError, err:
                self.unlock_page(page)
                if err.code.endswith("anon") and self.logged_in():
                    pywikibot.output(
u"editpage: received '%s' even though bot is logged in" % err.code,
                                     level=pywikibot.DEBUG)
                errdata = {
                    'site': self,
                    'title': page.title(withSection=False),
                    'user': self.user(),
                    'info': err.info
                }
                if err.code == "spamdetected":
                    raise SpamfilterError(self._ep_errors[err.code] % errdata
                            + err.info[ err.info.index("fragment: ") + 9: ])

                if err.code == "editconflict":
                    raise EditConflict(self._ep_errors[err.code] % errdata)
                if err.code in ("protectedpage", "cascadeprotected"):
                    raise LockedPage(errdata['title'])
                if err.code in self._ep_errors:
                    raise Error(self._ep_errors[err.code] % errdata)
                pywikibot.output(
                    u"editpage: Unexpected error code '%s' received."
                        % err.code,
                    level=pywikibot.DEBUG)
                raise
            assert ("edit" in result and "result" in result["edit"]), result
            if result["edit"]["result"] == "Success":
                self.unlock_page(page)
                if "nochange" in result["edit"]:
                    # null edit, page not changed
                    #TODO: do we want to notify the user of this?
                    return True
                page._revid = result["edit"]["newrevid"]
                # see http://www.mediawiki.org/wiki/API:Wikimania_2006_API_discussion#Notes
                # not safe to assume that saved text is the same as sent
                self.loadrevisions(page, getText=True)
                return True
            elif result["edit"]["result"] == "Failure":
                if "captcha" in result["edit"]:
                    captcha = result["edit"]["captcha"]
                    req['captchaid'] = captcha['id']
                    if captcha["type"] == "math":
                        req['captchaword'] = input(captcha["question"])
                        continue
                    elif "url" in captcha:
                        webbrowser.open(url)
                        req['captchaword'] = cap_answerwikipedia.input(
"Please view CAPTCHA in your browser, then type answer here:")
                        continue
                    else:
                        self.unlock_page(page)
                        pywikibot.output(
                    u"editpage: unknown CAPTCHA response %s, page not saved"
                                         % captcha,
                                         level=pywikibot.ERROR)
                        return False
                else:
                    self.unlock_page(page)
                    pywikibot.output(u"editpage: unknown failure reason %s"
                                      % str(result),
                                     level=pywikibot.ERROR)
                    return False
            else:
                self.unlock_page(page)
                pywikibot.output(
u"editpage: Unknown result code '%s' received; page not saved"
                                   % result["edit"]["result"],
                                 level=pywikibot.ERROR)
                pywikibot.output(str(result), level=pywikibot.VERBOSE)
                return False

    # catalog of move errors for use in error messages
    _mv_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied":
"User %(user)s is not authorized to edit on %(site)s wiki",
        "nosuppress":
"User %(user)s is not authorized to move pages without creating redirects",
        "cantmove-anon":
"""Bot is not logged in, and anon users are not authorized to move pages on
%(site)s wiki""",
        "cantmove":
"User %(user)s is not authorized to move pages on %(site)s wiki",
        "immobilenamespace":
"Pages in %(oldnamespace)s namespace cannot be moved on %(site)s wiki",
        "articleexists":
"Cannot move because page [[%(newtitle)s]] already exists on %(site)s wiki",
        "protectedpage":
"Page [[%(oldtitle)s]] is protected against moving on %(site)s wiki",
        "protectedtitle":
"Page [[%(newtitle)s]] is protected against creation on %(site)s wiki",
        "nonfilenamespace":
"Cannot move a file to %(newnamespace)s namespace on %(site)s wiki",
        "filetypemismatch":
"[[%(newtitle)s]] file extension does not match content of [[%(oldtitle)s]]"
    }

    def movepage(self, page, newtitle, summary, movetalk=True,
                 noredirect=False):
        """Move a Page to a new title.

        @param page: the Page to be moved (must exist)
        @param newtitle: the new title for the Page
        @type newtitle: unicode
        @param summary: edit summary (required!)
        @param movetalk: if True (default), also move the talk page if possible
        @param noredirect: if True, suppress creation of a redirect from the
            old title to the new one
        @return: Page object with the new title

        """
        oldtitle = page.title(withSection=False)
        newlink = pywikibot.Link(newtitle, self)
        if newlink.namespace:
            newtitle = self.namespace(newlink.namespace) + ":" + newlink.title
        else:
            newtitle = newlink.title
        if oldtitle == newtitle:
            raise Error("Cannot move page %s to its own title."
                        % oldtitle)
        if not page.exists():
            raise Error("Cannot move page %s because it does not exist on %s."
                        % (oldtitle, self))
        token = self.token(page, "move")
        self.lock_page(page)
        req = api.Request(site=self, action="move", to=newtitle,
                          token=token, reason=summary)
        req['from'] = oldtitle  # "from" is a python keyword
        if movetalk:
            req['movetalk'] = ""
        if noredirect:
            req['noredirect'] = ""
        try:
            result = req.submit()
            pywikibot.output(u"movepage response: %s" % result,
                             level=pywikibot.DEBUG)
        except api.APIError, err:
            if err.code.endswith("anon") and self.logged_in():
                pywikibot.output(
u"movepage: received '%s' even though bot is logged in" % err.code,
                                 level=pywikibot.DEBUG)
            errdata = {
                'site': self,
                'oldtitle': oldtitle,
                'oldnamespace': self.namespace(page.namespace()),
                'newtitle': newtitle,
                'newnamespace': self.namespace(newlink.namespace),
                'user': self.user(),
            }
            if err.code in self._mv_errors:
                raise Error(self._mv_errors[err.code] % errdata)
            pywikibot.output(u"movepage: Unexpected error code '%s' received."
                                 % err.code,
                             level=pywikibot.DEBUG)
            raise
        finally:
            self.unlock_page(page)
        if "move" not in result:
            pywikibot.output(u"movepage: %s" % result, level=pywikibot.ERROR)
            raise Error("movepage: unexpected response")
        #TODO: Check for talkmove-error messages
        if "talkmove-error-code" in result["move"]:
            pywikibot.output(u"movepage: Talk page %s not moved"
                              % (page.toggleTalkPage().title(asLink=True)),
                             level=pywikibot.WARNING)
        return pywikibot.Page(page, newtitle)

    # catalog of rollback errors for use in error messages
    _rb_errors = {
        "noapiwrite":
            "API editing not enabled on %(site)s wiki",
        "writeapidenied":
            "User %(user)s not allowed to edit through the API",
        "alreadyrolled":
            "Page [[%(title)s]] already rolled back; action aborted.",
    } # other errors shouldn't arise because we check for those errors

    def rollbackpage(self, page, summary=u''):
        """Roll back page to version before last user's edits.

        As a precaution against errors, this method will fail unless
        the page history contains at least two revisions, and at least
        one that is not by the same user who made the last edit.

        @param page: the Page to be rolled back (must exist)
        @param summary: edit summary (defaults to a standardized message)

        """
        if len(page._revisions) < 2:
            raise pywikibot.Error(
                  u"Rollback of %s aborted; load revision history first."
                    % page.title(asLink=True))
        last_rev = page._revisions[page.latestRevision()]
        last_user = last_rev.user
        for rev in sorted(page._revisions.keys(), reverse=True):
            # start with most recent revision first
            if rev.user != last_user:
                prev_user = rev.user
                break
        else:
            raise pywikibot.Error(
                  u"Rollback of %s aborted; only one user in revision history."
                   % page.title(asLink=True))
        summary = summary or (
u"Reverted edits by [[Special:Contributions/%(last_user)s|%(last_user)s]] "
u"([[User talk:%(last_user)s|Talk]]) to last version by %(prev_user)s"
                  % locals())
        token = self.token(page, "rollback")
        self.lock_page(page)
        req = api.Request(site=self, action="rollback",
                          title=page.title(withSection=False),
                          user=last_user,
                          token=token)
        try:
            result = req.submit()
        except api.APIError, err:
            errdata = {
                'site': self,
                'title': page.title(withSection=False),
                'user': self.user(),
            }
            if err.code in self._rb_errors:
                raise Error(self._rb_errors[err.code] % errdata)
            pywikibot.output(u"rollback: Unexpected error code '%s' received."
                                 % err.code,
                             level=pywikibot.DEBUG)
            raise
        finally:
            self.unlock_page(page)

    # catalog of delete errors for use in error messages
    _dl_errors = {
        "noapiwrite":
            "API editing not enabled on %(site)s wiki",
        "writeapidenied":
            "User %(user)s not allowed to edit through the API",
        "permissiondenied":
            "User %(user)s not authorized to delete pages on %(site)s wiki.",
        "cantdelete":
            "Could not delete [[%(title)s]]. Maybe it was deleted already.",
    } # other errors shouldn't occur because of pre-submission checks

    def deletepage(self, page, summary):
        """Delete page from the wiki. Requires appropriate privilege level.

        @param page: Page to be deleted.
        @param summary: Edit summary (required!).

        """
        try:
            self.login(sysop=True)
        except pywikibot.NoUsername, e:
            raise NoUsername("delete: Unable to login as sysop (%s)"
                        % e.__class__.__name__)
        if not self.logged_in(sysop=True):
            raise NoUsername("delete: Unable to login as sysop")
        token = self.token(page, "delete")
        self.lock_page(page)
        req = api.Request(site=self, action="delete", token=token,
                          title=page.title(withSection=False),
                          reason=summary)
        try:
            result = req.submit()
        except api.APIError, err:
            errdata = {
                'site': self,
                'title': page.title(withSection=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.output(u"delete: Unexpected error code '%s' received."
                                 % err.code,
                             level=pywikibot.DEBUG)
            raise
        finally:
            self.unlock_page(page)

    #TODO: implement undelete

    #TODO: implement patrol

    @deprecated("Site().exturlusage")
    def linksearch(self, siteurl, limit=None):
        """Backwards-compatible interface to exturlusage()"""
        return self.exturlusage(siteurl, total=limit)

    @deprecated('Site().logevents(logtype="upload",...)')
    @deprecate_arg("repeat", None)
    def newimages(self, number=100, lestart=None, leend=None, leuser=None,
                  letitle=None):
        """Yield ImagePages from most recent uploads"""
        if isinstance(letitle, basestring):
            letitle = pywikbot.Page(pywikibot.Link(letitle))
        return self.logevents(logtype="upload", total=number, start=lestart,
                              end=leend, user=leuser, page=letitle)

    def getImagesFromAnHash(self, hash_found=None):
        """Return all images that have the same hash.

        Useful to find duplicates or nowcommons.

        NOTE: it returns also the image itself, if you don't want it, just
        filter the list returned.

        NOTE 2: it returns the image title WITHOUT the image namespace.

        """
        if hash_found == None: # If the hash is none return None and not continue
            return None
        return [image.title(withNamespace=False)
                for image in self.allimages(sha1=hash_found)]

    def upload(self, imagepage, source_filename=None, source_url=None,
               comment=None, watch=False, ignore_warnings=False):
        """Upload a file to the wiki.

        Either source_filename or source_url, but not both, must be provided.

        @param imagepage: an ImagePage object from which the wiki-name of the
            file will be obtained.
        @param source_filename: path to the file to be uploaded
        @param source_url: URL of the file to be uploaded
        @param comment: Edit summary; if this is not provided, then
            imagepage.text will be used. An empty summary is not permitted.
        @param watch: If true, add imagepage to the bot user's watchlist
        @param ignore_warnings: if true, ignore API warnings and force
            upload (for example, to overwrite an existing file); default False

        """
        upload_warnings = {
            # map API warning codes to user error messages
            # %(msg)s will be replaced by message string from API responsse
            'duplicate-archive':
                "The file is a duplicate of a deleted file %(msg)s.",
            'was-deleted':
                "The file %(msg)s was previously deleted.",
            'emptyfile':
                "File %(msg)s is empty.",
            'exists':
                "File %(msg)s already exists.",
            'duplicate':
                "Uploaded file is a duplicate of %(msg)s.",
            'badfilename':
                "Target filename is invalid.",
             'filetype-unwanted-type':
                "File %(msg)s type is unwatched type.",
        }

        # check for required user right
        if "upload" not in self.userinfo["rights"]:
            raise pywikibot.Error(
                "User '%s' does not have upload rights on site %s."
                % (self.user(), self))
        # check for required parameters
        if (source_filename and source_url)\
                or (source_filename is None and source_url is None):
            raise ValueError(
"APISite.upload: must provide either source_filename or source_url, not both."
            )
        if comment is None:
            comment = imagepage.text
        if not comment:
            raise ValueError(
"APISite.upload: cannot upload file without a summary/description."
            )
        token = self.token(imagepage, "edit")
        if source_filename:
            # upload local file
            # make sure file actually exists
            if not os.path.isfile(source_filename):
                raise ValueError("File '%s' does not exist."
                                 % source_filename)
            filesize = os.path.getsize(source_filename)
            # TODO: if file size exceeds some threshold (to be determined),
            #       upload by chunks
            req = api.Request(site=self, action="upload", token=token,
                              filename=imagepage.title(withNamespace=False),
                              file=source_filename, comment=comment,
                              mime=True)
        else:
            # upload by URL
            if "upload_by_url" not in self.userinfo["rights"]:
                raise pywikibot.Error(
                    "User '%s' is not authorized to upload by URL on site %s."
                    % (self.user(), self))
            req = api.Request(site=self, action="upload", token=token,
                              filename=imagepage.title(withNamespace=False),
                              url=source_url, comment=comment)
        if watch:
            req["watch"] = ""
        if ignore_warnings:
            req["ignorewarnings"] = ""
        try:
            result = req.submit()
        except api.APIError, err:
            # TODO: catch and process foreseeable errors
            raise
        result = result["upload"]
        pywikibot.output(result, level=pywikibot.DEBUG)
        if "warnings" in result:
            warning = result["warnings"].keys()[0]
            message = result["warnings"][warning]
            raise pywikibot.UploadWarning(upload_warnings[warning]
                                          % {'msg': message})
        elif "result" not in result:
            pywikibot.output(u"Upload: unrecognized response: %s"
                              % result)
        if result["result"] == "Success":
            pywikibot.output(u"Upload successful.")
            imagepage._imageinfo = result["imageinfo"]
            return


#### METHODS NOT IMPLEMENTED YET ####
class NotImplementedYet:

    #TODO: is this needed any more? can it be obtained from the http module?
    def cookies(self, sysop = False):
        """Return a string containing the user's current cookies."""
        self._loadCookies(sysop = sysop)
        index = self._userIndex(sysop)
        return self._cookies[index]

    def _loadCookies(self, sysop = False):
        """Retrieve session cookies for login"""
        index = self._userIndex(sysop)
        if self._cookies[index] is not None:
            return
        try:
            if sysop:
                try:
                    username = config.sysopnames[self.family.name
                                                            ][self.code]
                except KeyError:
                    raise NoUsername("""\
You tried to perform an action that requires admin privileges, but you haven't
entered your sysop name in your user-config.py. Please add
sysopnames['%s']['%s']='name' to your user-config.py"""
                                     % (self.family.name, self.code))
            else:
                username = pywikibot.config2.usernames[self.family.name
                                                       ][self.code]
        except KeyError:
            self._cookies[index] = None
            self._isLoggedIn[index] = False
        else:
            tmp = '%s-%s-%s-login.data' % (
                    self.family.name, self.code, username)
            fn = config.datafilepath('login-data', tmp)
            if not os.path.exists(fn):
                self._cookies[index] = None
                self._isLoggedIn[index] = False
            else:
                f = open(fn)
                self._cookies[index] = '; '.join([x.strip() for x in f.readlines()])
                f.close()

    # THESE ARE FUNCTIONS NOT YET IMPLEMENTED IN THE API
    #TODO: avoid code duplication for the following methods
    def newpages(self, number = 10, get_redirect = False, repeat = False):
        """Yield new articles (as Page objects) from Special:Newpages.

        Starts with the newest article and fetches the number of articles
        specified in the first argument. If repeat is True, it fetches
        Newpages again. If there is no new page, it blocks until there is
        one, sleeping between subsequent fetches of Newpages.

        The objects yielded are tuples composed of the Page object,
        timestamp (unicode), length (int), an empty unicode string, username
        or IP address (str), comment (unicode).

        """
        # TODO: in recent MW versions Special:Newpages takes a namespace parameter,
        #       and defaults to 0 if not specified.
        # TODO: Detection of unregistered users is broken
        # TODO: Repeat mechanism doesn't make much sense as implemented;
        #       should use both offset and limit parameters, and have an
        #       option to fetch older rather than newer pages
        seen = set()
        while True:
            path = self.newpages_address(n=number)
            # The throttling is important here, so always enabled.
            get_throttle()
            html = self.getUrl(path)

            entryR = re.compile(
'<li[^>]*>(?P<date>.+?) \S*?<a href=".+?"'
' title="(?P<title>.+?)">.+?</a>.+?[\(\[](?P<length>[\d,.]+)[^\)\]]*[\)\]]'
' .?<a href=".+?" title=".+?:(?P<username>.+?)">'
                                )
            for m in entryR.finditer(html):
                date = m.group('date')
                title = m.group('title')
                title = title.replace('&quot;', '"')
                length = int(re.sub("[,.]", "", m.group('length')))
                loggedIn = u''
                username = m.group('username')
                comment = u''

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, date, length, loggedIn, username, comment
            if not repeat:
                break

    def longpages(self, number = 10, repeat = False):
        """Yield Pages from Special:Longpages.

        Return values are a tuple of Page object, length(int).

        """
        #TODO: should use offset and limit parameters; 'repeat' as now
        #      implemented is fairly useless
        # this comment applies to all the XXXXpages methods following, as well
        seen = set()
        while True:
            path = self.longpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(ur'<li>\(<a href=".+?" title=".+?">hist</a>\) ‎<a href=".+?" title="(?P<title>.+?)">.+?</a> ‎\[(?P<length>\d+)(.+?)\]</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                length = int(m.group('length'))
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, length
            if not repeat:
                break

    def shortpages(self, number = 10, repeat = False):
        """Yield Pages and lengths from Special:Shortpages."""
        throttle = True
        seen = set()
        while True:
            path = self.shortpages_address(n = number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(ur'<li>\(<a href=".+?" title=".+?">hist</a>\) ‎<a href=".+?" title="(?P<title>.+?)">.+?</a> ‎\[(?P<length>\d+)(.+?)\]</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                length = int(m.group('length'))

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, length
            if not repeat:
                break

    def deadendpages(self, number = 10, repeat = False):
        """Yield Page objects retrieved from Special:Deadendpages."""
        seen = set()
        while True:
            path = self.deadendpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def ancientpages(self, number = 10, repeat = False):
        """Yield Pages, datestamps from Special:Ancientpages."""
        seen = set()
        while True:
            path = self.ancientpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
'<li><a href=".+?" title="(?P<title>.+?)">.+?</a> (?P<date>.+?)</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                date = m.group('date')
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page, date
            if not repeat:
                break

    def lonelypages(self, number = 10, repeat = False):
        """Yield Pages retrieved from Special:Lonelypages."""
        throttle = True
        seen = set()
        while True:
            path = self.lonelypages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def unwatchedpages(self, number = 10, repeat = False):
        """Yield Pages from Special:Unwatchedpages (requires Admin privileges)."""
        seen = set()
        while True:
            path = self.unwatchedpages_address(n=number)
            get_throttle()
            html = self.getUrl(path, sysop = True)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a>.+?</li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def uncategorizedcategories(self, number = 10, repeat = False):
        """Yield Categories from Special:Uncategorizedcategories."""
        import catlib
        seen = set()
        while True:
            path = self.uncategorizedcategories_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = catlib.Category(self, title)
                    yield page
            if not repeat:
                break

    def newimages(self, number = 10, repeat = False):
        """Yield ImagePages from Special:Log&type=upload"""

        seen = set()
        regexp = re.compile('<li[^>]*>(?P<date>.+?)\s+<a href=.*?>(?P<user>.+?)</a>\s+\(.+?</a>\).*?<a href=".*?"(?P<new> class="new")? title="(?P<image>.+?)"\s*>(?:.*?<span class="comment">(?P<comment>.*?)</span>)?', re.UNICODE)

        while True:
            path = self.log_address(number, mode = 'upload')
            get_throttle()
            html = self.getUrl(path)

            for m in regexp.finditer(html):
                image = m.group('image')

                if image not in seen:
                    seen.add(image)

                    if m.group('new'):
                        output(u"Image \'%s\' has been deleted." % image)
                        continue

                    date = m.group('date')
                    user = m.group('user')
                    comment = m.group('comment') or ''

                    yield ImagePage(self, image), date, user, comment
            if not repeat:
                break

    def uncategorizedimages(self, number = 10, repeat = False):
        """Yield ImagePages from Special:Uncategorizedimages."""
        seen = set()
        ns = self.image_namespace()
        entryR = re.compile(
            '<a href=".+?" title="(?P<title>%s:.+?)">.+?</a>' % ns)
        while True:
            path = self.uncategorizedimages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = ImagePage(self, title)
                    yield page
            if not repeat:
                break

    def uncategorizedpages(self, number = 10, repeat = False):
        """Yield Pages from Special:Uncategorizedpages."""
        seen = set()
        while True:
            path = self.uncategorizedpages_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile(
                '<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def unusedcategories(self, number = 10, repeat = False):
        """Yield Category objects from Special:Unusedcategories."""
        import catlib
        seen = set()
        while True:
            path = self.unusedcategories_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile('<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')

                if title not in seen:
                    seen.add(title)
                    page = catlib.Category(self, title)
                    yield page
            if not repeat:
                break

    def unusedfiles(self, number = 10, repeat = False, extension = None):
        """Yield ImagePage objects from Special:Unusedimages."""
        seen = set()
        ns = self.image_namespace()
        entryR = re.compile(
            '<a href=".+?" title="(?P<title>%s:.+?)">.+?</a>' % ns)
        while True:
            path = self.unusedfiles_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            for m in entryR.finditer(html):
                fileext = None
                title = m.group('title')
                if extension:
                    fileext = title[len(title)-3:]
                if title not in seen and fileext == extension:
                    ## Check whether the media is used in a Proofread page
                    # code disabled because it slows this method down, and
                    # because it is unclear what it's supposed to do.
                    #basename = title[6:]
                    #page = Page(self, 'Page:' + basename)

                    #if not page.exists():
                    seen.add(title)
                    image = ImagePage(self, title)
                    yield image
            if not repeat:
                break

    def withoutinterwiki(self, number=10, repeat=False):
        """Yield Pages without language links from Special:Withoutinterwiki."""
        seen = set()
        while True:
            path = self.withoutinterwiki_address(n=number)
            get_throttle()
            html = self.getUrl(path)
            entryR = re.compile('<li><a href=".+?" title="(?P<title>.+?)">.+?</a></li>')
            for m in entryR.finditer(html):
                title = m.group('title')
                if title not in seen:
                    seen.add(title)
                    page = Page(self, title)
                    yield page
            if not repeat:
                break

    def linksearch(self, siteurl):
        """Yield Pages from results of Special:Linksearch for 'siteurl'."""
        if siteurl.startswith('*.'):
            siteurl = siteurl[2:]
        output(u'Querying [[Special:Linksearch]]...')
        cache = []
        for url in [siteurl, '*.' + siteurl]:
            path = self.linksearch_address(url)
            get_throttle()
            html = self.getUrl(path)
            loc = html.find('<div class="mw-spcontent">')
            if loc > -1:
                html = html[loc:]
            loc = html.find('<div class="printfooter">')
            if loc > -1:
                html = html[:loc]
            R = re.compile('title ?=\"(.*?)\"')
            for title in R.findall(html):
                if not siteurl in title:
                    # the links themselves have similar form
                    if title in cache:
                        continue
                    else:
                        cache.append(title)
                        yield Page(self, title)

