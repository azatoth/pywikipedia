#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This robot checks copyright text in Google and Yahoo.

Google search requires to install the pyGoogle module from http://pygoogle.sf.net
and get a Google API license key from http://code.google.com/apis/soapsearch/ (but
since December 2006 Google is no longer issuing new SOAP API keys).

Yahoo! search requires pYsearch module from http://pysearch.sourceforge.net and
a Yahoo AppID from http://developer.yahoo.com.

You can run the bot with the following commandline parameters:

-g           - Use Google search engine
-ng          - Do not use Google
-y           - Use Yahoo! search engine
-ny          - Do not use Yahoo!
-maxquery    - Stop after a specified number of queries for page (default: 25)
-skipquery   - Skip a number specified of queries
-new

-output      - Append results to a specified file (default: 'copyright/output.txt')
-file        - Work on all pages given in a local text file.
               Will read any [[wiki link]] and use these articles.
               Argument can also be given as "-file:filename".
-cat         - Work on all pages which are in a specific category.
               Argument can also be given as "-cat:categoryname".
-subcat      - When the pages to work on have been chosen by -cat, pages in
               subcategories of the selected category are also included.
               When -cat has not been selected, this has no effect.
-page        - Only check a specific page.
               Argument can also be given as "-page:pagetitle". You can give this
               parameter multiple times to check multiple pages.
-ref         - Work on all pages that link to a certain page.
               Argument can also be given as "-ref:referredpagetitle".
-filelinks   - Works on all pages that link to a certain image.
               Argument can also be given as "-filelinks:ImageName".
-links       - Work on all pages that are linked to from a certain page.
               Argument can also be given as "-links:linkingpagetitle".
-start       - Work on all pages in the wiki, starting at a given page.
-namespace:n - Number of namespace to process. The parameter can be used
               multiple times.

Examples:

If you want to check first 50 new articles then use this command:

    python copyright.py -new:50

If you want to check a category with no limit for number of queries to
request, use this:

    python copyright.py -cat:"Wikipedia featured articles" -maxquery:0

"""

#
# (C) Francesco Cosoleto, 2006
#
# Distributed under the terms of the MIT license.
#

from __future__ import generators
import sys, re, codecs, os, time
import wikipedia, pagegenerators, catlib, config, mediawiki_messages

__version__='$Id$'

#search_in_msn = False
exclude_quote = True

appdir = "copyright/"
output_file = appdir + "output.txt"

pages_for_exclusion_database = [
('it', 'User:RevertBot/Lista_di_esclusione', 'exclusion_list.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Abc', 'Abc.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Def', 'Def.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Ghi', 'Ghi.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Jkl', 'Jkl.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Mno', 'Mno.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Pqr', 'Pqr.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Stu', 'Stu.txt'),
('en', 'Wikipedia:Mirrors_and_forks/Vwxyz', 'Vwxyz.txt'),
#('de', 'Wikipedia:Weiternutzung', 'Weiternutzung.txt'),
('it', 'Wikipedia:Cloni', 'Cloni.txt'),
#('pl', 'Wikipedia:Mirrory_i_forki_polskiej_Wikipedii', 'Mirrory_i_forki_polskiej_Wikipedii.txt'),
#('pt', 'Wikipedia:Clones_da_Wikipédia', 'Clones_da_Wikipédia.txt'),
#('sv', 'Wikipedia:Spegelsidor', 'Spegelsidor.txt'),
]

sections_to_skip = {
'en':['References', 'Further reading', 'Citations', 'External links'],
'it':['Bibliografia', 'Riferimenti bibliografici', "Collegamenti esterni"],
}

def skip_section(text):
    l = list()
    for s in sections_to_skip.values():
        l.extend(s)
    sect_titles = '|'.join(l)

    sectC = re.compile('(?mi)^==\s*(' + sect_titles + ')\s*==')
    newtext = ''

    while True:
        newtext = cut_section(text, sectC)
        if newtext == text:
            break
        text = newtext
    return text

def cut_section(text, sectC):
    sectendC = re.compile('(?m)^==[^=]')
    start = sectC.search(text)
    if start:
        end = sectendC.search(text, start.end())
        if end:
            return text[:start.start()]+text[end.start():]
        else:
            return text[:start.start()]
    return text

def exclusion_file_list():
    for i in pages_for_exclusion_database:
        path = appdir + i[0] + '/' + i[2]
        mediawiki_messages.makepath(path)
        p = wikipedia.Page(wikipedia.getSite(i[0]),i[1])
        yield p, path

def load_pages(force_update = False):
    for page, path in exclusion_file_list():
        try:
            length = 0
            length = os.path.getsize(path)
            file_age = time.time() - os.path.getmtime(path)
            if file_age > 24 * 60 * 60:
                print 'Updating page [[' + page.title() + ']] to exclude new URLs...'
                length = 0
        except OSError:
            pass

        if length == 0 or force_update:
            try:
                data = page.get()
                f = codecs.open(path, 'w', 'utf-8')
                f.write(data)
                f.close()
            except wikipedia.IsRedirectPage:
                data = page.get(get_redirect=True)
            except:
                print 'Getting page failed'
    return

def check_list(text, cl, debug=False):
    for entry in cl:
        if entry:
            if text.find(entry) != -1:
                #print entry
                if debug:
                    print 'SKIP URL ' + text
                return True

def exclusion_list():
    prelist = []
    result_list = []
    load_pages()

    for page, path in exclusion_file_list():
        if 'exclusion_list.txt' in path:
            result_list += re.sub("</?pre>","", read_file(path, cut_comment = True)).splitlines()
        else:
            data = read_file(path)
            # wikipedia:en:Wikipedia:Mirrors and forks
            prelist += re.findall("(?i)url\s*=\s*<nowiki>(?:http://)?(.*)</nowiki>", data)
            prelist += re.findall("(?i)\*\s*Site:\s*\[?(?:http://)?(.*)\]?", data)
            # wikipedia:it:Wikipedia:Cloni
            if 'it/Cloni.txt' in path:
                prelist += re.findall('(?mi)^==(?!=)\s*\[?\s*(?:<nowiki>)?\s*(?:http://)?(.*?)(?:</nowiki>)?\s*\]?\s*==', data)
    list1 = []
    for entry in prelist:
        list1 += entry.split(", ")
    list2 = []
    for entry in list1:
        list2 += entry.split("and ")
    for entry in list2:
        # Remove unnecessary part of URL
        entry = re.sub("http://", "", entry)
        entry = re.sub("www\.", "", entry)
        entry = re.sub("</?nowiki>", "", entry)
        if entry:
            if '/' in entry:
                result_list += [re.sub(" .*", "", entry[:entry.rfind('/')])]
            else:
                result_list += [re.sub(" .*", "", entry)]

    result_list += read_file(appdir + 'exclusion_list.txt', cut_comment = True).splitlines()
    return result_list

def read_file(filename, cut_comment = False):
    text = u""
    f = codecs.open(filename, 'r','utf-8')
    text = f.read()
    if cut_comment:
        text = re.sub(" ?#.*", "", text)
    f.close()
    return text

def write_log(text, filename = output_file):
    f = codecs.open(filename, 'a', 'utf-8')
    f.write(text)
    f.close()

#
# Set regex used in cleanwikicode() to remove [[Image:]] tags
# and regex used in check_in_source() to reject pages with
# 'Wikipedia'.

def join_family_data(reString, namespace):
    for s in wikipedia.Family().namespaces[namespace].itervalues():
        if type (s) == type([]):
            for e in s:
                reString += '|' + e
        else:
            reString += '|' + s
    return '\s*(' + reString + ')\s*'

reImageC = re.compile('\[\[' + join_family_data('Image', 6) + ':.*?\]\]', re.I)
reWikipediaC = re.compile(join_family_data('Wikipedia', 4).replace("|Wiki|", "|"), re.I)

def cleanwikicode(text):
    if not text:
        return ""
    #write_log(text+'\n', "debug_cleanwikicode1.txt")
    text = re.sub('(?i)<p.*?>' ,'', text)
    text = re.sub('(?i)</?div.*?>' ,'', text)
    text = re.sub("(?i)</*small>", "", text)
    text = re.sub('(?i)<(/\s*)?br(\s*/)?>', '', text)
    text = re.sub('<!--.*?-->', '', text)
    text = re.sub('&lt;', '<', text)
    text = re.sub('&gt;', '>', text)

    if exclude_quote:
        text = re.sub("(?i){{quote\|.*?}}", "", text)
        text = re.sub("^[:*]?\s*''.*?''\.?\s*((\(|<ref>).*?(\)|</ref>))?\.?$", "", text)
        text = re.sub('^[:*]?\s*["][^"]+["]\.?\s*((\(|<ref>).*?(\)|</ref>))?\.?$', "", text)
        text = re.sub('^[:*]?\s*[«][^»]+[»]\.?\s*((\(|<ref>).*?(\)|</ref>))?\.?$', "", text)
        text = re.sub('^[:*]?\s*[“][^”]+[”]\.?\s*((\(|<ref>).*?(\)|</ref>))?\.?$', "", text)

    # exclude <ref> notes
    text = re.sub ("<ref.*?>.*?</ref>", "", text)
    # exclude wikitable
    text = re.sub('(?m)^[ \t]*({\||[|!]).*', "", text)
    # remove URL
    text = re.sub('https?://[\w/.,;:@&=%#\\\?_!~*\'|()\"+-]+', ' ', text)
    # remove Image tags
    text = reImageC.sub("", text)
    # replace piped wikilink
    text = re.sub("\[\[[^\]]*?\|(.*?)\]\]", "\\1", text)
    # remove unicode and polytonic template
    text = re.sub("(?i){{(unicode|polytonic)\|(.*?)}}", "\\1", text)
    # remove <nowiki> tags
    text = re.sub("</*nowiki>", "", text)
    # remove template
    text = re.sub('{{.*?}}', '', text)
    # remove LaTeX staff
    text = re.sub('<math>.*?</math>', '', text)
    #text = text.replace("''", "")
    text = text.replace("[", "")
    text = text.replace("]", "")
    text = re.sub('^[*:;]', '', text)

    text = text.replace("<!--", "")
    text = text.replace("-->", "")

    #if text:
    #    write_log(text+'\n', "debug_cleanwikicode2.txt")
    return text

excl_list = exclusion_list()

def exclusion_list_dump():
    res = ''
    for entry in excl_list:
        res += entry + '\n'
    f = open(appdir + 'exclusion_list.dump', 'w')
    f.write(res)
    f.close()

def n_index(text, n, sep):
    pos = 0
    while n>0:
        try:
            pos = text.index(sep, pos + 1)
            n -= 1
        except ValueError:
            return 0
    return pos

def mysplit(text, dim, sep):
    if not sep in text:
        return [text]
    t = text
    l = list()
    while t:
        if sep in t:
            n = n_index(t, dim, sep)
            if n>0:
                l.append(t[:n])
                t = t[n+1:]
                continue
        l.append(t)
        break
    return l

def query(lines = [], max_query_len = 1300):
    # Google max_query_len = 1480?
    # - '-Wikipedia ""' = 1467

    # Google limit queries to 32 words.

    output = u""
    n_query = 0
    previous_group_url = 'none'

    for line in lines:
        line = cleanwikicode(line)
        for search_words in mysplit(line, 31, " "):
            if len(search_words) > 120:
                n_query += 1
                #wikipedia.output(search_words)
                if config.copyright_max_query_for_page and n_query > config.copyright_max_query_for_page:
                    wikipedia.output(u"Max query limit for page reached")
                    return output
                if config.copyright_skip_query > n_query:
                    continue
                if len(search_words) > max_query_len:
                    search_words = search_words[:max_query_len]
                    consecutive = False
                    if " " in search_words:
                         search_words = search_words[:search_words.rindex(" ")]
                results = get_results(search_words)
                group_url = ''
                for url, engine in results:
                    group_url += '\n*%s - %s' % (engine, url)
                if results:
                    group_url_list = group_url.splitlines()
                    group_url_list.sort()
                    group_url = '\n'.join(group_url_list)
                    if previous_group_url == group_url:
                        if consecutive:
                            output += ' ' + search_words
                        else:
                            output += '\n**' + search_words
                    else:
                        output += group_url + '\n**' + search_words

                    previous_group_url = group_url
                    consecutive = True
                else:
                    consecutive = False
            else:
               consecutive = False

    return output

source_seen = set()
positive_source_seen = set()

def check_in_source(url):
    """
    Sources may be different from search engine database and include mentions of
    Wikipedia. This function avoid also errors in search results that can occurs
    either with Google and Yahoo! service.
    """
    import urllib2
    global excl_list, source_seen, positive_source_seen

    if url in positive_source_seen:
        return True

    if url in source_seen:
        return False

    if check_list(url, excl_list):
        return False

    # very experimental code
    if not url[-4:] in [".pdf", ".doc", ".ppt"]:
        try:
            resp = urllib2.urlopen(url)
            text = resp.read()
            #resp.close()
        except urllib2.HTTPerror:
            return False

            if reWikipediaC.search(text):
                # if 'wikipedia' in text.lower():
                excl_list += [url]
                #write_log(url + '\n', "copyright/sites_with_'wikipedia'.txt")
                positive_source_seen.add(url)
                return True
            else:
                #write_log(url + '\n', "copyright/sites_without_'wikipedia'.txt")
                source_seen.add(url)
    return False

def add_in_urllist(url, add_item, engine):
    for i in range(len(url)):
        if add_item in url[i]:
            if engine not in url[i][1]:
                url[i] = (add_item, url[i][1] + ', ' + engine)
            return
    url.append((add_item, engine))
    return

def get_results(query, numresults = 10):
    url = list()
    query = re.sub("[()\"<>]", "", query)
    #wikipedia.output(query)
    if config.copyright_google:
        import google
        google.LICENSE_KEY = config.google_key
        print "  google query..."
        search_request_retry = config.copyright_connection_tries
        while search_request_retry:
            try:
                data = google.doGoogleSearch('-Wikipedia "' + query + '"')
                search_request_retry = 0
                for entry in data.results:
                    if config.copyright_check_in_source_google:
                        if check_in_source(entry.URL):
                            continue
                    add_in_urllist(url, entry.URL, 'google')
            except KeyboardInterrupt:
                raise
            except Exception, err:
                #SOAP.faultType: <Fault SOAP-ENV:Server: Exception from service object:
                # Daily limit of 1000 queries exceeded for key xxx>
                print "Got an error ->", err
                if search_request_retry:
                    search_request_retry -= 1
    if config.copyright_yahoo:
        import yahoo.search.web
        print "  yahoo query..."
        data = yahoo.search.web.WebSearch(config.yahoo_appid, query='"' +
                                          query.encode('utf_8') +
                                          '" -Wikipedia', results=numresults)
        search_request_retry = config.copyright_connection_tries
        while search_request_retry:
            try:
                for entry in data.parse_results():
                    if config.copyright_check_in_source_yahoo:
                        if check_in_source(entry.Url):
                            continue
                    add_in_urllist(url, entry.Url, 'yahoo')
                search_request_retry = 0
            except Exception, err:
                print "Got an error ->", err
                if search_request_retry:
                    search_request_retry -= 1
    #if search_in_msn:
    #    ## max_query_len = 150?
    #    from __SOAPpy import WSDL
    #    print "  msn query..."
    #    wsdl_url = 'http://soap.search.msn.com/webservices.asmx?wsdl'
    #    server = WSDL.Proxy(wsdl_url)
    #    params = {'AppID': config.msn_appid, 'Query': '-Wikipedia "' + query + '"', 'CultureInfo': 'en-US', 'SafeSearch': 'Off', 'Requests': {
    #             'SourceRequest':{'Source': 'Web', 'Offset': 0, 'Count': 10, 'ResultFields': 'All',}}}
    #
    #    search_request_retry = config.copyright_connection_tries
    #    results = ''
    #    while search_request_retry:
    #        try:
    #            server_results = server.Search(Request = params)
    #            search_request_retry = 0
    #            if server_results.Responses[0].Results:
    #                results = server_results.Responses[0].Results[0]
    #        except Exception, err:
    #            print "Got an error ->", err
    #            search_request_retry -= 1
    #    for entry in results:
    #         try:
    #             add_in_urllist(url, entry.Url, 'msn')
    #         except AttributeError:
    #             print "attrib ERROR"

    offset = 0
    for i in range(len(url)):
        if check_list(url[i + offset][0], excl_list, debug = True):
            url.pop(i + offset)
            offset += -1
    return url

def get_by_id(title, id):
    return wikipedia.getSite().getUrl("/w/index.php?title=%s&oldid=%s&action=raw" % (title, id))

def checks_by_ids(ids):
    for title, id in ids:
        original_text = get_by_id(title, id)
        if original_text:
            wikipedia.output(original_text)
            output = query(lines=original_text.splitlines())
            if output:
                write_log("=== [[" + title + "]] ===\n{{/box|%s|prev|%s|%s|00}}" % (title.replace(" ", "_").replace("\"", "%22"), id, "author") + output, "copyright/ID_output.txt")

class CheckRobot:
    def __init__(self, generator):
        """
        """
        self.generator = generator

    def run(self):
        """
        Starts the robot.
        """
        # Run the generator which will yield Pages which might need to be
        # checked.
        for page in self.generator:
            try:
                # Load the page's text from the wiki
                original_text = page.get()
            except wikipedia.NoPage:
                wikipedia.output(u'Page %s not found' % page.title())
                continue
            except wikipedia.IsRedirectPage:
                original_text = page.get(get_redirect=True)

#            colors = [13] * len(page.title())
    	    wikipedia.output(page.title())

	    if original_text:
                text = skip_section(original_text)
                output = query(lines = text.splitlines())
                if output:
                   write_log('=== [[' + page.title() + ']] ===' + output + '\n', filename = output_file)

def check_config(var, license_id, license_name):
    if var:
        if not license_id:
            wikipedia.output(u"WARNING: You don't have set a " + license_name + ", search engine is disabled.")
            return False
    return var

def main():
    global output_file
    gen = None
    # pages which will be processed when the -page parameter is used
    PageTitles = []
    # IDs which will be processed when the -ids parameter is used
    ids = None
    # will become True when the user presses a ('yes to all') or uses the -always
    # commandline paramater.
    acceptall = False
    # Which namespaces should be processed?
    # default to [] which means all namespaces will be processed
    namespaces = []
    #
    #repeat = False

    firstPageTitle = None
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()


    config.copyright_yahoo = check_config(config.copyright_yahoo, config.yahoo_appid, "Yahoo AppID")
    config.copyright_google = check_config(config.copyright_google, config.google_key, "Google Web API license key")

    # Read commandline parameters.
    for arg in wikipedia.handleArgs():
        #if arg.startswith('-repeat'):
        #    repeat = True
        if arg.startswith('-y'):
            config.copyright_yahoo = True
        elif arg.startswith('-g'):
            config.copyright_google = True
        elif arg.startswith('-ny'):
            config.copyright_yahoo = False
        elif arg.startswith('-ng'):
            config.copyright_google = False
        elif arg.startswith('-output'):
            if len(arg) >= 8:
                output_file = arg[8:]
        elif arg.startswith('-maxquery'):
            if len(arg) >= 10:
                config.copyright_max_query_for_page = int(arg[10:])
        elif arg.startswith('-skipquery'):
            if len(arg) >= 11:
                config.copyright_skip_query = int(arg[11:])
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = wikipedia.input(u'Please enter the XML dump\'s filename:')
            else:
                xmlFilename = arg[5:]
        elif arg.startswith('-page'):
            if len(arg) == 5:
                PageTitles.append(wikipedia.input(u'Which page do you want to change?'))
            else:
                PageTitles.append(arg[6:])
        elif arg.startswith('-namespace:'):
            namespaces.append(int(arg[11:]))
        elif arg.startswith('-forceupdate'):
            load_pages(force_update = True)
        else:
            generator = genFactory.handleArg(arg)
            if generator:
                gen = generator

    if PageTitles:
        pages = [wikipedia.Page(wikipedia.getSite(), PageTitle) for PageTitle in PageTitles]
        gen = iter(pages)

    if ids:
        checks_by_ids(ids)

    if not gen and not ids:
        # syntax error, show help text from the top of this file
        wikipedia.output(__doc__, 'utf-8')
    if not gen:
        wikipedia.stopme()
        sys.exit()
    if namespaces != []:
        gen =  pagegenerators.NamespaceFilterPageGenerator(gen, namespaces)
    preloadingGen = pagegenerators.PreloadingGenerator(gen, pageNumber = 20)
    bot = CheckRobot(preloadingGen)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()