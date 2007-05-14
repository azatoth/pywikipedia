#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to log the robot in to a wiki account.

Suggestion is to make a special account to use for robot use only. Make
sure this robot account is well known on your home wikipedia before using.

Parameters:

   -pass:XXXX   Uses XXXX as password. Be careful if you use this
                parameter because your password will be shown on your
                screen.
   
   -sysop       Log in with your sysop account.
   
   -all         Try to log in on all sites where a username is defined in
                user-config.py.
                
   -force       When doing -all, ignores if the user is already loged in,
                and tries to login for all listed sites.
                This may be useful if you have changed the account name
                and need to aquire new login cookies.

If not given as parameter, the script will ask for your username and password
(password entry will be hidden), log in to your home wiki using this
combination, and store the resulting cookies (containing your password hash,
so keep it secured!) in a file in the login-data subdirectory.

All bots in this library will be looking for this cookie file and will use the
login information if it is present.

To log out, throw away the XX-login.data file that is created in the login-data
subdirectory.
"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distributed under the terms of the MIT license.
#
__version__='$Id$'

import re, sys, getpass
import httplib, urllib2
import wikipedia, config

# On some wikis you are only allowed to run a bot if there is a link to
# the bot's user page in a specific list.
botList = {
    'wikipedia': {
        'en': u'Wikipedia:Registered bots',
        'simple': u'Wikipedia:Bots',
    },
    'gentoo': {
        'en': u'Help:Bots',
    }
}

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

class LoginManager:
    def __init__(self, password = None, sysop = False, site = None):
        self.site = site or wikipedia.getSite()
        if sysop:
            try:
                self.username = config.sysopnames[self.site.family.name][self.site.lang]
            except:
                raise wikipedia.NoUsername(u'ERROR: Sysop username for %s:%s is undefined.\nIf you have a sysop account for that site, please add such a line to user-config.py:\n\nsysopnames[\'%s\'][\'%s\'] = \'myUsername\'' % (self.site.family.name, self.site.lang, self.site.family.name, self.site.lang))
        else:
            try:
                self.username = config.usernames[self.site.family.name][self.site.lang]
            except:
                raise wikipedia.NoUsername(u'ERROR: Username for %s:%s is undefined.\nIf you have an account for that site, please add such a line to user-config.py:\n\nusernames[\'%s\'][\'%s\'] = \'myUsername\'' % (self.site.family.name, self.site.lang, self.site.family.name, self.site.lang))
        self.password = password

    def botAllowed(self):
        """
        Checks whether the bot is listed on a specific page to comply with
        the policy on the respective wiki.
        """
        if botList.has_key(self.site.family.name) and botList[self.site.family.name].has_key(self.site.language()):
            botListPageTitle = botList[self.site.family.name][self.site.language()]
            botListPage = wikipedia.Page(self.site, botListPageTitle)
            for linkedPage in botListPage.linkedPages():
                if linkedPage.titleWithoutNamespace() == self.username:
                    return True
            return False
        else:
            # No bot policies on other 
            return True
    
    def getCookie(self, remember=True):
        """Login to wikipedia.
    
        remember    Remember login (default: True)
        
        Returns cookie data if succesful, None otherwise."""
    
        predata = {
            "wpName": self.username.encode(self.site.encoding()),
            "wpPassword": self.password,
            "wpLoginattempt": "Aanmelden & Inschrijven", # dutch button label seems to work for all wikis
            "wpRemember": str(int(bool(remember)))
        }
        address = self.site.login_address()

        if self.site.hostname() in config.authenticate.keys():
            headers = {
                "Content-type": "application/x-www-form-urlencoded", 
                "User-agent": wikipedia.useragent
            }
            data = self.site.urlEncode(predata)
            response = urllib2.urlopen(urllib2.Request('http://' + self.site.hostname() + address, data, headers))
            data = response.read()
            wikipedia.cj.save(wikipedia.COOKIEFILE)
            return "Ok"
        else:
            response, data = self.site.postForm(address, predata, useCookie=False)
            n = 0
            Reat=re.compile(': (.*?);')
            L = []

            for eat in response.msg.getallmatchingheaders('set-cookie'):
                m = Reat.search(eat)
                if m:
                    n += 1
                    L.append(m.group(1))
            
            log_data = []
            for Ldata in L:
                if (re.match('.*_session=.*', Ldata)):
                    log_data.append(Ldata)
                elif (re.match('.*UserID=.*', Ldata)):
                    log_data.append(Ldata)
                elif (re.match('.*UserName=.*', Ldata)):
                    log_data.append(Ldata)
                elif (re.match('.*Token=.*', Ldata)):
                    log_data.append(Ldata)
  
            if len(log_data) == 4:
                return "\n".join(L)
            else:
                if '<input type="hidden" name="wpCaptchaId"' in data:
                    wikipedia.output(u'There is a CAPTCHA in the server\'s response.\nPlease wait a while or log in using a graphical web browser to reset the request and try again.')
                return None

    def storecookiedata(self, data):
        """
        Stores cookie data.

        The argument data is the raw data, as returned by getCookie().

        Returns nothing."""
        filename = 'login-data/%s-%s-%s-login.data' % (self.site.family.name, self.site.lang, self.username)
        f = open(makepath(filename), 'w')
        f.write(data)
        f.close()

    def login(self, retry = False):
        if not self.password:
            # As we don't want the password to appear on the screen, we use getpass().
            s = u'Password for user %s on %s: ' % (self.username, self.site)
            self.password = getpass.getpass(s.encode(config.console_encoding))
            # Convert the password from the encoding your shell uses to the one your wiki
            # uses, via Unicode. This is the same as wikipedia.input() does with the 
            # username, but input() uses raw_input() instead of getpass().
            self.password = unicode(self.password, config.console_encoding)

        self.password = self.password.encode(self.site.encoding())

        wikipedia.output(u"Logging in to %s as %s" % (self.site, self.username))
        # Ensure bot policy on the English Wikipedia
        if not self.botAllowed():
            wikipedia.output(u'*** Your username is not listed on [[Wikipedia:Bots]].\n*** Please make sure you are allowed to use the robot before actually using it!')
        cookiedata = self.getCookie()
        if cookiedata:
            self.storecookiedata(cookiedata)
            wikipedia.output(u"Should be logged in now")
            return True
        else:
            wikipedia.output(u"Login failed. Wrong password?")
            if retry:
                self.password = None
                return self.login(retry = True)
            else:
                return False

def main():
    username = password = None
    sysop = False
    logall = False
    forceLogin = False
    for arg in wikipedia.handleArgs():
        if arg.startswith("-pass:"):
            password = arg[6:]
        elif arg == "-sysop":
            sysop = True
        elif arg == "-all":
            logall = True
        elif arg == "-force":
            forceLogin = True
        else:
            wikipedia.showHelp('login')
            sys.exit()
    if logall:
        if sysop:
            namedict = config.sysopnames
        else:
            namedict = config.usernames
        for familyName in namedict.iterkeys():
            for lang in namedict[familyName].iterkeys():
                site = wikipedia.getSite(code=lang, fam=familyName)
                if not forceLogin and site.loggedInAs(sysop = sysop) != None:
                    wikipedia.output(u'Already logged in on %s' % site)
                else:
                    loginMan = LoginManager(password, sysop = sysop, site = site)
                    loginMan.login()
    else:
        loginMan = LoginManager(password, sysop = sysop)
        loginMan.login()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
