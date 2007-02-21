# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The project wiki of Freeciv, an open source strategy game.

class Family(family.Family):
    
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'freeciv'
        self.langs = {
            'da': 'da.freeciv.wikia.com',
            'de': 'de.freeciv.wikia.com',
            'en': 'freeciv.wikia.com',
            'es': 'es.freeciv.wikia.com',
            'fi': 'fi.freeciv.wikia.com',
            'fr': 'fr.freeciv.wikia.com',
        }

        self.namespaces[4] = {
            '_default': [
                u'Freeciv',
                self.namespaces[4]['_default']
            ],
            'fi': u'FreeCiv wiki Suomalaisille',
        }

        self.namespaces[5] = {
            '_default': [
                lambda code: self._talkNamespace(code, 4),
                lambda code: self._talkNamespace('_default', 4),
                self.namespaces[5]['_default']
            ],
            'fi': u'Keskustelu FreeCiv wiki Suomalaisillesta',
        }

        self.namespaces[8]['fi'] = u'MediaWiki'

        self.namespaces[9]['da'] = u'MediaWiki diskussion'
        self.namespaces[9]['fi'] = u'MediaWiki talk'

        self.namespaces[110] = {
            '_default': u'Forum',
        }

        self.namespaces[111] = {
            '_default': u'Forum talk',
        }

        self.talkNamespacePattern['da'] = lambda ns: u'%s diskussion' % ns


    def path(self, code):
        return '/index.php'

    def version(self, code):
        return "1.9.2"
