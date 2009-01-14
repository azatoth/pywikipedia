# -*- coding: utf-8  -*-
"""
Objects representing various types of MediaWiki pages.
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
import pywikibot.site

import htmlentitydefs
import logging
import re
import sys
import threading
import unicodedata
import urllib

logger = logging.getLogger("wiki.page")

reNamespace = re.compile("^(.+?) *: *(.*)$")


class Page(object):
    """Page: A MediaWiki page

    This object only implements internally methods that do not require
    reading from or writing to the wiki.  All other methods are delegated
    to the Site object. 

    """

#    @deprecate_arg("insite", None)
#    @deprecate_arg("defaultNamespace", None)
    def __init__(self, source, title=u"", ns=0):
        """Instantiate a Page object.

        Three calling formats are supported:

          - If the first argument is a Page, create a copy of that object.
            This can be used to convert an existing Page into a subclass
            object, such as Category or ImagePage.  (If the title is also
            given as the second argument, creates a copy with that title;
            this is used when pages are moved.)
          - If the first argument is a Site, create a Page on that Site
            using the second argument as the title (may include a section),
            and the third as the namespace number. The namespace number is
            mandatory, even if the title includes the namespace prefix. This
            is the preferred syntax when using an already-normalized title
            obtained from api.php or a database dump.  WARNING: may produce
            invalid objects if page title isn't in normal form!
          - If the first argument is a Link, create a Page from that link.
            This is the preferred syntax when using a title scraped from
            wikitext, URLs, or another non-normalized source.

        @param source: the source of the page
        @type source: Link, Page (or subclass), or Site
        @param title: normalized title of the page; required if source is a
            Site, ignored otherwise
        @type title: unicode
        @param ns: namespace number; required if source is a Site, ignored
            otherwise
        @type ns: int

        """
        if isinstance(source, pywikibot.site.BaseSite):
            self._site = source
            if ns not in source.namespaces():
                raise pywikibot.Error(
                      "Invalid namespace '%i' for site %s."
                      % (ns, source.sitename()))
            self._ns = ns
            if ns and not title.startswith(source.namespace(ns)+u":"):
                title = source.namespace(ns) + u":" + title
            elif not ns and u":" in title:
                pos = title.index(u':')
                nsindex = source.ns_index(title[ :pos])
                if nsindex:
                    self._ns = nsindex
            if u"#" in title:
                title, self._section = title.split(u"#", 1)
            else:
                self._section = None
            if not title:
                raise pywikibot.Error(
                      "Page object cannot be created from Site without title.")
            self._title = title
        elif isinstance(source, Page): 
            # copy all of source's attributes to this object
            self.__dict__ = source.__dict__
            if title:
                # overwrite title
                if ":" in title:
                    prefix = title[ :title.index(":")]
                    self._ns = site.ns_index(prefix)
                    if self._ns is None:
                        self._ns = 0
                    else:
                        title = title[title.index(":")+1 : ].strip(" _")
                        self._title = "%s:%s" % (
                                         self.site().namespace(self._ns),
                                         self._title)
                else:
                    self._ns = 0
                if "#" in title:
                    self._section = title[title.index("#") + 1 : ].strip(" _")
                    title = title[ : title.index("#")].strip(" _")
                self._title = title
        elif isinstance(source, Link):
            self._site = source.site
            self._section = source.section
            self._ns = source.namespace
            self._title = source.title
            # reassemble the canonical title from components
            if self._ns:
                self._title = "%s:%s" % (self.site().namespace(self._ns),
                                         self._title)
        else:
            raise pywikibot.Error(
                  "Invalid argument type '%s' in Page constructor: %s"
                  % (type(source), source))
        if self._section is not None:
            self._title = self._title + "#" + self._section
        self._revisions = {}

    def site(self):
        """Return the Site object for the wiki on which this Page resides."""
        return self._site

    def namespace(self):
        """Return the number of the namespace of the page."""
        return self._ns

    @deprecate_arg("decode", None)
    @deprecate_arg("savetitle", "asUrl")
    def title(self, underscore=False, savetitle=False, withNamespace=True,
              withSection=True, asUrl=False, asLink=False,
              allowInterwiki=True, forceInterwiki=False, textlink=False,
              as_filename=False):
        """Return the title of this Page, as a Unicode string.

        @param underscore: if true, replace all ' ' characters with '_'
        @param withNamespace: if false, omit the namespace prefix
        @param withSection: if false, omit the section
        @param asUrl: if true, quote title as if in an URL
        @param asLink: if true, return the title in the form of a wikilink
        @param allowInterwiki: (only used if asLink is true) if true, format
            the link as an interwiki link if necessary
        @param forceInterwiki: (only used if asLink is true) if true, always
            format the link as an interwiki link
        @param textlink: (only used if asLink is true) if true, place a ':'
            before Category: and Image: links
        @param as_filename: if true, replace any characters that are unsafe
            in filenames

        """
        title = self._title
        if not withNamespace and self._ns != 0:
            title = title.split(u':', 1)[1]
        if not withSection and self._section:
            title = title.split(u'#', 1)[0]
        if underscore or asUrl:
            title = title.replace(u' ', u'_')
        if asUrl:
            encodedTitle = title.encode(self.site().encoding())
            title = urllib.quote(encodedTitle)
        if asLink:
            if forceInterwiki or (allowInterwiki and
                    (self.site().family.name != config.family
                     or self.site().code != config.mylang)):
                if self.site().family.name != config.family \
                        and self.site().family.name != self.site().code:
                    return u'[[%s:%s:%s]]' % (self.site().family.name,
                                              self.site().code,
                                              self._title)
                else:
                    # use this form for sites like commons, where the
                    # code is the same as the family name
                    return u'[[%s:%s]]' % (self.site().code,
                                           self._title)
            elif textlink and (self.isImage() or self.isCategory()):
                    return u'[[:%s]]' % title
            else:
                return u'[[%s]]' % title
        if as_filename:
            # Replace characters that are not possible in file names on some
            # systems.
            # Spaces are possible on most systems, but are bad for URLs.
            for forbidden in ':*?/\\ ':
                title = title.replace(forbidden, '_')
        return title

    @deprecate_arg("decode", None)
    @deprecate_arg("underscore", None)
    def section(self):
        """Return the name of the section this Page refers to.

        The section is the part of the title following a '#' character, if
        any. If no section is present, return None.

        """
        if self._section:
            return self._section
        else:
            return None

    def __str__(self):
        """Return a console representation of the pagelink."""
        return self.title(asLink=True, forceInterwiki=True
                          ).encode(sys.stderr.encoding)

    def __unicode__(self):
        return self.title(asLink=True, forceInterwiki=True)

    def __repr__(self):
        """Return a more complete string representation."""
        return u"%s(%s)" % (self.__class__.__name__,
                            self.title().encode(sys.stderr.encoding))

    def __cmp__(self, other):
        """Test for equality and inequality of Page objects.

        Page objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Page objects are sortable by namespace first, then by title.

        """
        if not isinstance(other, Page):
            # especially, return -1 if other is None
            return -1
        if not self.site() == other.site():
            return cmp(self.site(), other.site())
        if self.namespace() != other.namespace():
            return cmp(self.namespace(), other.namespace())
        owntitle = self.title(withNamespace=False)
        othertitle = other.title(withNamespace=False)
        return cmp(owntitle, othertitle)

    def __hash__(self):
        # Pseudo method that makes it possible to store Page objects as keys
        # in hash-tables. This relies on the fact that the string
        # representation of an instance can not change after the construction.
        return hash(unicode(self))

    def autoFormat(self):
        """Return L{date.autoFormat} dictName and value, if any.

        Value can be a year, date, etc., and dictName is 'YearBC',
        'Year_December', or another dictionary name. Please note that two
        entries may have exactly the same autoFormat, but be in two
        different namespaces, as some sites have categories with the
        same names. Regular titles return (None, None).

        """
        if not hasattr(self, '_autoFormat'):
            from pywikibot import date
            self._autoFormat = date.getAutoFormat(
                                        self.site().code,
                                        self.title(withNamespace=False)
                                    )
        return self._autoFormat

    def isAutoTitle(self):
        """Return True if title of this Page is in the autoFormat dictionary."""
        return self.autoFormat()[0] is not None

    @deprecate_arg("throttle", None)
    @deprecate_arg("nofollow_redirects", None)
    @deprecate_arg("change_edit_time", None)
    def get(self, force=False, get_redirect=False, sysop=False):
        """Return the wiki-text of the page.

        This will retrieve the page from the server if it has not been
        retrieved yet, or if force is True. This can raise the following
        exceptions that should be caught by the calling code:

          - NoPage: The page does not exist
          - IsRedirectPage: The page is a redirect. The argument of the
                exception is the title of the page it redirects to.
          - SectionError: The section does not exist on a page with a #
                link

        @param force: reload all page attributes, including errors.
        @param get_redirect: return the redirect text, do not follow the
            redirect, do not raise an exception.
        @param sysop: if the user has a sysop account, use it to retrieve
            this page

        """
        if force:
            # When forcing, we retry the page no matter what. Old exceptions
            # do not apply any more.
            for attr in ['_redirarg', '_getexception']:
                if hasattr(self, attr):
                    delattr(self,attr)
        else:
            # Make sure we re-raise an exception we got on an earlier attempt
            if hasattr(self, '_redirarg') and not get_redirect:
                raise pywikibot.IsRedirectPage, self._redirarg
            elif hasattr(self, '_getexception'):
                raise self._getexception
        if force or not hasattr(self, "_revid") \
                 or not self._revid in self._revisions \
                 or self._revisions[self._revid].text is None:
            self.site().loadrevisions(self, getText=True, sysop=sysop)
            # TODO: Exception handling for no-page, redirects, etc.

        return self._revisions[self._revid].text

    @deprecate_arg("throttle", None)
    @deprecate_arg("nofollow_redirects", None)
    @deprecate_arg("change_edit_time", None)
    def getOldVersion(self, oldid, force=False, get_redirect=False,
                      sysop=False):
        """Return text of an old revision of this page; same options as get().

        @param oldid: The revid of the revision desired.

        """
        if force or not oldid in self._revisions \
                or self._revisions[oldid].text is None:
            self.site().loadrevisions(self, getText=True, revids=oldid,
                                      sysop=sysop)
        # TODO: what about redirects, errors?
        return self._revisions[oldid].text

    def permalink(self):
        """Return the permalink URL for current revision of this page."""
        return "%s://%s/%sindex.php?title=%s&oldid=%s" \
               % (self.site().protocol(),
                  self.site().hostname(),
                  self.site().scriptpath(),
                  self.title(asUrl=True),
                  self.latestRevision())

    def latestRevision(self):
        """Return the current revision id for this page."""
        if not hasattr(self, '_revid'):
            self.site().loadrevisions(self)
        return self._revid

    def _textgetter(self):
        """Return the current (edited) wikitext, loading it if necessary."""
        if not hasattr(self, '_text') or self._text is None:
            try:
                self._text = self.get()
            except pywikibot.NoPage:
                # TODO: what other exceptions might be returned?
                self._text = u""
        return self._text

    def _textsetter(self, value):
        """Update the edited wikitext"""
        self._text = unicode(value)

    def _cleartext(self):
        """Delete the edited wikitext"""
        if hasattr(self, "_text"):
            del self._text

    text = property(_textgetter, _textsetter, _cleartext,
                    "The edited wikitext (unicode) of this Page")

    def expand_text(self):
        """Return the page text with all templates expanded."""
        req = pywikibot.data.api.Request(action="expandtemplates",
                                         text=self.text,
                                         title=self.title(withSection=False),
                                         site=self.site())
        result = req.submit()
        return result["expandtemplates"]["*"]

    def userName(self):
        """Return name or IP address of last user to edit page."""
        return self._revisions[self.latestRevision()].user

    def isIpEdit(self):
        """Return True if last editor was unregistered."""
        return self._revisions[self.latestRevision()].anon

    def editTime(self):
        """Return timestamp (in ISO 8601 format) of last revision to page."""
        return self._revisions[self.latestRevision()].timestamp

    def previousRevision(self):
        """Return the revision id for the previous revision of this Page."""
        vh = self.getVersionHistory(revCount=2)
        revkey = sorted(self._revisions.keys(), reverse=True)[1]
        return revkey

    def exists(self):
        """Return True if page exists on the wiki, even if it's a redirect.

        If the title includes a section, return False if this section isn't
        found.

        """
        return self.site().page_exists(self)

    def isRedirectPage(self):
        """Return True if this is a redirect, False if not or not existing."""
        return self.site().page_isredirect(self)

    def isEmpty(self):
        """Return True if the page text has less than 4 characters.

        Character count ignores language links and category links.
        Can raise the same exceptions as get().

        """
        txt = self.get()
        txt = pywikibot.removeLanguageLinks(txt, site = self.site())
        txt = pywikibot.removeCategoryLinks(txt, site = self.site())
        if len(txt) < 4:
            return True
        else:
            return False

    def isTalkPage(self):
        """Return True if this page is in any talk namespace."""
        ns = self.namespace()
        return ns >= 0 and ns % 2 == 1

    def toggleTalkPage(self):
        """Return other member of the article-talk page pair for this Page.

        If self is a talk page, returns the associated content page;
        otherwise, returns the associated talk page.  The returned page need
        not actually exist on the wiki.
        
        Returns None if self is a special page.

        """
        ns = self.namespace()
        if ns < 0: # Special page
            return None
        if self.isTalkPage():
            if self.namespace() == 1:
                return Page(self.site(), self.title(withNamespace=False))
            else:
                return Page(self.site(),
                            self.site().namespace(ns - 1) + ':'
                              + self.title(withNamespace=False))
        else:
            return Page(self.site(),
                        self.site().namespace(ns + 1) + ':'
                          + self.title(withNamespace=False))

    def isCategory(self):
        """Return True if the page is a Category, False otherwise."""
        return self.namespace() == 14

    def isImage(self):
        """Return True if this is an image description page, False otherwise."""
        return self.namespace() == 6

    def isDisambig(self):
        """Return True if this is a disambiguation page, False otherwise.

        Relies on the presence of specific templates, identified in
        the Family file or on a wiki page, to identify disambiguation
        pages.

        By default, loads a list of template names from the Family file;
        if the value in the Family file is None, looks for the list on
        [[MediaWiki:Disambiguationspage]].

        """
        if not hasattr(self, "_isDisambig"):
            if not hasattr(self.site(), "_disambigtemplates"):
                self.site()._disambigtemplates = \
                                self.site().family.disambig(self.site().code)
                if self.site()._disambigtemplates is None:
                    try:
                        disambigpages = Page(self.site(),
                                             "MediaWiki:Disambiguationspage")
                        self.site()._disambigtemplates = [
                            link.title(withNamespace=False)
                              for link in disambigpages.linkedPages()
                              if link.namespace() == 10
                        ]
                    except NoPage:
                        self.site()._disambigtemplates = ['Disambig']
            for t in self.templates():
                if t.title(withNamespace=False) in self.site()._disambigtemplates:
                    self._isDisambig = True
                    break
            else:
                self._isDisambig = False
        return self._isDisambig

    def getReferences(self, follow_redirects=True, withTemplateInclusion=True,
                      onlyTemplateInclusion=False, redirectsOnly=False,
                      namespaces=None):
        """Return an iterator all pages that refer to or embed the page.

        If you need a full list of referring pages, use 
        C{pages = list(s.getReferences())}

        @param follow_redirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        @param withTemplateInclusion: if True, also iterate pages where self
            is used as a template.
        @param onlyTemplateInclusion: if True, only iterate pages where self
            is used as a template.
        @param redirectsOnly: if True, only iterate redirects to self.
        @param namespaces: only iterate pages in these namespaces

        """
        # N.B.: this method intentionally overlaps with backlinks() and
        # embeddedin(). Depending on the interface, it may be more efficient
        # to implement those methods in the site interface and then combine
        # the results for this method, or to implement this method and then
        # split up the results for the others. 
        return self.site().pagereferences(
                           self, follow_redirects, redirectsOnly,
                           withTemplateInclusion, onlyTemplateInclusion,
                           namespaces)

    def backlinks(self, followRedirects=True, filterRedirects=None,
                  namespaces=None):
        """Return an iterator for pages that link to this page.

        @param followRedirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        @param filterRedirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        @param namespaces: only iterate pages in these namespaces

        """
        return self.site().pagebacklinks(self, followRedirects, filterRedirects,
                                         namespaces)

    def embeddedin(self, filter_redirects=None, namespaces=None):
        """Return an iterator for pages that embed this page as a template.

        @param filterRedirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        @param namespaces: only iterate pages in these namespaces

        """
        return self.site().page_embeddedin(self, filter_redirects, namespaces)

    def canBeEdited(self):
        """Return bool indicating whether this page can be edited.

        This returns True if and only if:
          - page is unprotected, and bot has an account for this site, or
          - page is protected, and bot has a sysop account for this site.

        """
        return self.site().page_can_be_edited(self)

    def botMayEdit(self):
        """Return True if this page allows bots to edit it.

        This will be True if the page doesn't contain {{bots}} or
        {{nobots}}, or it contains them and the active bot is allowed to
        edit this page. (This method is only useful on those sites that
        recognize the bot-exclusion protocol; on other sites, it will always
        return True.)

        The framework enforces this restriction by default. It is possible
        to override this by setting ignore_bot_templates=True in
        user_config.py, or using page.put(force=True).

        """ # TODO: move this to Site object?
        if config.ignore_bot_templates: #Check the "master ignore switch"
            return True
        try:
            templates = self.templatesWithParams();
        except (pywikibot.NoPage,
                pywikibot.IsRedirectPage,
                pywikibot.SectionError):
            return True
        for template in templates:
            title = template[0].title(withNamespace=False)
            if title == 'Nobots':
                return False
            elif title == 'Bots':
                if len(template[1]) == 0:
                    return True
                else:
                    (ttype, bots) = template[1][0].split('=', 1)
                    bots = bots.split(',')
                    if ttype == 'allow':
                        if 'all' in bots or username in bots:
                            return True
                        else:
                            return False
                    if ttype == 'deny':
                        if 'all' in bots or username in bots:
                            return False
                        else:
                            return True
        # no restricting template found
        return True

    def save(self, comment=None, watch=None, minor=True, force=False,
             async=False, callback=None):
        """Save the current contents of page's text to the wiki.

        @param comment: The edit summary for the modification (optional, but
            most wikis strongly encourage its use)
        @type comment: unicode
        @param watch: if True, add or if False, remove this Page to/from bot
            user's watchlist; if None, leave watchlist status unchanged
        @type watch: bool or None
        @param minor: if True, mark this edit as minor
        @type minor: bool
        @param force: if True, ignore botMayEdit() setting
        @type force: bool
        @param async: if True, launch a separate thread to save
            asynchronously
        @param callback: a callable object that will be called after the
            page put operation. This object must take two arguments: (1) a
            Page object, and (2) an exception instance, which will be None
            if the page was saved successfully. The callback is intended for
            use by bots that need to keep track of which saves were
            successful.

        """
        if not comment:
            comment = config.default_edit_summary
        if watch is None:
            unwatch = False
            watch = False
        else:
            unwatch = not watch
        if not force and not self.botMayEdit:
            raise pywikibot.PageNotSaved(
                "Page %s not saved; editing restricted by {{bots}} template"
                % self.title(asLink=True))
        if async:
            thd = threading.Thread(
                      target=self._save,
                      args=(comment, minor, watch, unwatch, callback)
                  )
            pywikibot.threadpool.append(thd)
            thd.start()
        else:
            self._save(comment, minor, watch, unwatch, callback)

    def _save(self, comment, minor, watch, unwatch, callback):
        err = None
        try:
            done = self.site().editpage(self, summary=comment, minor=minor,
                                        watch=watch, unwatch=unwatch)
            if not done:
                pywikibot.output("Page %s not saved" % self.title(asLink=True),
                                 level=pywikibot.WARNING)
            else:
                pywikibot.output("Page %s saved" % self.title(asLink=True))
        except pywikibot.Error, err:
            logger.exception("Error saving page %s" % self.title(asLink=True))
        if callback:
            callback(self, err)

    def put(self, newtext, comment=u'', watchArticle=None, minorEdit=True,
            force=False, async=False, callback=None):
        """Save the page with the contents of the first argument as the text.

        This method is maintained primarily for backwards-compatibility.
        For new code, using Page.save() is preferred.  See save() method
        docs for all parameters not listed here.

        @param newtext: The complete text of the revised page.
        @type newtext: unicode

        """
        self.text = newtext
        return self.save(comment, watchArticle, minorEdit, force,
                         async, callback)

    def put_async(self, newtext, comment=u'', watchArticle=None,
                  minorEdit=True, force=False, callback=None):
        """Put page on queue to be saved to wiki asynchronously.

        Asynchronous version of put (takes the same arguments), which places
        pages on a queue to be saved by a daemon thread. All arguments are
        the same as for .put().  This version is maintained solely for
        backwards-compatibility.

        """
        return self.put(newtext, comment=comment, watchArticle=watchArticle,
                        minorEdit=minorEdit, force=force, async=True,
                        callback=callback)

    def linkedPages(self):
        """Iterate Pages that this Page links to.

        Only returns pages from "normal" internal links. Image and category
        links are omitted unless prefixed with ":". Embedded templates are
        omitted (but links within them are returned). All interwiki and
        external links are omitted.

        @return: a generator that yields Page objects.

        """
        return self.site().pagelinks(self)

    def interwiki(self, expand=True):
        """Iterate interwiki links in the page text, excluding language links.

        @param expand: if True (default), include interwiki links found in
            templates transcluded onto this page; if False, only iterate
            interwiki links found in this page's own wikitext
        @return: a generator that yields Link objects

        """
        # This function does not exist in the API, so it has to be
        # implemented by screen-scraping
        if expand:
            text = self.expand_text()
        else:
            text = self.text
        for linkmatch in pywikibot.link_regex.finditer(
                            pywikibot.removeDisabledParts(text)):
            linktitle = linkmatch.group("title")
            link = Link(linktitle, self.site())
            # only yield links that are to a different site and that
            # are not language links
            try:
                if link.site != self.site():
                    if linktitle.lstrip().startswith(":"):
                        # initial ":" indicates not a language link
                        yield link
                    elif link.site.family != self.site().family:
                        # link to a different family is not a language link
                        yield link
            except pywikibot.Error:
                # ignore any links with invalid contents
                continue

    def langlinks(self):
        """Iterate all interlanguage links on this page.

        @return: a generator that yields Link objects.

        """
        return self.site().pagelanglinks(self)

    @deprecate_arg("followRedirects", None)
    @deprecate_arg("loose", None)
    def imagelinks(self, followRedirects=None, loose=None):
        """Iterate ImagePage objects for images displayed on this Page.

        @return: a generator that yields ImagePage objects.

        """
        return self.site().pageimages(self)

    def templates(self):
        """Iterate Page objects for templates used on this Page.

        Template parameters are ignored.  This method only returns embedded
        templates, not template pages that happen to be referenced through
        a normal link.

        """
        return self.site().pagetemplates(self)

    def templatesWithParams(self):
        """Iterate templates used on this Page.

        @return: a generator that yields a tuple for each use of a template
        in the page, with the template Page as the first entry and a list of
        parameters as the second entry.

        """
        templates = pywikibot.extract_templates_and_params(self.text)
        # backwards-compatibility: convert the dict returned as the second
        # element into a list in the format used by old scripts
        result = []
        for template in templates:
            args = template[1]
            positional = []
            named = {}
            for key in sorted(args.keys()):
                try:
                    int(key)
                except ValueError:
                    named[key] = args[key]
                else:
                    positional.append(args[key])
            for name in named:
                positional.append("%s=%s" % (name, named[name]))
            result.append((pywikibot.Page(
                             pywikibot.Link(template[0], self.site())),
                           positional))
        return result

    @deprecate_arg("nofollow_redirects", None)
    @deprecate_arg("get_redirect", None)
    def categories(self, withSortKey=False):
        """Iterate categories that the article is in.

        @param withSortKey: if True, include the sort key in each Category.
        @return: a generator that yields Category objects.

        """
        return self.site().pagecategories(self, withSortKey=withSortKey)

    def extlinks(self):
        """Iterate all external URLs (not interwiki links) from this page.

        @return: a generator that yields unicode objects containing URLs.

        """
        return self.site().page_extlinks(self)

    def getRedirectTarget(self):
        """Return a Page object for the target this Page redirects to.

        If this page is not a redirect page, will raise an IsNotRedirectPage
        exception. This method also can raise a NoPage exception.

        """
        if not self.isRedirectPage():
            raise pywikibot.IsNotRedirectPage
        if not isinstance(self._redir, Page):
            self.site().getredirtarget(self)
        return self._redir

    @deprecate_arg("forceReload", None)
    def getVersionHistory(self, reverseOrder=False, getAll=False,
                          revCount=500):
        """Load the version history page and return history information.

        Return value is a list of tuples, where each tuple represents one
        edit and is built of revision id, edit date/time, user name, and
        edit summary. Starts with the most current revision, unless
        reverseOrder is True. Defaults to getting the first revCount edits,
        unless getAll is True.

        """
        if getAll:
            limit = None
        else:
            limit = revCount
        self.site().loadrevisions(self, getText=False, rvdir=reverseOrder,
                                  limit=limit)
        if getAll:
            revCount = len(self._revisions)
        return [ ( self._revisions[rev].revid,
                   self._revisions[rev].timestamp,
                   self._revisions[rev].user,
                   self._revisions[rev].comment
                 ) for rev in sorted(self._revisions.keys(),
                                     reverse=not reverseOrder)[ : revCount]
               ]

    def getVersionHistoryTable(self, forceReload=False, reverseOrder=False,
                               getAll=False, revCount=500):
        """Return the version history as a wiki table."""
        result = '{| border="1"\n'
        result += '! oldid || date/time || username || edit summary\n'
        for oldid, time, username, summary \
                in self.getVersionHistory(forceReload=forceReload,
                                          reverseOrder=reverseOrder,
                                          getAll=getAll, revCount=revCount):
            result += '|----\n'
            result += '| %s || %s || %s || <nowiki>%s</nowiki>\n'\
                      % (oldid, time, username, summary)
        result += '|}\n'
        return result

    def fullVersionHistory(self):
        """Iterate all previous versions including wikitext.

        @return: A generator that yields tuples consisting of revision ID,
            edit date/time, user name and content
        """
        return self.site().loadrevisions(self, withText=True)

    def contributingUsers(self):
        """Return a set of usernames (or IPs) of users who edited this page."""
        edits = self.getVersionHistory()
        users = set([edit[2] for edit in edits])
        return users

    @deprecate_arg("throttle", None)
    def move(self, newtitle, reason=None, movetalkpage=True, sysop=False,
             deleteAndMove=False, safe=True):
        """Move this page to a new title.

        @param newtitle: The new page title.
        @param reason: The edit summary for the move.
        @param movetalkpage: If true, move this page's talk page (if it exists)
        @param sysop: Try to move using sysop account, if available
        @param deleteAndMove: if move succeeds, delete the old page
            (usually requires sysop privileges, depending on wiki settings)
        @param safe: If false, attempt to delete existing page at newtitle
            (if there is one) and then move this page to that title

        """
        if reason is None:
            pywikibot.output(u'Moving %s to [[%s]].'
                             % (self.title(asLink=True), newtitle))
            reason = pywikibot.input(u'Please enter a reason for the move:')
        # TODO: implement "safe" parameter
        # TODO: implement "sysop" parameter
        return self.site().movepage(self, newtitle, reason,
                                    movetalk=movetalkpage,
                                    noredirect=deleteAndMove)

    @deprecate_arg("throttle", None)
    def delete(self, reason=None, prompt=True, throttle=None, mark=False):
        """Deletes the page from the wiki. Requires administrator status.

        @param reason: The edit summary for the deletion.
        @param prompt: If true, prompt user for confirmation before deleting.
        @param mark: if true, and user does not have sysop rights, place a
            speedy-deletion request on the page instead.

        """
        if reason is None:
            pywikibot.output(u'Deleting %s.' % (self.title(asLink=True)))
            reason = pywikibot.input(u'Please enter a reason for the deletion:')
        answer = u'y'
        if prompt and not hasattr(self.site(), '_noDeletePrompt'):
            answer = pywikibot.inputChoice(u'Do you want to delete %s?'
                        % self.title(asLink = True, forceInterwiki = True),
                                           ['Yes', 'No', 'All'],
                                           ['Y', 'N', 'A'],
                                           'N')
            if answer in ['a', 'A']:
                answer = 'y'
                self.site()._noDeletePrompt = True
        if answer in ['y', 'Y']:
            return self.site().delete(self, reason, mark=mark)

    def loadDeletedRevisions(self):
        """Retrieve all deleted revisions for this Page from Special/Undelete.

        Stores all revisions' timestamps, dates, editors and comments in
        self._deletedRevs attribute.

        @return: list of timestamps (which can be used to retrieve revisions
            later on).

        """
        return self.site().loadDeletedRevisions(self)

    def getDeletedRevision(self, timestamp, retrieveText=False):
        """Return a particular deleted revision by timestamp.

        @return: a list of [date, editor, comment, text, restoration
            marker]. text will be None, unless retrieveText is True (or has
            been retrieved earlier). If timestamp is not found, returns
            None.

        """
        return self.site().getDeletedRevision(self, timestamp,
                                              getText=retrieveText)

    def markDeletedRevision(self, timestamp, undelete=True):
        """Mark the revision identified by timestamp for undeletion.

        @param undelete: if False, mark the revision to remain deleted.

        """
        if self._deletedRevs == None:
            self.loadDeletedRevisions()
        if timestamp not in self._deletedRevs:
            #TODO: Throw an exception?
            return None
        self._deletedRevs[timestamp][4] = undelete
        self._deletedRevsModified = True

    @deprecate_arg("throttle", None)
    def undelete(self, comment=None):
        """Undelete revisions based on the markers set by previous calls.

        If no calls have been made since loadDeletedRevisions(), everything
        will be restored.

        Simplest case::
            Page(...).undelete('This will restore all revisions')

        More complex::
            pg = Page(...)
            revs = pg.loadDeletedRevsions()
            for rev in revs:
                if ... #decide whether to undelete a revision
                    pg.markDeletedRevision(rev) #mark for undeletion
            pg.undelete('This will restore only selected revisions.')

        @param comment: The undeletion edit summary.

        """
        if comment is None:
            pywikibot.output(u'Preparing to undelete %s.'
                             % (self.title(asLink=True)))
            comment = pywikibot.input(
                        u'Please enter a reason for the undeletion:')
        return self.site().undelete(self, comment)

    @deprecate_arg("throttle", None)
    def protect(self, edit='sysop', move='sysop', unprotect=False,
                reason=None, prompt=True):
        """(Un)protect a wiki page. Requires administrator status.

        Valid protection levels (in MediaWiki 1.12) are '' (equivalent to
        'none'), 'autoconfirmed', and 'sysop'.

        @param edit: Level of edit protection
        @param move: Level of move protection
        @param unprotect: If true, unprotect the page (equivalent to setting
            all protection levels to '')
        @param reason: Edit summary.
        @param prompt: If true, ask user for confirmation.

        """
        if reason is None:
            if unprotect:
                un = u'un'
            else:
                un = u''
            pywikibot.output(u'Preparing to %sprotect %s.'
                             % (un, self.title(asLink=True)))
            reason = pywikibot.input(u'Please enter a reason for the action:')
        if unprotect:
            edit = move = ""
        answer = 'y'
        if prompt and not hasattr(self.site(), '_noProtectPrompt'):
            answer = pywikibot.inputChoice(
                        u'Do you want to change the protection level of %s?'
                          % self.title(asLink=True, forceInterwiki = True),
                        ['Yes', 'No', 'All'], ['Y', 'N', 'A'], 'N')
            if answer in ['a', 'A']:
                answer = 'y'
                self.site()._noProtectPrompt = True
        if answer in ['y', 'Y']:
            return self.site().protect(self, edit, move, reason)

    def change_category(self, oldCat, newCat, comment=None, sortKey=None,
                        inPlace=True):
        """Remove page from oldCat and add it to newCat.

        oldCat and newCat should be Category objects.
        If newCat is None, the category will be removed.
        
        """ # TODO: document remaining arguments
        site = self.site()
        changesMade = False

        if not self.canBeEdited():
            pywikibot.output(u"Can't edit %s, skipping it..."
                              % self.title(asLink=True))
            return False
        if inPlace == True:
            newtext = pywikibot.replaceCategoryInPlace(self.text,
                                                       oldCat, newCat)
            if newtext == self.text:
                pywikibot.output(
                    u'No changes in made in page %s.'
                     % self.title(asLink=True))
                return False
            try:
                self.put(newtext, comment)
                return True
            except pywikibot.EditConflict:
                pywikibot.output(
                    u'Skipping %s because of edit conflict'
                     % self.title(asLink=True))
            except pywikibot.LockedPage:
                pywikibot.output(u'Skipping locked page %s'
                                  % self.title(asLink=True))
            except pywikibot.SpamfilterError, error:
                pywikibot.output(
                    u'Changing page %s blocked by spam filter (URL=%s)'
                                 % (self.title(asLink=True), error.url))
            except pywikibot.NoUsername:
                pywikibot.output(
                    u"Page %s not saved; sysop privileges required."
                                 % self.title(asLink=True))
            except pywikibot.PageNotSaved, error:
                pywikibot.output(u"Saving page %s failed: %s"
                                 % (self.title(asLink=True), error.message))
            return False

        # This loop will replace all occurrences of the category to be changed,
        # and remove duplicates.
        newCatList = []
        newCatSet = set()
        cats = list(self.categories(get_redirect=True))
        for i in range(len(cats)):
            cat = cats[i]
            if cat == oldCat:
                changesMade = True
                if not sortKey:
                    sortKey = cat.sortKey
                if newCat:
                    if newCat.title() not in newCatSet:
                        newCategory = Category(site, newCat.title(),
                                               sortKey=sortKey)
                        newCatSet.add(newCat.title())
                        newCatList.append(newCategory)
            elif cat.title() not in newCatSet:
                newCatSet.add(cat.title())
                newCatList.append(cat)

        if not changesMade:
            pywikibot.output(u'ERROR: %s is not in category %s!'
                              % (self.title(asLink=True), oldCat.title()))
        else:
            try:
                text = pywikibot.replaceCategoryLinks(self.text, newCatList)
            except ValueError:
                # Make sure that the only way replaceCategoryLinks() can return
                # a ValueError is in the case of interwiki links to self.
                pywikibot.output(
                        u'Skipping %s because of interwiki link to self' % self)
            try:
                self.put(text, comment)
            except pywikibot.EditConflict:
                pywikibot.output(
                        u'Skipping %s because of edit conflict' % self.title())
            except pywikibot.SpamfilterError, e:
                pywikibot.output(
                        u'Skipping %s because of blacklist entry %s'
                        % (self.title(), e.url))
            except pywikibot.LockedPage:
                pywikibot.output(
                        u'Skipping %s because page is locked' % self.title())
            except pywikibot.PageNotSaved, error:
                pywikibot.output(u"Saving page %s failed: %s"
                                 % (self.title(asLink=True), error.message))

######## DEPRECATED METHODS ########

    def encoding(self):
        """DEPRECATED: use Site.encoding() instead"""
        logger.debug(u"Page.encoding() is deprecated; use Site.encoding().")
        return self.site().encoding()

    def titleWithoutNamespace(self, underscore=False):
        """DEPRECATED: use self.title(withNamespace=False) instead."""
        logger.debug(
            u"Page.titleWithoutNamespace() method is deprecated.")
        return self.title(underscore=underscore, withNamespace=False,
                          withSection=False)

    def titleForFilename(self):
        """DEPRECATED: use self.title(as_filename=True) instead."""
        logger.debug(
            u"Page.titleForFilename() method is deprecated.")
        return self.title(as_filename=True)

    def sectionFreeTitle(self, underscore=False):
        """DEPRECATED: use self.title(withSection=False) instead."""
        logger.debug(
            u"Page.sectionFreeTitle() method is deprecated.")
        return self.title(underscore=underscore, withSection=False)

    def aslink(self, forceInterwiki=False, textlink=False, noInterwiki=False):
        """DEPRECATED: use self.title(asLink=True) instead."""
        logger.debug(u"Page.aslink() method is deprecated.")
        return self.title(asLink=True, forceInterwiki=forceInterwiki,
                          allowInterwiki=not noInterwiki, textlink=textlink)

    def urlname(self):
        """Return the Page title encoded for use in an URL.

        DEPRECATED: use self.title(asUrl=True) instead.

        """
        logger.debug(u"Page.urlname() method is deprecated.")
        return self.title(asUrl=True)

####### DISABLED METHODS (warnings provided) ######
    # these methods are easily replaced by editing the page's text using
    # textlib methods and then using put() on the result.

    def removeImage(self, image, put=False, summary=None, safe=True):
        """Old method to remove all instances of an image from page."""
        logger.warning(u"Page.removeImage() is no longer supported.")

    def replaceImage(self, image, replacement=None, put=False, summary=None,
                     safe=True):
        """Old method to replace all instances of an image with another."""
        logger.warning(u"Page.replaceImage() is no longer supported.")


class ImagePage(Page):
    """A subclass of Page representing an image descriptor wiki page.

    Supports the same interface as Page, with the following added methods:

    getImagePageHtml          : Download image page and return raw HTML text.
    fileURL                   : Return the URL for the image described on this
                                page.
    fileIsOnCommons           : Return True if image stored on Wikimedia
                                Commons.
    fileIsShared              : Return True if image stored on Wikitravel
                                shared repository.
    getFileMd5Sum             : Return image file's MD5 checksum.
    getFileVersionHistory     : Return the image file's version history.
    getFileVersionHistoryTable: Return the version history in the form of a
                                wiki table.
    usingPages                : Iterate Pages on which the image is displayed.

    """
    def __init__(self, source, title=u"", insite=None):
        Page.__init__(self, source, title, 6)
        if self.namespace() != 6:
            raise ValueError(u"'%s' is not in the image namespace!" % title)

    def getImagePageHtml(self):
        """
        Download the image page, and return the HTML, as a unicode string.

        Caches the HTML code, so that if you run this method twice on the
        same ImagePage object, the page will only be downloaded once.
        """
        if not hasattr(self, '_imagePageHtml'):
            from pywikibot.data import http
            path = "%s/index.php?title=%s" \
                   % (self.site().scriptpath(), self.title(asUrl=True))
            self._imagePageHtml = http.request(self.site(), path)
        return self._imagePageHtml

    def fileUrl(self):
        """Return the URL for the image described on this page."""
        # TODO add scaling option?
        if not hasattr(self, '_imageinfo'):
            self._imageinfo = self.site().getimageinfo(self) #FIXME
        return self._imageinfo['url']

    def fileIsOnCommons(self):
        """Return True if the image is stored on Wikimedia Commons"""
        return self.fileUrl().startswith(
            'http://upload.wikimedia.org/wikipedia/commons/')

    def fileIsShared(self):
        """Return True if image is stored on any known shared repository."""
        # as of now, the only known repositories are commons and wikitravel
        if 'wikitravel_shared' in self.site().shared_image_repository():
            return self.fileUrl().startswith(
                u'http://wikitravel.org/upload/shared/')
        return self.fileIsOnCommons()

    def getFileMd5Sum(self):
        """Return image file's MD5 checksum."""
        logger.debug(
            "ImagePage.getFileMd5Sum() is deprecated; use getFileSHA1Sum().")
# FIXME: MD5 might be performed on incomplete file due to server disconnection
# (see bug #1795683).
        import md5, urllib
        f = urllib.urlopen(self.fileUrl())
        # TODO: check whether this needs a User-Agent header added
        md5Checksum = md5.new(f.read()).hexdigest()
        f.close()
        return md5Checksum

    def getFileSHA1Sum(self):
        """Return image file's SHA1 checksum."""
        if not hasattr(self, '_imageinfo'):
            self._imageinfo = self.site().getimageinfo(self) #FIXME
        return self._imageinfo['sha1']

    def getFileVersionHistory(self):
        """Return the image file's version history.

        @return: An iterator yielding tuples containing (timestamp,
            username, resolution, filesize, comment).

        """
        #TODO; return value may need to change
        return self.site().getimageinfo(self, history=True) #FIXME

    def getFileVersionHistoryTable(self):
        """Return the version history in the form of a wiki table."""
        lines = []
        #TODO: if getFileVersionHistory changes, make sure this follows it
        for (datetime, username, resolution, size, comment) \
                in self.getFileVersionHistory():
            lines.append('| %s || %s || %s || %s || <nowiki>%s</nowiki>' \
                         % (datetime, username, resolution, size, comment))
        return u'{| border="1"\n! date/time || username || resolution || size || edit summary\n|----\n' + u'\n|----\n'.join(lines) + '\n|}'

    def usingPages(self):
        """Yield Pages on which the image is displayed."""
        return self.site().getimageusage(self)


class Category(Page):
    """A page in the Category: namespace"""

    def __init__(self, source, title=u"", insite=None, sortKey=None):
        """All parameters are the same as for Page() constructor.

        """
        Page.__init__(self, source, title, 14)
        if self.namespace() != 14:
            raise ValueError(u"'%s' is not in the category namespace!"
                             % title)
        self.sortKey = sortKey

    @deprecate_arg("forceInterwiki", None)
    @deprecate_arg("textlink", None)
    @deprecate_arg("noInterwiki", None)
    def aslink(self, sortKey=u''):
        """Return a link to place a page in this Category.

        Use this only to generate a "true" category link, not for interwikis
        or text links to category pages.

        @param sortKey: The sort key for the article to be placed in this
            Category; if omitted, default sort key is used.
        @type sortKey: (optional) unicode

        """
        if sortKey:
            titleWithSortKey = '%s|%s' % (self.title(withSection=False),
                                          self.sortKey)
        else:
            titleWithSortKey = self.title(withSection=False)
        return '[[%s]]' % titleWithSortKey

    @deprecate_arg("startFrom", None)
    @deprecate_arg("cacheResults", None)
    def subcategories(self, recurse=False):
        """Iterate all subcategories of the current category.

        @param recurse: if not False or 0, also iterate subcategories of
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate direct subcats and
            first-level sub-sub-cats, but no deeper.)
        @type recurse: int or bool

        """
        if not isinstance(recurse, bool) and recurse:
            recurse = recurse - 1
        if not hasattr(self, "_subcats"):
            self._subcats = []
            for member in self.site().categorymembers(self, namespaces=[14]):
                subcat = Category(self.site(), member.title())
                self._subcats.append(subcat)
                yield subcat
                if recurse:
                    for item in subcat.subcategories(recurse):
                        yield item
        else:
            for subcat in self._subcats:
                yield subcat
                if recurse:
                    for item in subcat.subcategories(recurse):
                        yield item

    @deprecate_arg("startFrom", None)
    def articles(self, recurse=False):
        """
        Yields all articles in the current category.

        @param recurse: if not False or 0, also iterate articles in
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate articles in first-level
            subcats, but no deeper.)
        @type recurse: int or bool

        """
        namespaces = [x for x in self.site().namespaces().keys()
                      if x>=0 and x!=14]
        for member in self.site().categorymembers(self,
                                                  namespaces=namespaces):
            yield member
        if recurse:
            if not isinstance(recurse, bool) and recurse:
                recurse = recurse - 1
            for subcat in self.subcategories():
                for article in subcat.articles(recurse):
                    yield article

    def isEmptyCategory(self):
        """Return True if category has no members (including subcategories)."""
        for member in self.site().categorymembers(self, limit=1):
            return False
        return True

    def copyTo(self, catname):
        """
        Copy text of category page to a new page.  Does not move contents.

        @param catname: New category title (without namespace)
        @return: True if copying was successful, False if target page
            already existed.

        """
        # This seems far too specialized to be in the top-level framework
        catname = self.site().category_namespace() + ':' + catname
        targetCat = Category(self.site(), catname)
        if targetCat.exists():
            logger.warn('Target page %s already exists!'
                             % targetCat.title())
            return False
        else:
            pywikibot.output('Moving text from %s to %s.'
                             % (self.title(), targetCat.title()))
            authors = ', '.join(self.contributingUsers())
            creationSummary = pywikibot.translate(
                                  self.site(), msg_created_for_renaming
                              ) % (self.title(), authors)
            targetCat.put(self.get(), creationSummary)
            return True

    def copyAndKeep(self, catname, cfdTemplates):
        """Copy partial category page text (not contents) to a new title.

        Like copyTo above, except this removes a list of templates (like
        deletion templates) that appear in the old category text.  It also
        removes all text between the two HTML comments BEGIN CFD TEMPLATE
        and END CFD TEMPLATE. (This is to deal with CFD templates that are
        substituted.)

        Returns true if copying was successful, false if target page already
        existed.

        @param catname: New category title (without namespace)
        @param cfdTemplates: A list (or iterator) of templates to be removed
            from the page text
        @return: True if copying was successful, False if target page
            already existed.

        """
        # I don't see why we need this as part of the framework either
        catname = self.site().category_namespace() + ':' + catname
        targetCat = Category(self.site(), catname)
        if targetCat.exists():
            logger.warn('Target page %s already exists!'
                             % targetCat.title())
            return False
        else:
            pywikibot.output('Moving text from %s to %s.'
                             % (self.title(), targetCat.title()))
            authors = ', '.join(self.contributingUsers())
            creationSummary = pywikibot.translate(
                                  self.site(), msg_created_for_renaming
                              ) % (self.title(), authors)
            newtext = self.get()
        for regexName in cfdTemplates:
            matchcfd = re.compile(r"{{%s.*?}}" % regexName, re.IGNORECASE)
            newtext = matchcfd.sub('',newtext)
            matchcomment = re.compile(
                        r"<!--BEGIN CFD TEMPLATE-->.*?<!--END CFD TEMPLATE-->",
                                      re.IGNORECASE | re.MULTILINE | re.DOTALL)
            newtext = matchcomment.sub('', newtext)
            pos = 0
            while (newtext[pos:pos+1] == "\n"):
                pos = pos + 1
            newtext = newtext[pos:]
            targetCat.put(newtext, creationSummary)
            return True

#### DEPRECATED METHODS ####
    def subcategoriesList(self, recurse=False):
        """DEPRECATED: Equivalent to list(self.subcategories(...))"""
        logger.debug("Category.subcategoriesList() method is deprecated.")
        return sorted(list(set(self.subcategories(recurse))))

    def articlesList(self, recurse=False):
        """DEPRECATED: equivalent to list(self.articles(...))"""
        logger.debug("Category.articlesList() method is deprecated.")
        return sorted(list(set(self.articles(recurse))))

    def supercategories(self):
        """DEPRECATED: equivalent to self.categories()"""
        logger.debug("Category.supercategories() method is deprecated.")
        return self.categories()

    def supercategoriesList(self):
        """DEPRECATED: equivalent to list(self.categories(...))"""
        logger.debug("Category.articlesList() method is deprecated.")
        return sorted(list(set(self.categories())))


class Revision(object):
    """A structure holding information about a single revision of a Page."""
    def __init__(self, revid, timestamp, user, anon=False, comment=u"",
                 text=None, minor=False):
        """All parameters correspond to object attributes (e.g., revid
        parameter is stored as self.revid)

        @param revid: Revision id number
        @type revid: int
        @param text: Revision wikitext.
        @type text: unicode, or None if text not yet retrieved
        @param timestamp: Revision time stamp (in ISO 8601 format)
        @type timestamp: unicode
        @param user: user who edited this revision
        @type user: unicode
        @param anon: user is unregistered
        @type anon: bool
        @param comment: edit comment text
        @type comment: unicode
        @param minor: edit flagged as minor
        @type minor: bool

        """
        self.revid = revid
        self.text = text
        self.timestamp = timestamp
        self.user = user
        self.anon = anon
        self.comment = comment
        self.minor = minor


class Link(object):
    """A Mediawiki link (local or interwiki)

    Has the following attributes:

      - site:  The Site object for the wiki linked to
      - namespace: The namespace of the page linked to (int)
      - title: The title of the page linked to (unicode); does not include
        namespace or section
      - section: The section of the page linked to (unicode or None); this
        contains any text following a '#' character in the title
      - anchor: The anchor text (unicode or None); this contains any text
        following a '|' character inside the link

    """
    illegal_titles_pattern = re.compile(
        # Matching titles will be held as illegal.
            u'''[^ %!\"$&'()*,\\-.\\/0-9:;=?@A-Z\\\\^_`a-z~\u0080-\uFFFF+]'''
            # URL percent encoding sequences interfere with the ability
            # to round-trip titles -- you can't link to them consistently.
            u'|%[0-9A-Fa-f]{2}' 
            # XML/HTML character references produce similar issues.
            u'|&[A-Za-z0-9\x80-\xff]+;'
            u'|&#[0-9]+;'
            u'|&#x[0-9A-Fa-f]+;'
        )

    def __init__(self, text, source=None, defaultNamespace=0):
        """Constructor

        @param text: the link text (everything appearing between [[ and ]]
            on a wiki page)
        @type text: unicode
        @param source: the Site on which the link was found (not necessarily
            the site to which the link refers)
        @type source: Site
        @param defaultNamespace: a namespace to use if the link does not
            contain one (defaults to 0)
        @type defaultNamespace: int

        """
        self._text = text
        self._source = source or pywikibot.Site()
        self._defaultns = defaultNamespace

        # preprocess text (these changes aren't site-dependent)
        # First remove anchor, which is stored unchanged, if there is one
        if u"|" in self._text:
            self._text, self._anchor = self._text.split(u"|", 1)
        else:
            self._anchor = None

        # Clean up the name, it can come from anywhere.
        # Convert HTML entities to unicode
        t = html2unicode(self._text)

        # Convert URL-encoded characters to unicode
        t = url2unicode(t, site=self._source)

        # Normalize unicode string to a NFC (composed) format to allow proper
        # string comparisons. According to
        # http://svn.wikimedia.org/viewvc/mediawiki/branches/REL1_6/phase3/includes/normal/UtfNormal.php?view=markup
        # the mediawiki code normalizes everything to NFC, not NFKC (which
        # might result in information loss).
        t = unicodedata.normalize('NFC', t)

        # This code was adapted from Title.php : secureAndSplit()
        #
        if u'\ufffd' in t:
            raise pywikibot.Error("Title contains illegal char (\\uFFFD)")

        # Replace underscores by spaces
        t = t.replace(u"_", u" ")
        # replace multiple spaces and underscores with a single space
        while u"  " in t: t = t.replace(u"  ", u" ")
        # Strip spaces at both ends
        t = t.strip(" ")
        # Remove left-to-right and right-to-left markers.
        t = t.replace(u"\u200e", u"").replace(u"\u200f", u"")
        self._text = t

    def parse_site(self):
        """Parse only enough text to determine the host site."""

        t = self._text
        self._site = self._source
        firstPass = True
        while u":" in t:
            # Initial colon
            if t.startswith(u":"):
                # remove the colon but continue processing
                # remove any subsequent whitespace
                t = t.lstrip(u":").lstrip(u" ")
                continue
            fam = self._site.family
            prefix = t[ :t.index(u":")].lower() # part of text before :
            ns = self._site.ns_index(prefix)
            if ns:
                # Ordinary namespace
                return
            if prefix in fam.langs.keys()\
                   or prefix in fam.get_known_families(site=self._site):
                # looks like an interwiki link
                if not firstPass:
                    return
                t = t[t.index(u":"): ].lstrip(u": ") # part of text after :
                if prefix in fam.langs.keys():
                    newsite = pywikibot.Site(prefix, fam)
                else:
                    otherlang = self._site.code
                    familyName = fam.get_known_families(site=self._site)[prefix]
                    if familyName in ['commons', 'meta']:
                        otherlang = familyName
                    try:
                        newsite = pywikibot.Site(otherlang, familyName)
                    except ValueError:
                        return
                # Redundant interwiki prefix to the local wiki
                if newsite == self._site:
                    firstPass = False
                    continue
                self._site = newsite
            else:
                return   # text before : doesn't match any known prefix

    def parse(self):
        """Parse text; called internally when accessing attributes"""
        
        self._site = self._source
        self._namespace = self._defaultns
        t = self._text

        # This code was adapted from Title.php : secureAndSplit()
        #
        firstPass = True
        while u":" in t:
            # Initial colon indicates main namespace rather than default
            if t.startswith(u":"):
                self._namespace = 0
                # remove the colon but continue processing
                # remove any subsequent whitespace
                t = t.lstrip(u":").lstrip(u" ")
                continue

            fam = self._site.family
            prefix = t[ :t.index(u":")].lower()
            ns = self._site.ns_index(prefix)
            if ns:
                # Ordinary namespace
                t = t[t.index(u":"): ].lstrip(u":").lstrip(u" ")
                self._namespace = ns
                break
            if prefix in fam.langs.keys()\
                   or prefix in fam.get_known_families(site=self._site):
                # looks like an interwiki link
                if not firstPass:
                    # Can't make a local interwiki link to an interwiki link.
                    raise pywikibot.Error(
                          "Improperly formatted interwiki link '%s'"
                          % self._text)
                t = t[t.index(u":"): ].lstrip(u":").lstrip(u" ")
                if prefix in fam.langs.keys():
                    newsite = pywikibot.Site(prefix, fam)
                else:
                    otherlang = self._site.code
                    familyName = fam.get_known_families(site=self._site)[prefix]
                    if familyName in ['commons', 'meta']:
                        otherlang = familyName
                    try:
                        newsite = pywikibot.Site(otherlang, familyName)
                    except ValueError:
                        raise pywikibot.Error("""\
%s is not a local page on %s, and the %s family is
not supported by PyWikiBot!"""
                              % (title, self._site(), familyName))

                # Redundant interwiki prefix to the local wiki
                if newsite == self._site:
                    if not t:
                        # Can't have an empty self-link
                        raise pywikibot.Error(
                              "Invalid link title: '%s'" % self._text)
                    firstPass = False
                    continue
                self._site = newsite
            else:
                break   # text before : doesn't match any known prefix

        if u"#" in t:
            t, sec = t.split(u'#', 1)
            t, self._section = t.rstrip(), sec.lstrip()
        else:
            self._section = None

        # Reject illegal characters.
        m = Link.illegal_titles_pattern.search(t)
        if m:
            raise pywikibot.Error(
                  u"Invalid title: contains illegal char(s) '%s'" % m.group(0))

        # Pages with "/./" or "/../" appearing in the URLs will
        # often be unreachable due to the way web browsers deal
        #* with 'relative' URLs. Forbid them explicitly.

        if u'.' in t and (
                t == u'.' or t == u'..'
                or t.startswith(u"./")
                or t.startswith(u"../")
                or u"/./" in t
                or u"/../" in t
                or t.endswith(u"/.")
                or t.endswith(u"/..")
        ):
            raise pywikibot.Error(
                  "Invalid title (contains . / combinations): '%s'"
                        % self._text)

        # Magic tilde sequences? Nu-uh!
        if u"~~~" in t:
            raise pywikibot.Error("Invalid title (contains ~~~): '%s'" % self._text)

        if self._namespace != -1 and len(t) > 255:
            raise pywikibot.Error("Invalid title (over 255 bytes): '%s'" % t)

        if self._site.case() == 'first-letter':
            t = t[:1].upper() + t[1:]

        # Can't make a link to a namespace alone...
        # "empty" local links can only be self-links
        # with a fragment identifier.
        if not t and self._site == self._source and self._namespace != 0:
            raise ValueError("Invalid link (no page title): '%s'" % self._text)

        self._title = t

    # define attributes, to be evaluated lazily

    @property
    def site(self):
        if not hasattr(self, "_site"):
            self.parse_site()
        return self._site

    @property
    def namespace(self):
        if not hasattr(self, "_namespace"):
            self.parse()
        return self._namespace

    @property
    def title(self):
        if not hasattr(self, "_title"):
            self.parse()
        return self._title

    @property
    def section(self):
        if not hasattr(self, "_section"):
            self.parse()
        return self._section

    @property
    def anchor(self):
        if not hasattr(self, "_anchor"):
            self.parse()
        return self._anchor

    def canonical_title(self):
        """Return full page title, including localized namespace."""
        if self.namespace:
            return "%s:%s" % (self.site.namespace(self.namespace),
                              self.title)
        else:
            return self.title

    def astext(self, onsite=None):
        """Return a text representation of the link.

        @param onsite: if specified, present as a (possibly interwiki) link
            from the given site; otherwise, present as an internal link on
            the source site.

        """
        if onsite is None:
            onsite = self.site
        title = self.title
        if self.namespace:
            title = onsite.namespace(self.namespace) + ":" + title
        if self.section:
            title = title + "#" + self.section
        if onsite == self.site:
            return u'[[%s]]' % title
        if onsite.family == self.site.family:
            return u'[[%s:%s]]' % (self.site.code, title)
        if self.site.family.name == self.site.code:
            # use this form for sites like commons, where the
            # code is the same as the family name
            return u'[[%s:%s]]' % (self.site.code,
                                   title)
        return u'[[%s:%s:%s]]' % (self.site.family.name,
                                  self.site.code,
                                  title)

    def __str__(self):
        return self.astext().encode("ascii", "backslashreplace")

    def __cmp__(self, other):
        """Test for equality and inequality of Link objects.

        Link objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Link objects are sortable by site, then namespace, then title.

        """
        if not isinstance(other, Link):
            # especially, return -1 if other is None
            return -1
        if not self.site == other.site:
            return cmp(self.site, other.site)
        if self.namespace != other.namespace:
            return cmp(self.namespace, other.namespace)
        return cmp(self.title, other.title)


# Utility functions for parsing page titles

def html2unicode(text, ignore = []):
    """Return text, replacing HTML entities by equivalent unicode characters."""
    # This regular expression will match any decimal and hexadecimal entity and
    # also entities that might be named entities.
    entityR = re.compile(
        r'&(#(?P<decimal>\d+)|#x(?P<hex>[0-9a-fA-F]+)|(?P<name>[A-Za-z]+));')
    # These characters are Html-illegal, but sadly you *can* find some of
    # these and converting them to unichr(decimal) is unsuitable
    convertIllegalHtmlEntities = {
        128 : 8364, # €
        130 : 8218, # ‚
        131 : 402,  # ƒ
        132 : 8222, # „
        133 : 8230, # …
        134 : 8224, # †
        135 : 8225, # ‡
        136 : 710,  # ˆ
        137 : 8240, # ‰
        138 : 352,  # Š
        139 : 8249, # ‹
        140 : 338,  # Œ
        142 : 381,  # Ž
        145 : 8216, # ‘
        146 : 8217, # ’
        147 : 8220, # “
        148 : 8221, # ”
        149 : 8226, # •
        150 : 8211, # –
        151 : 8212, # —
        152 : 732,  # ˜
        153 : 8482, # ™
        154 : 353,  # š
        155 : 8250, # ›
        156 : 339,  # œ
        158 : 382,  # ž
        159 : 376   # Ÿ
    }
    #ensuring that illegal &#129; &#141; and &#157, which have no known values,
    #don't get converted to unichr(129), unichr(141) or unichr(157)
    ignore = set(ignore) | set([129, 141, 157])
    result = u''
    i = 0
    found = True
    while found:
        text = text[i:]
        match = entityR.search(text)
        if match:
            unicodeCodepoint = None
            if match.group('decimal'):
                unicodeCodepoint = int(match.group('decimal'))
            elif match.group('hex'):
                unicodeCodepoint = int(match.group('hex'), 16)
            elif match.group('name'):
                name = match.group('name')
                if name in htmlentitydefs.name2codepoint:
                    # We found a known HTML entity.
                    unicodeCodepoint = htmlentitydefs.name2codepoint[name]
            result += text[:match.start()]
            try:
                unicodeCodepoint=convertIllegalHtmlEntities[unicodeCodepoint]
            except KeyError:
                pass
            if unicodeCodepoint and unicodeCodepoint not in ignore:
                result += unichr(unicodeCodepoint)
            else:
                # Leave the entity unchanged
                result += text[match.start():match.end()]
            i = match.end()
        else:
            result += text
            found = False
    return result

def url2unicode(title, site, site2 = None):
    """Convert url-encoded text to unicode using site's encoding.

    If site2 is provided, try its encodings as well.  Uses the first encoding
    that doesn't cause an error.

    """
    # create a list of all possible encodings for both hint sites
    encList = [site.encoding()] + list(site.encodings())
    if site2 and site2 <> site:
        encList.append(site2.encoding())
        encList += list(site2.encodings())
    firstException = None
    # try to handle all encodings (will probably retry utf-8)
    for enc in encList:
        try:
            t = title.encode(enc)
            t = urllib.unquote(t)
            return unicode(t, enc)
        except UnicodeError, ex:
            if not firstException:
                firstException = ex
            pass
    # Couldn't convert, raise the original exception
    raise firstException

