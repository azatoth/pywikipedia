# -*- coding: utf-8  -*-
"""
Script to log the robot in to a wikipedia account.

Suggestion is to make a special account to use for robot use only. Make
sure this robot account is well known on your home wikipedia before using.

This script has no command line arguments. Please run it as such. It will ask
for your username and password (it will show your password on the screen!), log
in to your home wikipedia using this combination, and store the resulting
cookies (containing your password in encoded form, so keep it secured!) in a
file named login.data

The wikipedia library will be looking for this file and will use the login
information if it is present.

Arguments:

  -lang:xx Log in to the given wikipedia language
  
To log out, throw away the XX-login.data file that is created in the login-data
subdirectory..
"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distributed under the terms of the PSF license.
#
__version__='$Id$'

import re, sys, getpass
import httplib
import wikipedia, config

def makepath(path):
    """ creates missing directories for the given path and
        returns a normalized absolute version of the path.

    - if the given path already exists in the filesystem
      the filesystem is not modified.

    - otherwise makepath creates directories along the given path
      using the dirname() of the path. You may append
      a '/' to the path if you want it to be a directory path.

    from holger@trillke.net 2002/03/18
    """
    from os import makedirs
    from os.path import normpath,dirname,exists,abspath

    dpath = normpath(dirname(path))
    if not exists(dpath): makedirs(dpath)
    return normpath(abspath(path))


for arg in sys.argv[1:]:
    arg = wikipedia.argHandler(arg)
    if arg:
        print "Unknown argument: ",arg
        sys.exit(1)

mysite = wikipedia.getSite()
wikipedia.output(u"Logging in to %s" % repr(mysite))

username = wikipedia.input(u'username:', encode = True)
# As we don't want the password to appear on the screen, we use getpass(). 
password = getpass.getpass('password: ')
# Convert the password from the encoding your shell uses to the one your wiki
# uses, via Unicode. This is the same as wikipedia.input() does with the 
# username, but input() uses raw_input() instead of getpass().
password = unicode(password, config.console_encoding)
password = password.encode(wikipedia.myencoding())

# Ensure bot policy on the English Wikipedia
ensite=wikipedia.getSite(code='en',fam='wikipedia')
if mysite == ensite:
    pl=wikipedia.PageLink(ensite,'Wikipedia:Bots')
    text=pl.get()
    if not '[[User:%s'%username in text:
        print "Your username is not listed on [[Wikipedia:Bots]]"
        print "Please make sure you are allowed to use the robot"
        print "Before actually using it!"
        
data = wikipedia.urlencode((
            ('wpName', username),
            ('wpPassword', password),
            ('wpLoginattempt', "Aanmelden & Inschrijven"),
            ('wpRemember', '1'),
            ))

headers = {"Content-type": "application/x-www-form-urlencoded", 
           "User-agent": "RobHooftWikiRobot/1.0"}
conn = httplib.HTTPConnection(mysite.hostname())
pagename = mysite.login_address()
conn.request("POST", pagename, data, headers)
response = conn.getresponse()
data = response.read()
conn.close()
#print response.status, response.reason
#print data
#print dir(response)
f=open(makepath('login-data/%s-%s-login.data' % (mysite.family.name, mysite.lang)), 'w')
n=0
msg=response.msg
Reat=re.compile(': (.*?);')
#print repr(msg.getallmatchingheaders('set-cookie'))
for eat in msg.getallmatchingheaders('set-cookie'):
    m=Reat.search(eat)
    if m:
        n=n+1
        f.write(m.group(1)+'\n')
f.close()

if n==4:
    print "Should be logged in now"
else:
    print "Hm. Did something go wrong? Wrong password?"
