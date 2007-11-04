# -*- coding: utf-8  -*-
"""
Interface functions to Mediawiki's api.php
"""
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import urllib
import http


class API:

    def __init__(self, site):
        self.site = site

    def query(prop, **kwargs):
        params = dict(kwargs)
        params['action'] = 'query'
        if not params.has_key('format'): #Most probably, we want the XML format
            params['format'] = 'xml'
        address = '/w/api.php?' + urllib.urlencode(params)

        return http.HTTP(None).GET(address) #TODO: Use site's HTTP object instead
