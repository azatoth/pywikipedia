# -*- coding: iso8859-1 -*-
"""
Script to copy a table from one Wikipedia to another one, translating it
on-the-fly. 

Syntax:
  copy_table.py -type:abcd -from:xy Article_Name

Command line options:

-from:xy       Copy the table from the Wikipedia article in language xy
               Article must have interwiki link to xy

-debug         Show debug info, and don't send the results to the server
              
-type:abcd     Translates the table, using translations given below.
               When the -type argument is not used, the bot will simply
               copy the table as-is.

-file:XYZ      Reads article names from a file. XYZ is the name of the 
               file from which the list is taken. If XYZ is not given, the
               user is asked for a filename.
               Page titles should be saved one per line, without [[brackets]].
               The -pos parameter won't work if -file is used.                              

-image         Copy all images within the found table to the target Wikipedia

Article_Name:  Name of the article where a table should be inserted

"""
#
# (C) Daniel Herding, 2004
#
# Distribute under the terms of the PSF license.
#
__version__='$Id$'
#
import wikipedia, translator, re, sys, string

# Summary message
msg={
    "en":"robot: copying table from ",
    "de":"Bot: Kopiere Tabelle von ",
    }

# get edit summary message
if msg.has_key(wikipedia.mylang):
    msglang = wikipedia.mylang
else:
    msglang = "en"

# prints text on the screen only if in -debug mode
def print_debug(text):
    if debug:
        print text
    
# if the -file argument is used, page titles are dumped in this array.
# otherwise it will only contain one page.
page_list = []
from_lang = ""
type = ""
debug = False
copy_images = False

# read command line parameters
for arg in sys.argv[1:]:
    if wikipedia.argHandler(arg):
        pass
    elif arg.startswith("-from"):
        from_lang = arg[6:]
    elif arg.startswith("-type:"):
        type = arg[6:]
    elif arg == "-debug":
        debug = True
    elif arg == "-image":
        copy_images = True
    elif arg.startswith('-file'):
        if len(arg) == 5:
            file = raw_input('Please enter the list\'s filename: ')
        else:
            file = arg[6:]
        # open file and read page titles out of it
        f=open(file)
        for line in f.readlines():
            if line != '\n':           
                page_list.append(line)
        f.close()
    else:
        page_list.append(arg)

# this is a modified version of wikipedia.imagelinks(). Maybe we can
# unify both.
def imagelinks(lang, text):
    result = []
    # check if we know this wikipedia's image namespace name
    if lang in wikipedia.image:
        im=wikipedia.image[lang] + ':'
    else:
        im='Image:'
    w1=r'('+im+'[^\]\|]*)'
    w2=r'([^\]\|]*)'
    Rlink = re.compile(r'\[\['+w1+r'(\|'+w2+r')?\]\]')
    for l in Rlink.findall(text):
        result.append(wikipedia.PageLink(lang, l[0]))
    return result


def treat(to_pl):
    try:
        to_text = to_pl.get()
        interwikis = to_pl.interwiki()
    except wikipedia.IsRedirectPage:
        print "Can't work on redirect page."
        return
    except wikipedia.NoPage:
        print "Page not found."
        return
    from_pl = ""
    for interwiki in interwikis:
        if interwiki.code() == from_lang:
            from_pl = interwiki
    if from_pl == "":
        print "Interwiki link to " + from_lang + " not found."
        return
    from_text = from_pl.get()
    wikipedia.setAction(msg[msglang] + from_lang + ":" + from_pl.linkname())
    # search start of table
    table = get_table(from_text)
    if not table:
        print "No table found in %s." % from_lang + ":" + from_pl.linkname()
        return
    translated_table = translator.translate(table, type, from_lang, debug, wikipedia.mylang)
    if not translated_table:
        print "Could not translate table."
        return
    print_debug("\n" + translated_table)
    # add table to top of the article, seperated by a blank lines
    to_text = translated_table + "\n\n" + to_text
    if not debug:
        print "Changing page %s" % (to_pl)
        # save changes on Wikipedia
        to_pl.put(to_text, minorEdit='0')

    print_debug("Copying images")
    if copy_images:
        # extract image links from original table
        images=imagelinks(from_lang, table)
        import lib_images
        for i in images:
            lib_images.transfer_image(i, wikipedia.mylang, debug)
            
        

# Regular expression that will match both <table and {|
startR = re.compile(r"<table|\{\|")
# Regular expression that will match both </table> and |}
endR = re.compile(r"</table>|\|\}")

# Finds the first table inside a text, including cascaded inner tables.
def get_table(text):
    pos = 0
    # find first start tag
    first_start_tag = re.search(startR, text)
    if not first_start_tag:
        return
    else:
        print_debug("First start tag found at " + str(first_start_tag.start()))
        pos = first_start_tag.end()
        # number of start tags minus numer of end tags
        table_level = 1
        remaining_text = text
    # until an end tag has been found for each start tag:
    while table_level != 0:
        # continue search after the last found tag
        remaining_text = text[pos:]
        next_start_tag = re.search(startR, remaining_text, pos)
        next_end_tag = re.search(endR, remaining_text, pos)
        if not next_end_tag:
            print_debug("Error: missing end tag")
            pass
        # if another cascaded table is opened before the current one is closed    
        elif next_start_tag and next_start_tag.start() < next_end_tag.start():
            print_debug( "Next start tag found at " + str(pos + next_start_tag.start()))
            pos += next_start_tag.end()
            table_level += 1
            print_debug("Table level is " + str(table_level))
        else:
            print_debug( "Next end tag found at " + str(pos + next_end_tag.start()))
            pos += next_end_tag.end()
            table_level -= 1
            print_debug("Table level is " + str(table_level))
    print_debug("Table starts at " + str(first_start_tag.start()) + " and ends at " + str(pos) +"\n")
    print_debug(text[first_start_tag.start():pos])
    return text[first_start_tag.start():pos]

        
for current_page_name in page_list:
    thispl = wikipedia.PageLink(wikipedia.mylang, current_page_name)
    treat(thispl)
