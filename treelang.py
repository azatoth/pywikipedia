#coding: iso-8859-1
"""
Script to check language links for general pages. This works by downloading the
page, and using existing translations plus hints from the command line to
download the equivalent pages from other languages. All of such pages are
downloaded as well and checked for interwiki links recursively until there are
no more links that are encountered. A rationalization process then selects the
right interwiki links, and if this is unambiguous, the interwiki links in the
original page will be automatically updated and the modified page uploaded.

This script understands various command-line arguments:
    -force: do not ask permission to make "controversial" changes, like
            removing a language because none of the found alternatives actually
            exists.
    -always: make changes even when a single byte is changed in the page,
             not only when one of the links has a significant change.
    -same: try to translate the page to other languages by testing whether
           a page with the same name exists on each of the other known 
           wikipedias
    -hint: used as -hint:de:Anweisung to give the robot a hint where to
           start looking for translations
    -name: similar to -same, but UPPERCASE the last name for eo:
    -untranslated: untranslated pages are not skipped; instead in those
                   cases interactively a translation hint is asked of the user.
    -confirm: ask for confirmation in all cases. Without this argument, 
              additions and unambiguous modifications are made without
              confirmation.
    -autonomous: run automatically, do not ask any questions. If a question
                 to an operator is needed, write the name of the page
                 to autonomous_problems.dat and terminate.

    Arguments that are interpreted by more bot:

    -lang: specifies the language the bot is run on (e.g. -lang:de).
           Overwrites the settings in username.dat
    
     All other arguments are words that make up the page name.

Two configuration options can be used to change the workings of this robot:

treelang_backlink: if set to True, all problems in foreign wikipedias will
                   be reported
treelang_log:      if set to True, all messages will be logged to a file
                   as well as being displayed to the screen.

Both these options are set to True by default. They can be changed through
the user-config.py configuration file.

"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distribute under the terms of the PSF license.
#
__version__ = '$Id$'
#
import sys, copy, re

import wikipedia, config, titletranslate, unequal

# Summary used in the modification request
wikipedia.setAction('semi-automatic interwiki script')

debug = 1
forreal = 1

msg = {
    'en':('Adding','Removing','Modifying'),
    'nl':('Erbij','Eraf','Anders'),
    'da':('Tilf�jer','Fjerner','�ndrer'),
    'fr':('Ajoute','Retire','Modifie'),
    'de':('Erg�nze','Entferne','�ndere'),
    }
        
def autonomous_problem(pl, reason = ''):
    if autonomous:
        f=open('autonomous_problem.dat', 'a')
        f.write("%s {%s}\n" % (pl, reason))
        f.close()
        sys.exit(1)
    
def compareLanguages(old, new):
    global confirm
    removing = []
    adding = []
    modifying = []
    for code in old.keys():
        if code not in new.keys():
            confirm += 1
            removing.append(code)
        elif old[code] != new[code]:
            modifying.append(code)

    for code2 in new.keys():
        if code2 not in old.keys():
            adding.append(code2)
    s = ""
    if adding:
        s = s + " %s:" % (msg[msglang][0]) + ",".join(adding)
    if removing: 
        s = s + " %s:" % (msg[msglang][1]) + ",".join(removing)
    if modifying:
        s = s + " %s:" % (msg[msglang][2]) + ",".join(modifying)
    return s,removing

#===========
    
def treestep(arr, pl, abort_on_redirect = 0):
    assert arr[pl] is None
    print "Getting %s"%pl
    n = 0
    try:
        text = pl.get()
    except wikipedia.NoPage:
        print "---> Does not actually exist"
        arr[pl] = ''
        return 0
    except wikipedia.LockedPage:
        print "---> Locked"
        arr[pl] = 1
        return 0
    except wikipedia.IsRedirectPage,arg:
        if abort_on_redirect and pl.code() == wikipedia.mylang:
            raise
        newpl = wikipedia.PageLink(pl.code(), str(arg))
        arr[pl] = ''
        print "NOTE: %s is a redirect to %s" % (pl, newpl)
        if not newpl in arr:
            if unequal.unequal(inpl, newpl):
                print "NOTE: %s is unequal to %s, not adding it" % (newpl, inpl)
            else:
                arr[newpl] = None
            return 1
        return 0
    arr[pl] = text
    if unequal.bigger(inpl,pl):
        print "NOTE: %s is bigger than %s, not following references" % (pl, inpl)
    else:
        for newpl in pl.interwiki():
            if newpl not in arr:
                print "NOTE: from %s we got the new %s"%(pl,newpl)
                if unequal.unequal(inpl, newpl):
                    print "NOTE: %s is unequal to %s, not adding it" % (newpl, inpl)
                else:
                    arr[newpl] = None
                    n += 1
    return n
    
def treesearch(pl):
    arr = {pl:None}
    # First make one step based on the language itself
    try:
        n = treestep(arr, pl, abort_on_redirect = 1)
    except wikipedia.IsRedirectPage:
        print "Is redirect page"
        return
    if n == 0 and not arr[pl]:
        print "Mother doesn't exist"
        return
    if untranslated:
        if len(arr) > 1:
            print "Already has translations"
        else:
            if bell:
                sys.stdout.write('\07')
            newhint = raw_input("Hint:")
            if not newhint:
                return
            hints.append(newhint)
    # Then add translations if we survived.
    titletranslate.translate(pl, arr, same = same, hints = hints)
    modifications = 1
    while modifications:
        modifications = 0
        for newpl in arr.keys():
            if arr[newpl] is None:
                modifications += treestep(arr, newpl)
    return arr

inname = []

bell = 1
ask = 1
same = 0
log = config.treelang_log
only_if_status = 1
confirm = 0
autonomous = 0
untranslated = 0
backlink = config.treelang_backlink
hints = []

for arg in sys.argv[1:]:
    if wikipedia.argHandler(arg):
        pass
    elif arg == '-force':
        ask = False
    elif arg == '-always':
        only_if_status = False
    elif arg == '-same':
        same = True
    elif arg == '-untranslated':
        untranslated = True
    elif arg.startswith('-hint:'):
        hints.append(arg[6:])
    elif arg == '-name':
        same = 'name'
    elif arg == '-confirm':
        confirm = True
    elif arg == '-autonomous':
        autonomous = True
        bell = 0
    else:
        inname.append(arg)

if msg.has_key(wikipedia.mylang):
    msglang = wikipedia.mylang
else:
    msglang = 'en'

if log:
    import logger
    sys.stdout = logger.Logger(sys.stdout, filename = 'treelang.log')

unequal.read_exceptions()

inname = '_'.join(inname)
if not inname:
    inname = raw_input('Which page to check:')

inpl = wikipedia.PageLink(wikipedia.mylang, inname)

m = treesearch(inpl)
if not m:
    print "No matrix"
    sys.exit(1)
print "==Result=="
new = {}
k = m.keys()
k.sort()
for pl in k:
    if pl.code() == wikipedia.mylang and m[pl]:
        if pl!=inpl:
            print "ERROR: %s refers back to %s" % (inpl, pl)
            confirm += 1
            autonomous_problem(inpl, 'Someone refers to %s with us' % pl)
    elif m[pl]:
        print pl
        if new.has_key(pl.code()) and new[pl.code()] != None and new[pl.code()]!=pl:
            print "ERROR: '%s' as well as '%s'" % (new[pl.code()], pl)
            autonomous_problem(inpl,"'%s' as well as '%s'" % (new[pl.code()], pl))
            while 1:
                if bell:
                    sys.stdout.write('\07')
                confirm += 1
                answer = raw_input("Use (f)ormer or (l)atter or (n)either or (q)uit?")
                if answer.startswith('f'):
                    break
                elif answer.startswith('l'):
                    new[pl.code()] = pl
                    break
                elif answer.startswith('n'):
                    new[pl.code()] = None
                    break
                elif answer.startswith('q'):
                    sys.exit(1)
        elif pl.code() in ('zh-tw','zh-cn') and new.has_key('zh') and new['zh'] is not None:
            print "NOTE: Ignoring %s, using %s"%(new['zh'].asasciilink(),pl.asasciilink())
            new['zh'] = None # Remove the global zh link
            new[pl.code()] = pl # Add the more precise one
        elif pl.code() == 'zh' and (
            (new.has_key('zh-tw') and new['zh-tw'] is not None) or
            (new.has_key('zh-cn') and new['zh-cn'] is not None)):
            print "NOTE: Ignoring %s"%(pl.asasciilink())
            pass # do not add global zh if there is a specific zh-tw or zh-cn
        elif pl.code() not in new or new[pl.code()] != None:
            new[pl.code()] = pl

# Remove the neithers
for k,v in new.items():
    if v is None:
        del new[k]
        
print "==status=="
old={}
for pl in inpl.interwiki():
    old[pl.code()] = pl
####
mods, removing = compareLanguages(old, new)
if not mods and only_if_status:
    print "No changes"
else:
    print mods
    print "==changes should be made=="
    oldtext = m[inpl]
    newtext = wikipedia.replaceLanguageLinks(oldtext, new)
    if debug:
        import difflib
        for line in difflib.ndiff(oldtext.split('\r\n'),newtext.split('\r\n')):
            if line[0] in ['+','-']:
                print repr(line)[2:-1]
    if newtext != oldtext:
        print "NOTE: Replace %s: %s" % (wikipedia.mylang, inname)
        if forreal:
            if ask:
                if confirm:
                    if bell:
                        sys.stdout.write('\07')
                    autonomous_problem(inpl, 'removing: %s'%(",".join(removing)))
                    answer = raw_input('submit y/n ?')
                else:
                    answer = 'y'
            else:
                answer = 'y'
            if answer == 'y':
                status, reason, data = wikipedia.putPage(wikipedia.mylang, inname, newtext,
                                                         comment='robot '+mods)
                if str(status) != '302':
                    print status, reason
            else:
                backlink = False

if backlink:
    for code in new.keys():
        pl = new[code]
        if not unequal.bigger(inpl,pl):
            shouldlink = new.values() + [inpl]
            linked = pl.interwiki()
            for xpl in shouldlink:
                if xpl != pl and not xpl in linked:
                    for l in linked:
                        if l.code() == xpl.code():
                            print "WARNING:", pl.asasciiselflink(), "does not link to", xpl.asasciilink(), "but to", l.asasciilink()
                            break
                    else:
                        print "WARNING:", pl.asasciiselflink(), "does not link to", xpl.asasciilink()
            # Check for superfluous links
            for xpl in linked:
                if not xpl in shouldlink:
                    # Check whether there is an alternative page on that language.
                    for l in shouldlink:
                        if l.code() == xpl.code():
                            # Already reported above.
                            break
                    else:
                        # New warning
                        print "WARNING:", pl.asasciiselflink(), "links to incorrect", xpl.asasciilink()
