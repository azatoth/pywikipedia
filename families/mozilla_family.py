# -*- coding: utf-8  -*-

import family

# The official Mozilla Wiki.

class Family(family.Family):
    name = 'mozilla'
    
    def __init__(self):
        family.Family.__init__(self)
	self.langs = {
            'en': 'wiki.mozilla.org',
	}
	self.namespaces[4] = {
	    '_default': u'MozillaWiki',
	    }
	self.namespaces[5] = {
	    '_default': u'MozillaWiki talk',
	    }
	
    def version(self, code):
        return "1.4.2"
    
    def path(self, code):
        return ''
