# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wiktionary

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wiktionary'

        self.languages_by_size = [
            'en', 'fr', 'zh', 'lt', 'mg', 'tr', 'ru', 'vi', 'pl', 'ta', 'io',
            'ko', 'pt', 'fi', 'hu', 'el', 'de', 'no', 'sv', 'it', 'nl', 'my',
            'kn', 'li', 'et', 'lo', 'ml', 'ja', 'es', 'ku', 'ar', 'ro', 'te',
            'id', 'gl', 'ca', 'uk', 'bg', 'vo', 'fa', 'is', 'cs', 'hr', 'scn',
            'simple', 'sr', 'oc', 'th', 'af', 'fy', 'sw', 'br', 'he', 'la',
            'sq', 'sl', 'hy', 'eo', 'tt', 'cy', 'zh-min-nan', 'da', 'wa', 'ne',
            'lv', 'tk', 'ast', 'ur', 'ka', 'hsb', 'eu', 'kk', 'ky', 'az', 'wo',
            'ang', 'hi', 'co', 'ga', 'mr', 'gn', 'ia', 'be', 'sk', 'tl', 'ms',
            'csb', 'st', 'nn', 'nds', 'kl', 'sd', 'km', 'ps', 'ug', 'sh', 'ti',
            'mk', 'si', 'bn', 'an', 'zu', 'gu', 'lb', 'ss', 'qu', 'ts', 'bs',
            'fo', 'am', 'rw', 'chr', 'om', 'su', 'kw', 'gv', 'iu', 'mn', 'nah',
            'ie', 'yi', 'tg', 'pa', 'za', 'mt', 'gd', 'tpi', 'dv', 'ik', 'mi',
            'sg', 'so', 'roa-rup', 'uz', 'ln', 'jv', 'sm', 'ha', 'ay', 'sa',
            'na', 'jbo', 'ks', 'fj', 'tn', 'dz', 'als',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wiktionary.org' % lang


        # CentralAuth cross avaliable projects.
        self.cross_projects = [
            'wikipedia', 'wikibooks', 'wikiquote', 'wikisource', 'wikinews', 'wikiversity',
            'meta', 'mediawiki', 'test', 'incubator', 'commons', 'species'
        ]
        # Global bot allowed languages on
        # http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ang', 'ast', 'az', 'bg', 'bn', 'da', 'eo', 'es', 'fa', 'fy', 'ga',
            'gd', 'hu', 'ia', 'ie', 'ik', 'jv', 'ka', 'li', 'lt', 'mk', 'nl',
            'no', 'oc', 'pt', 'sk', 'tg', 'th', 'ti', 'ts', 'ug', 'uk', 'vo',
            'za', 'zh-min-nan', 'zh', 'zu', 
        ]

        # Other than most Wikipedias, page names must not start with a capital
        # letter on ALL Wiktionaries.
        self.nocapitalize = self.langs.keys()

        self.alphabetic_roman = [
            'aa', 'af', 'ak', 'als', 'an', 'roa-rup', 'ast', 'gn', 'ay', 'az',
            'id', 'ms', 'bm', 'zh-min-nan', 'jv', 'su', 'mt', 'bi', 'bo', 'bs',
            'br', 'ca', 'cs', 'ch', 'sn', 'co', 'za', 'cy', 'da', 'de', 'na',
            'mh', 'et', 'ang', 'en', 'es', 'eo', 'eu', 'to', 'fr', 'fy', 'fo',
            'ga', 'gv', 'sm', 'gd', 'gl', 'hr', 'io', 'ia', 'ie', 'ik', 'xh',
            'is', 'zu', 'it', 'kl', 'csb', 'kw', 'rw', 'rn', 'sw', 'ky', 'ku',
            'la', 'lv', 'lb', 'lt', 'li', 'ln', 'jbo', 'hu', 'mg', 'mi', 'mo',
            'my', 'fj', 'nah', 'nl', 'cr', 'no', 'nn', 'hsb', 'oc', 'om', 'ug',
            'uz', 'nds', 'pl', 'pt', 'ro', 'rm', 'qu', 'sg', 'sc', 'st', 'tn',
            'sq', 'scn', 'simple', 'ss', 'sk', 'sl', 'so', 'sh', 'fi', 'sv',
            'tl', 'tt', 'vi', 'tpi', 'tr', 'tw', 'vo', 'wa', 'wo', 'ts', 'yo',
            'el', 'av', 'ab', 'ba', 'be', 'bg', 'mk', 'mn', 'ru', 'sr', 'tg',
            'uk', 'kk', 'hy', 'yi', 'he', 'ur', 'ar', 'tk', 'sd', 'fa', 'ha',
            'ps', 'dv', 'ks', 'ne', 'pi', 'bh', 'mr', 'sa', 'hi', 'as', 'bn',
            'pa', 'gu', 'or', 'ta', 'te', 'kn', 'ml', 'si', 'th', 'lo', 'dz',
            'ka', 'ti', 'am', 'chr', 'iu', 'km', 'zh', 'ja', 'ko',
           ]


        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        self.interwiki_putfirst = {
            'da': self.alphabetic,
            'en': self.alphabetic,
            'et': self.alphabetic,
            'fi': self.alphabetic,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'ms': self.alphabetic_revised,
            'pl': self.alphabetic,
            'sv': self.alphabetic_roman,
            'simple': self.alphabetic,
        }

        self.obsolete = {
            'aa': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wiktionary
            'ab': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Abkhaz_Wiktionary
            'ak': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wiktionary
            'as': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Assamese_Wiktionary
            'av': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Avar_Wiktionary
            'ba': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bashkir_Wiktionary
            'bh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bihari_Wiktionary
            'bi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bislama_Wiktionary
            'bm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wiktionary
            'bo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tibetan_Wiktionary
            'ch': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Chamorro_Wiktionary
            'cr': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wiktionary
            'dk': 'da',
            'jp': 'ja',
            'mh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wiktionary
            'mo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wiktionary
            'minnan':'zh-min-nan',
            'nb': 'no',
            'or': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Oriya_Wiktionary
            'pi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Pali_Bhasa_Wiktionary
            'rm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rhaetian_Wiktionary
            'rn': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kirundi_Wiktionary
            'sc': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sardinian_Wiktionary
            'sn': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Shona_Wiktionary
            'to': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tongan_Wiktionary
            'tlh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Klingon_Wiktionary
            'tw': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Twi_Wiktionary
            'tokipona': None,
            'xh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Xhosa_Wiktionary
            'yo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yoruba_Wiktionary
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.interwiki_on_one_line = ['pl']

        self.interwiki_attop = ['pl']

    def version(self, code):
        return '1.16wmf4'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
