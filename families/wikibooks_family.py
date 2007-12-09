# -*- coding: utf-8  -*-
import urllib
import family, config

__version__ = '$Id$'

# The wikimedia family that is known as Wikibooks

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikibooks'

        self.langs = {
            'dk':'da.wikibooks.org',
            'jp':'ja.wikibooks.org',
            'minnan':'zh-min-nan.wikibooks.org',
            'nb':'no.wikibooks.org',
            'zh-cn':'zh.wikibooks.org',
            'zh-tw':'zh.wikibooks.org'
            }

        for lang in self.knownlanguages:
            self.langs[lang] = '%s.wikibooks.org' % lang

        # Override defaults
        self.namespaces[2]['pl'] = u'Wikipedysta'
        self.namespaces[3]['pl'] = u'Dyskusja Wikipedysty'

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikibooks', self.namespaces[4]['_default']],
            'ar': u'ويكي الكتب',
            'bg': u'Уикикниги',
            'bs': u'Wikiknjige',
            'ca': u'Viquillibres',
            'cs': u'Wikiknihy',
            'cy': u'Wicillyfrau',
            'el': u'Βικιβιβλία',
            'eo': u'Vikilibroj',
            'es': u'Wikilibros',
            'fa': u'ویکی‌نسک',
            'fi': u'Wikikirjasto',
            'fr': u'Wikilivres',
            'ga': u'Vicíleabhair',
            'he': u'ויקיספר',
            'hr': u'Wikiknjige',
            'hu': u'Wikikönyvek',
            'is': u'Wikibækur',
            'ka': u'ვიკიწიგნები',
            'kk': u'Уикикітап',
            'ko': u'위키책',
            'la': u'Vicilibri',
            'ml': u'വിക്കി പുസ്തകശാല',
            'no': u'Wikibøker',
            'oc': u'Wikilibres',
            'ru': u'Викиучебник',
            'sl': u'Wikiknjige',
            'sr': u'Викикњиге',
            'tr': u'Vikikitap',
            'ur': u'وکی کتب',
            'uz': u'Vikikitob',
        }

        self.namespaces[5] = {
            '_default': [u'Wikibooks talk', self.namespaces[5]['_default']],
            'af': u'Wikibooksbespreking',
            'als': u'Wikibooks Diskussion',
            'ar': u'نقاش ويكي الكتب',
            'ast': u'Wikibooks discusión',
            'ay': u'Wikibooks Discusión',
            'az': u'Wikibooks müzakirəsi',
            'ba': u'Wikibooks б-са фекер алышыу',
            'be': u'Wikibooks размовы',
            'bg': u'Уикикниги беседа',
            'bm': u'Discussion Wikibooks',
            'bn': u'Wikibooks আলাপ',
            'bs': u'Razgovor s Wikiknjigama',
            'ca': u'Viquillibres Discussió',
            'cs': u'Wikiknihy diskuse',
            'cv': u'Wikibooks сӳтсе явмалли',
            'cy': u'Sgwrs Wicillyfrau',
            'da': u'Wikibooks-diskussion',
            'de': u'Wikibooks Diskussion',
            'el': u'Βικιβιβλία συζήτηση',
            'eo': u'Vikilibroj diskuto',
            'es': u'Wikilibros Discusión',
            'et': u'Wikibooks arutelu',
            'eu': u'Wikibooks eztabaida',
            'fa': u'بحث ویکی‌نسک',
            'fi': u'Keskustelu Wikikirjastosta',
            'fr': u'Discussion Wikilivres',
            'fy': u'Wikibooks oerlis',
            'ga': u'Plé Vicíleabhar',
            'gl': u'Conversa Wikibooks',
            'gn': u'Wikibooks Discusión',
            'he': u'שיחת ויקיספר',
            'hi': u'Wikibooks वार्ता',
            'hr': u'Razgovor Wikiknjige',
            'hu': u'Wikikönyvek vita',
            'hy': u'Wikibooks քննարկում',
            'ia': u'Discussion Wikibooks',
            'id': u'Pembicaraan Wikibooks',
            'is': u'Wikibækurspjall',
            'it': u'Discussioni Wikibooks',
            'ja': u'Wikibooks‐ノート',
            'ka': u'ვიკიწიგნები განხილვა',
            'kk': u'Уикикітап талқылауы',
            'kn': u'Wikibooks ಚರ್ಚೆ',
            'ko': u'위키책토론',
            'ku': u'Wikibooks nîqaş',
            'la': u'Disputatio Vicilibrorum',
            'lb': u'Wikibooks Diskussion',
            'ln': u'Discussion Wikibooks',
            'lt': u'Wikibooks aptarimas',
            'lv': u'Wikibooks diskusija',
            'mk': u'Разговор за Wikibooks',
            'ml': u'വിക്കി പുസ്തകശാല സംവാദം',
            'mr': u'Wikibooks चर्चा',
            'ms': u'Perbincangan Wikibooks',
            'nah': u'Wikibooks Discusión',
            'nds': u'Wikibooks Diskuschoon',
            'nl': u'Overleg Wikibooks',
            'no': u'Wikibøker-diskusjon',
            'oc': u'Discussion Wikilibres',
            'pa': u'Wikibooks ਚਰਚਾ',
            'pl': u'Dyskusja Wikibooks',
            'pt': u'Wikibooks Discussão',
            'qu': u'Wikibooks rimanakuy',
            'ro': u'Discuţie Wikibooks',
            'ru': u'Обсуждение Викиучебника',
            'sa': u'Wikibooksसंभाषणं',
            'sk': u'Diskusia k Wikibooks',
            'sl': u'Pogovor o Wikiknjigah',
            'sq': u'Wikibooks diskutim',
            'sr': u'Разговор о викикњигама',
            'su': u'Obrolan Wikibooks',
            'sv': u'Wikibooksdiskussion',
            'ta': u'Wikibooks பேச்சு',
            'te': u'Wikibooks చర్చ',
            'tg': u'Баҳси Wikibooks',
            'th': u'คุยเรื่องWikibooks',
            'tr': u'Vikikitap tartışma',
            'tt': u'Wikibooks bäxäse',
            'uk': u'Обговорення Wikibooks',
            'ur': u'تبادلۂ خیال وکی کتب',
            'uz': u'Vikikitob munozarasi',
            'vi': u'Thảo luận Wikibooks',
            'vo': u'Bespik dö Wikibooks',
            'wa': u'Wikibooks copene',
        }

        self.namespaces[100] = {
            'id': u'Resep',
            'fr': u'Transwiki',
            'he': u'שער',
            'it': u'Progetto',
            'ms': u'Resipi',
        }

        self.namespaces[101] = {
            'id': u'Pembicaraan Resep',
            'fr': u'Discussion Transwiki',
            'he': u'שיחת שער',
            'it': u'Discussioni progetto',
            'ms': u'Perbualan Resipi',
        }

        self.namespaces[102] = {
            'cy': u'Silff lyfrau',
            'de': u'Regal',
            'en': u'Cookbook',
            'es': u'Wikiversidad',
            'id': u'Wisata',
            'it': u'Ripiano',
            'nl': u'Transwiki',
            'sr': u'Кувар',
        }

        self.namespaces[103] = {
            'cy': u'Sgwrs Silff lyfrau',
            'de': u'Regal Diskussion',
            'en': u'Cookbook talk',
            'es': u'Wikiversidad Discusión',
            'id': u'Pembicaraan Wisata',
            'it': u'Discussioni ripiano',
            'nl': u'Overleg transwiki',
            'sr': u'Разговор о кувару',
        }

        self.namespaces[104] = {
            'he': u'מדף',
            'ka': u'თარო',
            'nl': u'Wikijunior',
        }

        self.namespaces[105] = {
            'he': u'שיחת מדף',
            'ka': u'თარო განხილვა',
            'nl': u'Overleg Wikijunior',
        }

        self.namespaces[108] = {
            'en': u'Transwiki',
        }

        self.namespaces[109] = {
            'en': u'Transwiki talk',
        }

        self.namespaces[110] = {
            'en': u'Wikijunior',
        }

        self.namespaces[111] = {
            'en': u'Wikijunior talk',
        }

        self.namespaces[112] = {
            'en': u'Subject',
        }

        self.namespaces[113] = {
            'en': u'Subject talk',
        }

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        alphabetic = ['af','ar','roa-rup','om','bg','be','bn','bs',
                      'ca','chr','co','cs','cy','da','de','als','et',
                      'el','en','es','eo','eu','fa','fr','fy','ga','gv',
                      'gd','gl','ko','hi','hr','io','id','ia','is','it',
                      'he','jv','ka','csb','ks','sw','la','lv','lt','hu',
                      'mk','mg','ml','mi','mr','ms','zh-cfr','mn','nah','na',
                      'nl','ja','no','nb','oc','nds','pl','pt','ro','ru',
                      'sa','st','sq','si','simple','sk','sl','sr','su',
                      'fi','sv','ta','tt','th','ur','vi',
                      'tpi','tr','uk','vo','yi','yo','za','zh','zh-cn',
                      'zh-tw']

        self.obsolete = {
            'dk': 'da',
            'jp': 'ja',
            'minnan':'zh-min-nan',
            'nb': 'no',
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.interwiki_putfirst = {
            'en': alphabetic,
            'fi': alphabetic,
            'fr': alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': alphabetic,
            'simple': alphabetic
        }

    def version(self, code):
        return "1.11"

    def shared_image_repository(self, code):
        return ('commons', 'commons')
