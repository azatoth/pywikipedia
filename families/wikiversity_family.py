# -*- coding: utf-8  -*-
import urllib
import family, config

__version__ = '$Id$'

# The wikimedia family that is known as Wikiversity

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiversity'

        self.langs = {
            'beta': 'beta.wikiversity.org',
        }

        for lang in self.knownlanguages:
            if lang not in self.langs:
                self.langs[lang] = lang+'.wikiversity.org'

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikiversity', self.namespaces[4]['_default']],
            'es': u'Wikiversidad',
            'fr': u'Wikiversité',
            'it': u'Wikiversità',
        }
        self.namespaces[5] = {
            '_default': [u'Wikiversity talk', self.namespaces[5]['_default']],
            'de': u'Wikiversity Diskussion',
            'es': u'Wikiversidad Discusión',
            'fr': u'Discussion Wikiversité',
            'it': u'Discussioni Wikiversità',
        }

        self.namespaces[100] = {
            'en': u'School',
            'it': u'Facoltà',
        }
        self.namespaces[101] = {
            'en': u'School talk',
            'it': u'Discussioni facoltà',
        }
        self.namespaces[102] = {
            'en': u'Portal',
            'fr': u'Projet',
            'it': u'Corso',
        }
        self.namespaces[103] = {
            'en': u'Portal talk',
            'fr': u'Discussion Projet',
            'it': u'Discussioni corso',
        }
        self.namespaces[104] = {
            'en': u'Topic',
            'it': u'Materia',
        }
        self.namespaces[105] = {
            'en': u'Topic talk',
            'it': u'Discussioni materia',
        }
        self.namespaces[106] = {
            'de': u'Kurs',
            'fr': u'Faculté',
            'it': u'Dipartimento',
        }
        self.namespaces[107] = {
            'de': u'Kurs Diskussion',
            'fr': u'Discussion Faculté',
            'it': u'Discussioni dipartimento',
        }
        self.namespaces[108] = {
            'de': u'Projekt',
            'fr': u'Département',
        }
        self.namespaces[109] = {
            'de': u'Projekt Diskussion',
            'fr': u'Discussion Département',
        }
        self.namespaces[110] = {
            'fr': u'Transwiki',
        }
        self.namespaces[111] = {
            'fr': u'Discussion Transwiki',
        }

        self.obsolete = {
            'dk': 'da',
            'jp': 'ja',
            'minnan':'zh-min-nan',
            'nb': 'no',
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.mainpages = {
            'de': u'Hauptseite',
            'fr': u'Accueil',
            'it': u'Pagina principale',
        }

    def version(self,code):
        return "1.12alpha"

    def shared_image_repository(self, code):
        return ('commons', 'commons')
