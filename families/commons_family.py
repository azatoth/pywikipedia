# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The Wikimedia Commons family

class Family(family.Family):
    
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'commons'
        self.langs = {
            'commons': 'commons.wikimedia.org',
        }
        
        self.namespaces[4] = {
            '_default': [u'Commons', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Commons talk', self.namespaces[5]['_default']],
        }
        self.namespaces[100] = {
            '_default': [u'Creator', self.namespaces[5]['_default']],
        }
        self.namespaces[101] = {
            '_default': [u'Creator talk', self.namespaces[5]['_default']],
        }

        self.interwiki_forward = 'wikipedia'

    def version(self, code):
        return "1.11alpha"
    
    def shared_image_repository(self):
        return ('commons', 'commons')
