# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The Wikimedia Incubator family

class Family(family.Family):
    
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'incubator'
        self.langs = {
            'incubator': 'incubator.wikimedia.org',
        }
        
        self.namespaces[4] = {
            '_default': [u'Incubator', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Incubator talk', self.namespaces[5]['_default']],
        }

    def version(self, code):
        return "1.11alpha"

