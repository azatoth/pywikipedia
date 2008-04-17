# -*- coding: utf-8  -*-
"""
The initialization file for the Pywikibot framework.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

import logging
logging.getLogger().setLevel(logging.DEBUG)

from exceptions import *

import config

_sites = {}
default_family = config.family
default_code = config.mylang

def Site(code=None, fam=None, user=None, interface=None):
    """Return the specified Site object.

    Returns a cached object if possible, otherwise instantiates a new one.

    @param code: language code
    @type code: string
    @param fam: family name or object
    @type fam: string or Family
    @param user: bot user name to use on this site
    @type user: unicode

    """
    if code == None:
        code = default_code
    if fam == None:
        fam = default_family
    if user == None:
        try:
            user = config.usernames[fam][code]
        except KeyError:
            user = None
    if interface is None:
        interface = config.site_interface
    try:
        exec "from site import %s as __Site" % interface
    except ImportError:
        raise ValueError("Invalid interface name '%s'" % interface)
    key = '%s:%s:%s' % (fam, code, user)
    if not _sites.has_key(key):
        _sites[key] = __Site(code=code, fam=fam, user=user)
        _sites[key].getsiteinfo()
        try:
            _sites[key].login(False)
        except NoUsername:
            pass
    return _sites[key]

getSite = Site # alias for backwards-compability

from page import Page, ImagePage, Category

##def Page(*args, **kwargs):
##    from page import Page as _Page
##    return _Page(*args, **kwargs)
##
##def ImagePage(*args, **kwargs):
##    from page import ImagePage as _ImagePage
##    return _ImagePage(*args, **kwargs)
##
##def Category(*args, **kwargs):
##    from page import Category as _Category
##    return _Category(*args, **kwargs)

# DEBUG

def output(text):
    print text

def input(prompt, password=False):
    if password:
        import getpass
        return getpass.getpass(prompt)
    return raw_input(prompt)

def stopme():
    """Drop this process from the throttle log.

    Can be called manually if desired, but if not, will be called automatically
    at Python exit.

    """
    # only need one drop() call because all throttles use the same global pid
    try:
        _sites[_sites.keys()[0]].throttle.drop()
        logging.info("Dropped throttle(s).")
    except IndexError:
        pass

import atexit
atexit.register(stopme)

