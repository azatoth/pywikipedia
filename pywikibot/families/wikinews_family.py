# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikinews

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikinews'

        self.languages_by_size = [
            'en', 'sr', 'pl', 'it', 'de', 'fr', 'pt', 'es', 'zh', 'sv',
            'ja', 'ru', 'nl', 'he', 'fi', 'ar', 'sd', 'cs', 'no', 'uk',
            'hu', 'ca', 'ro', 'th', 'bs', 'bg', 'ta', 'tr'
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikinews.org' % lang

        self.obsolete = {
            'jp': 'ja',
            'nb': 'no',
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.
        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'pl': self.alphabetic,
        }

        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['cs', 'hu',]

    def code2encoding(self, code):
        return 'utf-8'

    def version(self, code):
        return '1.16alpha-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
