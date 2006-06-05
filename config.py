# -*- coding: utf-8 -*-
#
# (C) Rob W.W. Hooft, 2003
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os, re, sys

# IMPORTANT:
# Do not change any of the variables in this file. Instead, make
# a file user-config.py, and overwrite values in there.

############## ACCOUNT SETTINGS ##############

# The family of sites we are working on. wikipedia.py will import
# families/xxx_family.py so if you want to change this variable,
# you need to write such a file.
family = 'wikipedia'
# The language code of the site we're working on.
mylang = 'language'

# The dictionary usernames should contain a username for each site where you
# have a bot account. Please set your usernames by adding such lines to your
# user-config.py:
#
# usernames['wikipedia']['de'] = 'myGermanUsername'
# usernames['wiktionary']['en'] = 'myEnglishUsername'
#
# If you have a sysop account one some wikis, this will be used to delete pages
# or to edit locked pages if you add such lines to your
# user-config.py:
#
# sysopnames['wikipedia']['de'] = 'myGermanUsername'
# sysopnames['wiktionary']['en'] = 'myEnglishUsername'
usernames = {}
sysopnames = {}
disambiguation_comment = {}

# Some sites will require password identication to access the HTML pages at
# the site. If you have any such site, add lines to your user-config.py of
# the following form:
#
# authenticate['en.wikipedia.org'] = ('John','XXXXX')
#
# where John is your login name, and XXXXX your password.
# Note:
# 1. This is only for sites that use authentication in the form that gives
#    you a popup for name and password when you try to access any data, NOT
#    for, for example, wiki usernames
# 2. You must use the hostname of the site, not its family/language pair
authenticate = {}

# Get the names of all known families, and initialize
# with empty dictionaries
RfamilyFile = re.compile('(?P<name>.+)_family.py$')
for filename in os.listdir('families'):
    m = RfamilyFile.match(filename)
    if m:
        familyName = m.group('name')
        usernames[familyName] = {}
        sysopnames[familyName] = {}
        disambiguation_comment[familyName] = {}

############## USER INTERFACE SETTINGS ##############

# The encoding that's used in the user's console, i.e. how strings are encoded
# when they are read by raw_input(). On Windows systems' DOS box, this should
# be 'cp850' ('cp437' for older versions). Linux users might try 'iso-8859-1'
# or 'utf-8'. If this variable is set to None, the default is 'cp850' on
# windows, and iso-8859-1 on other systems
console_encoding = None

# The encoding in which textfiles are stored, which contain lists of page titles.
textfile_encoding = 'utf-8'

# tkinter isn't yet ready
userinterface = 'terminal'

# Should the system bell be ringed if the bot expects user input?
ring_bell = True

# Colorization can be used to markup important text parts of the output.
# ANSI escape codes are used for this. Unfortunatelly this only works in
# Linux/Unix terminals.
# Set this to False if you're using Linux and your tty doesn't support
# ANSI colors.
colorized_output = (sys.stdout.isatty() and sys.platform != 'win32')

############## EXTERNAL EDITOR SETTINGS ##############
# The command for the editor you want to use. If set to None, a simple Tkinter
# editor will be used.
editor = None

# Warning: DO NOT use an editor which doesn't support Unicode to edit pages!
# You will BREAK non-ASCII symbols!
editor_encoding = 'utf-8'

# The temporary file name extension can be set in order to use syntax
# highlighting in your text editor.
editor_filename_extension = 'wiki'

############## LOGFILE SETTINGS ##############

# Should all bots keep a logfile?
# TODO: Not used yet
always_log = False
# Should no bot, not even interwiki.py, keep a logfile?
never_log = False

############## INTERWIKI SETTINGS ##############

# Should interwiki.py report warnings for missing links between foreign
# languages?
interwiki_backlink = True

# Should interwiki.py display every new link it discovers?
interwiki_shownew = True

# Should interwiki.py output a graph PNG file on conflicts?
# You need pydot for this: http://dkbza.org/pydot.html
interwiki_graph = False

# If interwiki graphs are enabled, which format should be used?
# Supported formats include png, jpg, ps and svg.
interwiki_graph_format = 'png'

# If interwiki graphs are enabled, should we save the dot file
# too ? Usefull to make another graph with the same data
interwiki_graph_dumpdot = False

# Save file with local articles without interwikis.
without_interwiki = False

############## SOLVE_DISAMBIGUATION SETTINGS ############
#
# Set disambiguation_comment[FAMILY][LANG] to a non-empty string to override
# the default edit comment for the solve_disambiguation bot.
# Use %s to represent the name of the disambiguation page being treated.
# Example:
#
# disambiguation_comment['wikipedia']['en'] = \
#    "Robot-assisted disambiguation ([[WP:DPL|you can help!]]): %s"

############## IMAGE RELATED SETTINGS ##############
# If you set this to True, images will be uploaded to Wikimedia
# Commons by default.
upload_to_commons = False

############## SETTINGS TO AVOID SERVER OVERLOAD ##############

# Slow down the robot such that it never requests a second page within
# 'minthrottle' seconds. This can be lengthened if the server is slow,
# but never more than 'maxthrottle' seconds. However - if you are running
# more than one bot in parallel the times are lengthened.
minthrottle = 1
maxthrottle = 10

# Slow down the robot such that it never makes a second change within
# 'put_throttle' seconds.
put_throttle = 10
# Sometimes you want to know when a delay is inserted. If a delay is larger
# than 'noisysleep' seconds, it is logged on the screen.
noisysleep = 3.0

# Maximum of pages which can be retrieved by special pages. Increase this if
# you heavily use boilerplate.py, double_redirect.py, and especially if you're
# running solve_disambiguation.py with the -primary argument.
special_page_limit = 500

############## TABLE CONVERSION BOT SETTINGS ##############

# will split long paragraphs for better reading the source.
# only table2wiki.py use it by now
splitLongParagraphs = False
# sometimes HTML-tables are indented for better reading.
# That can do very ugly results.
deIndentTables = True
# table2wiki.py works quite stable, so you might switch to True
table2wikiAskOnlyWarnings = True
table2wikiSkipWarnings = False

############## WEBLINK CHECKER SETTINGS ##############

# How many external links should weblinkchecker.py check at the same time?
# If you have a fast connection, you might want to increase this number so
# that slow servers won't slow you down.
max_external_links = 50

report_dead_links_on_talk = False

############## DATABASE SETTINGS ##############
db_hostname = 'localhost'
db_username = 'wikiuser'
db_password = ''

############## FURTHER SETTINGS ##############

# The bot can make some additional changes to each page it edits, e.g. fix
# whitespace or positioning of interwiki and category links.

# This is an experimental feature; handle with care and consider re-checking 
# each bot edit if enabling this!
cosmetic_changes = False

# If cosmetic changes are switched on, and you also have several accounts at
# projects where you're not familiar with the local conventions, you probably
# only want the bot to do cosmetic changes on your "home" wiki which you
# specified in config.mylang and config.family.
# If you want the bot to also do cosmetic changes when editing a page on a
# foreign wiki, set cosmetic_changes_mylang_only to False, but be careful!
cosmetic_changes_mylang_only = True

# Some scripts allow using the Google Web API. To use this feature, you must
# install the pyGoogle module from http://pygoogle.sf.net/ and get a Google
# Web API license key from http://www.google.com/apis/index.html .
google_key = ''

# End of configuration section
# ============================
# System-level and User-level changes.
# Store current variables and their types.
_glv={}
_glv.update(globals())
_gl=_glv.keys()
_tp={}
for _key in _gl:
    if _key[0]!='_':
        _tp[_key]=type(globals()[_key])
del _key
# Get the user files
_thislevel=0
_fns=["user-config.py"]
for _filename in _fns:
    _thislevel += 1
    if os.path.exists(_filename):
        _filestatus=os.stat(_filename)
        _filemode=_filestatus[0]
        _fileuid=_filestatus[4]
        if (sys.platform=='win32' or _fileuid==os.getuid() or _fileuid==0):
            if sys.platform=='win32' or _filemode&002==0:
                execfile(_filename)
            else:
                print "WARNING: Skipped '%s': writeable by others."%_filename
        else:
            print "WARNING: Skipped '%s': owned by someone else."%_filename
        del _filemode,_fileuid,_filestatus
del os,sys,_filename,_thislevel,_fns
# Test for obsoleted and/or unknown variables.
for _key in globals().keys():
    if _key[0]=='_':
        pass
    elif _key in _gl:
        nt=type(globals()[_key])
        ot=_tp[_key]
        if nt==ot or nt==type(None) or ot==type(None):
            pass
        elif nt==type(1) and ot==type(1.0):
            pass
        elif ot==type(1) and nt==type(1.0):
            pass
        elif nt==type(1) and ot==type(True):
            pass
        elif ot==type(1) and nt==type(True):
            pass
        else:
            print "WARNING: Type of '%s' changed"%_key
            print "       Was: ",ot
            print "       Now: ",nt
        del nt,ot
    else:
        print "WARNING: Configuration variable %s not known. Misspelled?"%_key
del _key,_tp

# Fix up default console_encoding
if console_encoding == None:
    import sys as _sys
    if _sys.platform=='win32':
        console_encoding = 'cp850'
    else:
        console_encoding = 'iso-8859-1'
    del _sys
#
# When called as main program, list all configuration variables
#
if __name__=="__main__":
    import sys as _sys
    _all=1
    for _arg in _sys.argv[1:]:
        if _arg=="modified":
            _all=0
        else:
            print "Unknown arg %s ignored"%_arg
    _k=globals().keys()
    _k.sort()
    for _name in _k:
        if _name[0]!='_':
            if _all or _glv[_name]!=globals()[_name]:
                print _name,"=",repr(globals()[_name])
    del _sys
    
del _glv
