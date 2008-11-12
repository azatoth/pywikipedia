# -*- coding: utf-8  -*-
"""
Functions for manipulating wiki-text.

Unless otherwise noted, all functions take a unicode string as the argument
and return a unicode string.

"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import pywikibot
import re


def unescape(s):
    """Replace escaped HTML-special characters by their originals"""
    if '&' not in s:
        return s
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&") # Must be last
    return s


def replaceExcept(text, old, new, exceptions, caseInsensitive=False,
                  allowoverlap=False, marker = '', site = None):
    """
    Return text with 'old' replaced by 'new', ignoring specified types of text.

    Skips occurences of 'old' within exceptions; e.g., within nowiki tags or
    HTML comments. If caseInsensitive is true, then use case insensitive
    regex matching. If allowoverlap is true, overlapping occurences are all
    replaced (watch out when using this, it might lead to infinite loops!).

    Parameters:
        text            - a unicode string
        old             - a compiled regular expression
        new             - a unicode string (which can contain regular
                          expression references), or a function which takes
                          a match object as parameter. See parameter repl of
                          re.sub().
        exceptions      - a list of strings which signal what to leave out,
                          e.g. ['math', 'table', 'template']
        caseInsensitive - a boolean
        marker          - a string that will be added to the last replacement;
                          if nothing is changed, it is added at the end

    """
    if site is None:
        site = pywikibot.getSite()

    exceptionRegexes = {
        'comment':     re.compile(r'(?s)<!--.*?-->'),
        # section headers
        'header':      re.compile(r'\r\n=+.+=+ *\r\n'),
        'includeonly': re.compile(r'(?is)<includeonly>.*?</includeonly>'),
        'math':        re.compile(r'(?is)<math>.*?</math>'),
        'noinclude':   re.compile(r'(?is)<noinclude>.*?</noinclude>'),
        # wiki tags are ignored inside nowiki tags.
        'nowiki':      re.compile(r'(?is)<nowiki>.*?</nowiki>'),
        # preformatted text
        'pre':         re.compile(r'(?ism)<pre>.*?</pre>'),
        'source':      re.compile(r'(?is)<source .*?</source>'),
        # inline references
        'ref':         re.compile(r'(?ism)<ref[ >].*?</ref>'),
        'timeline':    re.compile(r'(?is)<timeline>.*?</timeline>'),
        # lines that start with a space are shown in a monospace font and
        # have whitespace preserved.
        'startspace':  re.compile(r'(?m)^ (.*?)$'),
        # tables often have whitespace that is used to improve wiki
        # source code readability.
        # TODO: handle nested tables.
        'table':       re.compile(r'(?ims)^{\|.*?^\|}|<table>.*?</table>'),
        # templates with parameters often have whitespace that is used to
        # improve wiki source code readability.
        # 'template':    re.compile(r'(?s){{.*?}}'),
        # The regex above fails on nested templates. This regex can handle
        # templates cascaded up to level 3, but no deeper. For arbitrary
        # depth, we'd need recursion which can't be done in Python's re.
        # After all, the language of correct parenthesis words is not regular.
        'template':    re.compile(r'(?s){{(({{(({{.*?}})|.)*}})|.)*}}'),
        'hyperlink':   compileLinkR(),
        'gallery':     re.compile(r'(?is)<gallery.*?>.*?</gallery>'),
        # this matches internal wikilinks, but also interwiki, categories, and
        # images.
        'link':        re.compile(r'\[\[[^\]\|]*(\|[^\]]*)?\]\]'),
        'interwiki':   re.compile(r'(?i)\[\[(%s)\s?:[^\]]*\]\][\s]*'
                               % '|'.join(site.validLanguageLinks() + site.family.obsolete.keys())),

    }

    # if we got a string, compile it as a regular expression
    if type(old) is str or type(old) is unicode:
        if caseInsensitive:
            old = re.compile(old, re.IGNORECASE | re.UNICODE)
        else:
            old = re.compile(old)

    dontTouchRegexes = []
    for exc in exceptions:
        if isinstance(exc, str) or isinstance(exc, unicode):
            # assume it's a reference to the exceptionRegexes dictionary
            # defined above.
            if not exceptionRegexes.has_key(exc):
                raise ValueError("Unknown tag type: " + exc)
            dontTouchRegexes.append(exceptionRegexes[exc])
        else:
            # assume it's a regular expression
            dontTouchRegexes.append(exc)
    index = 0
    markerpos = len(text)
    while True:
        match = old.search(text, index)
        if not match:
            # nothing left to replace
            break

        # check which exception will occur next.
        nextExceptionMatch = None
        for dontTouchR in dontTouchRegexes:
            excMatch = dontTouchR.search(text, index)
            if excMatch and (
                    nextExceptionMatch is None or
                    excMatch.start() < nextExceptionMatch.start()):
                nextExceptionMatch = excMatch

        if nextExceptionMatch is not None and nextExceptionMatch.start() <= match.start():
            # an HTML comment or text in nowiki tags stands before the next valid match. Skip.
            index = nextExceptionMatch.end()
        else:
            # We found a valid match. Replace it.
            if callable(new):
                # the parameter new can be a function which takes the match as a parameter.
                replacement = new(match)
            else:
                # it is not a function, but a string.

                # it is a little hack to make \n work. It would be better to fix it
                # previously, but better than nothing.
                new = new.replace('\\n', '\n')

                # We cannot just insert the new string, as it may contain regex
                # group references such as \2 or \g<name>.
                # On the other hand, this approach does not work because it can't
                # handle lookahead or lookbehind (see bug #1731008):
                #replacement = old.sub(new, text[match.start():match.end()])
                #text = text[:match.start()] + replacement + text[match.end():]

                # So we have to process the group references manually.
                replacement = new

                groupR = re.compile(r'\\(?P<number>\d+)|\\g<(?P<name>.+?)>')
                while True:
                    groupMatch = groupR.search(replacement)
                    if not groupMatch:
                        break
                    groupID = groupMatch.group('name') or int(groupMatch.group('number'))
                    replacement = replacement[:groupMatch.start()] + match.group(groupID) + replacement[groupMatch.end():]
            text = text[:match.start()] + replacement + text[match.end():]

            # continue the search on the remaining text
            if allowoverlap:
                index = match.start() + 1
            else:
                index = match.start() + len(replacement)
            markerpos = match.start() + len(replacement)
    text = text[:markerpos] + marker + text[markerpos:]
    return text


def removeDisabledParts(text, tags = ['*']):
    """
    Return text without portions where wiki markup is disabled

    Parts that can/will be removed are --
    * HTML comments
    * nowiki tags
    * pre tags
    * includeonly tags

    The exact set of parts which should be removed can be passed as the
    'parts' parameter, which defaults to all.
    """
    regexes = {
            'comments' :   r'<!--.*?-->',
            'includeonly': r'<includeonly>.*?</includeonly>',
            'nowiki':      r'<nowiki>.*?</nowiki>',
            'pre':         r'<pre>.*?</pre>',
            'source':      r'<source .*?</source>',
    }
    if '*' in tags:
        tags = regexes.keys()
    toRemoveR = re.compile('|'.join([regexes[tag] for tag in tags]),
                           re.IGNORECASE | re.DOTALL)
    return toRemoveR.sub('', text)


def isDisabled(text, index, tags = ['*']):
    """
    Return True if text[index] is disabled, e.g. by a comment or by nowiki tags.

    For the tags parameter, see removeDisabledParts() above.
    """
    # Find a marker that is not already in the text.
    marker = '@@'
    while marker in text:
        marker += '@'
    text = text[:index] + marker + text[index:]
    text = removeDisabledParts(text, tags)
    return (marker not in text)


# Functions dealing with interwiki language links

# Note - MediaWiki supports two kinds of interwiki links; interlanguage and
#        interproject.  These functions only deal with links to a
#        corresponding page in another language on the same project (e.g.,
#        Wikipedia, Wiktionary, etc.) in another language. They do not find
#        or change links to a different project, or any that are formatted
#        as in-line interwiki links (e.g., "[[:es:Articulo]]".  (CONFIRM)

def getLanguageLinks(text, insite = None, pageLink = "[[]]"):
    """
    Return a dict of interlanguage links found in text.

    Dict uses language codes as keys and Page objects as values.
    Do not call this routine directly, use Page.interwiki() method
    instead.

    """
    if insite == None:
        insite = pywikibot.getSite()
    result = {}
    # Ignore interwiki links within nowiki tags, includeonly tags, pre tags,
    # and HTML comments
    text = removeDisabledParts(text)

    # This regular expression will find every link that is possibly an
    # interwiki link.
    # NOTE: language codes are case-insensitive and only consist of basic latin
    # letters and hyphens.
    interwikiR = re.compile(r'\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]')
    for lang, pagetitle in interwikiR.findall(text):
        lang = lang.lower()
        # Check if it really is in fact an interwiki link to a known
        # language, or if it's e.g. a category tag or an internal link
        if lang in insite.family.obsolete:
            lang = insite.family.obsolete[lang]
        if lang in insite.validLanguageLinks():
            if '|' in pagetitle:
                # ignore text after the pipe
                pagetitle = pagetitle[:pagetitle.index('|')]
            # we want the actual page objects rather than the titles
            site = insite.getSite(code = lang)
            try:
                result[site] = pywikibot.Page(site, pagetitle, insite = insite)
            except InvalidTitle:
                output(
        u"[getLanguageLinks] Text contains invalid interwiki link [[%s:%s]]."
                           % (lang, pagetitle))
                continue
    return result


def removeLanguageLinks(text, site = None, marker = ''):
    """Return text with all interlanguage links removed.

    If a link to an unknown language is encountered, a warning is printed.
    If a marker is defined, that string is placed at the location of the
    last occurence of an interwiki link (at the end if there are no
    interwiki links).

    """
    if site == None:
        site = pywikibot.getSite()
    if not site.validLanguageLinks():
        return text
    # This regular expression will find every interwiki link, plus trailing
    # whitespace.
    languages = '|'.join(site.validLanguageLinks() + site.family.obsolete.keys())
    interwikiR = re.compile(r'\[\[(%s)\s?:[^\]]*\]\][\s]*'
                            % languages, re.IGNORECASE)
    text = replaceExcept(text, interwikiR, '',
                         ['nowiki', 'comment', 'math', 'pre', 'source'], marker=marker)
    return text.strip()


def replaceLanguageLinks(oldtext, new, site = None):
    """Replace interlanguage links in the text with a new set of links.

    'new' should be a dict with the Site objects as keys, and Page objects
    as values (i.e., just like the dict returned by getLanguageLinks
    function).
    
    """
    # Find a marker that is not already in the text.
    marker = '@@'
    while marker in oldtext:
        marker += '@'
    if site == None:
        site = pywikibot.getSite()
    s = interwikiFormat(new, insite = site)
    s2 = removeLanguageLinks(oldtext, site = site, marker = marker)
    if s:
        if site.language() in site.family.interwiki_attop:
            newtext = s + site.family.interwiki_text_separator + s2.replace(marker,'').strip()
        else:
            # calculate what was after the language links on the page
            firstafter = s2.find(marker) + len(marker)
            # Is there any text in the 'after' part that means we should keep it after?
            if "</noinclude>" in s2[firstafter:]:
                newtext = s2[:firstafter] + s + s2[firstafter:]
            elif site.language() in site.family.categories_last:
                cats = getCategoryLinks(s2, site = site)
                s2 = removeCategoryLinks(s2.replace(marker,'').strip(), site) + site.family.interwiki_text_separator + s
                newtext = replaceCategoryLinks(s2, cats, site=site)
            else:
                newtext = s2.replace(marker,'').strip() + site.family.interwiki_text_separator + s
            newtext = newtext.replace(marker,'')
    else:
        newtext = s2.replace(marker,'')
    return newtext


def interwikiFormat(links, insite = None):
    """Convert interwiki link dict into a wikitext string.

    'links' should be a dict with the Site objects as keys, and Page
    objects as values.

    Return a unicode string that is formatted for inclusion in insite
    (defaulting to the current site).
    """
    if insite is None:
        insite = pywikibot.getSite()
    if not links:
        return ''

    ar = interwikiSort(links.keys(), insite)
    s = []
    for site in ar:
        try:
            link = links[site].aslink(forceInterwiki=True)
            s.append(link)
        except AttributeError:
            s.append(pywikibot.getSite(site).linkto(links[site],
                                                    othersite=insite))
    if insite.lang in insite.family.interwiki_on_one_line:
        sep = u' '
    else:
        sep = u'\r\n'
    s=sep.join(s) + u'\r\n'
    return s


# Sort sites according to local interwiki sort logic
def interwikiSort(sites, insite = None):
    if insite is None:
      insite = pywikibot.getSite()
    if not sites:
      return []

    sites.sort()
    putfirst = insite.interwiki_putfirst()
    if putfirst:
        #In this case I might have to change the order
        firstsites = []
        for code in putfirst:
            # The code may not exist in this family?
            if code in insite.family.obsolete:
                code = insite.family.obsolete[code]
            if code in insite.validLanguageLinks():
                site = insite.getSite(code = code)
                if site in sites:
                    del sites[sites.index(site)]
                    firstsites = firstsites + [site]
        sites = firstsites + sites
    if insite.interwiki_putfirst_doubled(sites): #some implementations return False
        sites = insite.interwiki_putfirst_doubled(sites) + sites
    return sites


# Functions dealing with category links

def getCategoryLinks(text, site):
    """Return a list of category links found in text.

    List contains Category objects.
    Do not call this routine directly, use Page.categories() instead.

    """
    result = []
    # Ignore category links within nowiki tags, pre tags, includeonly tags,
    # and HTML comments
    text = removeDisabledParts(text)
    catNamespace = '|'.join(site.category_namespaces())
    R = re.compile(r'\[\[\s*(?P<namespace>%s)\s*:\s*(?P<catName>.+?)'
                   r'(?:\|(?P<sortKey>.+?))?\s*\]\]'
                   % catNamespace, re.I)
    for match in R.finditer(text):
        cat = pywikibot.Category(site,
                                 '%s:%s' % (match.group('namespace'),
                                            match.group('catName')),
                                 sortKey = match.group('sortKey'))
        result.append(cat)
    return result


def removeCategoryLinks(text, site, marker = ''):
    """Return text with all category links removed.

    Put the string marker after the last replacement (at the end of the text
    if  there is no replacement).

    """
    # This regular expression will find every link that is possibly an
    # interwiki link, plus trailing whitespace. The language code is grouped.
    # NOTE: This assumes that language codes only consist of non-capital
    # ASCII letters and hyphens.
    catNamespace = '|'.join(site.category_namespaces())
    categoryR = re.compile(r'\[\[\s*(%s)\s*:.*?\]\]\s*' % catNamespace, re.I)
    text = replaceExcept(text, categoryR, '', ['nowiki', 'comment', 'math', 'pre', 'source'], marker = marker)
    if marker:
        #avoid having multiple linefeeds at the end of the text
        text = re.sub('\s*%s' % re.escape(marker), '\r\n' + marker, text.strip())
    return text.strip()


def replaceCategoryInPlace(oldtext, oldcat, newcat, site=None):
    """Replace the category oldcat with the category newcat and return
       the modified text.

    """
    if site is None:
        site = pywikibot.getSite()

    catNamespace = '|'.join(site.category_namespaces())
    title = oldcat.titleWithoutNamespace()
    if not title:
        return
    # title might contain regex special characters
    title = re.escape(title)
    # title might not be capitalized correctly on the wiki
    if title[0].isalpha() and not site.nocapitalize:
        title = "[%s%s]" % (title[0].upper(), title[0].lower()) + title[1:]
    # spaces and underscores in page titles are interchangeable, and collapsible
    title = title.replace(r"\ ", "[ _]+").replace(r"\_", "[ _]+")
    categoryR = re.compile(r'\[\[\s*(%s)\s*:\s*%s\s*((?:\|[^]]+)?\]\])'
                            % (catNamespace, title), re.I)
    if newcat is None:
        text = replaceExcept(oldtext, categoryR, '',
                             ['nowiki', 'comment', 'math', 'pre', 'source'])
    else:
        text = replaceExcept(oldtext, categoryR,
                             '[[%s:%s\\2' % (site.namespace(14),
                                             newcat.titleWithoutNamespace()),
                             ['nowiki', 'comment', 'math', 'pre', 'source'])
    return text


def replaceCategoryLinks(oldtext, new, site = None, addOnly = False):
    """Replace the category links given in the wikitext given
       in oldtext by the new links given in new.

       'new' should be a list of Category objects.

       If addOnly is True, the old category won't be deleted and
       the category(s) given will be added
       (and so they won't replace anything).
    """

    # Find a marker that is not already in the text.
    marker = '@@'
    while marker in oldtext:
        marker += '@'

    if site is None:
        site = pywikibot.getSite()
    if site.sitename() == 'wikipedia:de' and "{{Personendaten" in oldtext:
        raise Error('The PyWikipediaBot is no longer allowed to touch categories on the German Wikipedia on pages that contain the person data template because of the non-standard placement of that template. See http://de.wikipedia.org/wiki/Hilfe_Diskussion:Personendaten/Archiv/bis_2006#Position_der_Personendaten_am_.22Artikelende.22')

    s = categoryFormat(new, insite = site)
    if addOnly:
        s2 = oldtext
    else:
        s2 = removeCategoryLinks(oldtext, site = site, marker = marker)

    if s:
        if site.language() in site.family.category_attop:
            newtext = s + site.family.category_text_separator + s2
        else:
            # calculate what was after the categories links on the page
            firstafter = s2.find(marker)
            # Is there any text in the 'after' part that means we should keep it after?
            if "</noinclude>" in s2[firstafter:]:
                newtext = s2[:firstafter] + s + s2[firstafter:]
            elif site.language() in site.family.categories_last:
                newtext = s2.replace(marker,'').strip() + site.family.category_text_separator + s
            else:
                interwiki = getLanguageLinks(s2)
                s2 = removeLanguageLinks(s2.replace(marker,''), site) + site.family.category_text_separator + s
                newtext = replaceLanguageLinks(s2, interwiki, site)
        newtext = newtext.replace(marker,'')
    else:
        s2 = s2.replace(marker,'')
        return s2
    return newtext.strip()


def categoryFormat(categories, insite = None):
    """Return a string containing links to all categories in a list.

    'categories' should be a list of Category objects.

    The string is formatted for inclusion in insite.
    
    """
    if not categories:
        return ''
    if insite is None:
        insite = pywikibot.getSite()
    catLinks = [category.aslink(noInterwiki = True) for category in categories]
    if insite.category_on_one_line():
        sep = ' '
    else:
        sep = '\r\n'
    # Some people don't like the categories sorted
    #catLinks.sort()
    return sep.join(catLinks) + '\r\n'


def compileLinkR(withoutBracketed=False, onlyBracketed=False):
    """Return a regex that matches external links."""
    # RFC 2396 says that URLs may only contain certain characters.
    # For this regex we also accept non-allowed characters, so that the bot
    # will later show these links as broken ('Non-ASCII Characters in URL').
    # Note: While allowing parenthesis inside URLs, MediaWiki will regard
    # right parenthesis at the end of the URL as not part of that URL.
    # The same applies to dot, comma, colon and some other characters.
    notAtEnd = '\]\s\)\.:;,<>"'
    # So characters inside the URL can be anything except whitespace,
    # closing squared brackets, quotation marks, greater than and less
    # than, and the last character also can't be parenthesis or another
    # character disallowed by MediaWiki.
    notInside = '\]\s<>"'
    # The first half of this regular expression is required because '' is
    # not allowed inside links. For example, in this wiki text:
    #       ''Please see http://www.example.org.''
    # .'' shouldn't be considered as part of the link.
    regex = r'(?P<url>http[s]?://[^' + notInside + ']*?[^' + notAtEnd + '](?=[' + notAtEnd+ ']*\'\')|http[s]?://[^' + notInside + ']*[^' + notAtEnd + '])'

    if withoutBracketed:
        regex = r'(?<!\[)' + regex
    elif onlyBracketed:
        regex = r'\[' + regex
    linkR = re.compile(regex)
    return linkR

