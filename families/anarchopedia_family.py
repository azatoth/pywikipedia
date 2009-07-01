# -*- coding: utf-8  -*-
import family

# The Anarchopedia family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'anarchopedia'

        interface_lang = {
            'ara': 'ar',
            'bos': 'sr',
            'dan': 'da',
            'deu': 'de',
            'dut': 'nl',
            'ell': 'el',
            'eng': 'en',
            'epo': 'en',
            'fas': 'fa',
            'fin': 'fi',
            'fra': 'fr',
            'heb': 'he',
            'hrv': 'sr',
            'hye': 'hy',
            'ind': 'id',
            'ita': 'it',
            'jpn': 'ja',
            'kor': 'ko',
            'lav': 'lv',
            'lit': 'lit',
            'nor': 'no',
            'nsh': 'sr',
            'pol': 'pl',
            'por': 'pt',
            'rum': 'ro',
            'rus': 'ru',
            'spa': 'es',
            'sqi': 'sq',
            'srp': 'sr',
            'swe': 'sv',
            'tur': 'tr',
            'zho': 'zh',
        }

        for lang in interface_lang.values():
            self.langs[lang] = '%s.anarchopedia.org' % lang

        copy = [-2, -1, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        for code, interface in interface_lang.items():
            for ns in copy:
                if self.namespaces[ns].has_key(interface):
                    self.namespaces[ns][code] = self.namespaces[ns][interface]

        self.namespaces[1]['fr'] = u'Discuter'

        self.namespaces[3]['fr'] = u'Discussion Utilisateur'

        self.namespaces[4] = {
            '_default': u'Anarchopedia',
            'ar': u'أنارشوبيديا',
            'el': u'Αναρχοπαίδεια',
            'eo': u'Anarĥopedio',
            'es': u'Anarcopedia',
            'fa': u'آنارکوپديا',
            'he': u'אנרכופדיה',
            'hy': u'Անարխոպեդիա',
            'it': u'Anarcopedia',
            'ja': u'アナーキォペディア',
            'ko': u'아나코백과',
            'lv': u'Anarkopēdija',
            'pt': u'Anarcopédia',
            'ro': u'Anarhopedia',
            'ru': u'Анархопедия',
            'sq': u'Anarshipedia',
            'sr': u'Anarhopedija / Анархопедија',
            'tr': u'Anarşipedi',
            'zh': u'安那其百科',
        }
        self.namespaces[5] = {
            '_default': u'Anarchopedia talk',
            'ar': u'نقاش أنارشوبيديا',
            'bs': u'Разговор о Anarchopedia',
            'da': u'Anarchopedia-diskussion',
            'de': u'Anarchopedia Diskussion',
            'el': u'Αναρχοπαίδεια συζήτηση',
            'es': u'Anarcopedia Discusión',
            'fa': u'بحث آنارکوپديا',
            'fi': u'Keskustelu Anarchopediasta',
            'fr': u'Discussion Anarchopedia',
            'he': u'שיחת אנרכופדיה',
            'hy': u'Անարխոպեդիայի քննարկում',
            'id': u'Pembicaraan Anarchopedia',
            'it': u'Discussioni Anarcopedia',
            'ja': u'アナーキォペディア‐ノート',
            'ko': u'아나코백과토론',
            'lv': u'Anarkopēdija diskusija',
            'nl': u'Overleg Anarchopedia',
            'no': u'Anarchopedia-diskusjon',
            'or': u'Anarchopedia-diskusjon',
            'pl': u'Dyskusja Anarchopedia',
            'pt': u'Anarcopédia Discussão',
            'ro': u'Discuţie Anarhopedia',
            'ru': u'Обсуждение Анархопедии',
            'sh': u'Разговор о Anarhopedija / Анархопедија',
            'sq': u'Anarshipedia diskutim',
            'sr': u'Разговор о Anarhopedija / Анархопедија',
            'sv': u'Anarchopediadiskussion',
            'tr': u'Anarşipedi tartışma',
            'zh': u'安那其百科 talk',
        }

        self.namespaces[6]['tr'] = u'Resim'
        self.namespaces[6]['da'] = u'Billede'
        self.namespaces[6]['sq'] = u'Figura'

        self.namespaces[7]['da'] = u'Billeddiskussion'
        self.namespaces[7]['fr'] = u'Discussion Fichier'
        self.namespaces[7]['sq'] = u'Figura diskutim'
        self.namespaces[7]['tr'] = u'Resim tartışma'


        self.namespaces[11]['fr'] = u'Discussion Modèle'

        self.namespaces[13]['fr'] = u'Discussion Aide'

        self.namespaces[14]['sq'] = u'Kategori'

        self.namespaces[15]['fr'] = u'Discussion Catégorie'
        self.namespaces[15]['sq'] = u'Kategori Diskutim'



        self.nocapitalize = self.langs.keys()

        self.obsolete = {
            'ara': 'ar',
            'bos': 'bs',
            'zho': 'zh',
            'dan': 'da',
            'deu': 'de',
            'dut': 'nl',
            'ell': 'el',
            'eng': 'en',
            'epo': 'eo',
            'fas': 'fa',
            'fra': 'fr',
            'fin': 'fi',
            'heb': 'he',
            'ind': 'id',
            'ita': 'it',
            'jpn': 'ja',
            'lit': 'lt',
            'lav': 'lv',
            'nor': 'no',
            'nsh': 'sh',
            'pol': 'pl',
            'por': 'pt',
            'rum': 'ro',
            'rus': 'ru',
            'spa': 'es',
            'srp': 'sr',
            'srp': 'hr',
            'swe': 'sv',
            'kor': 'ko',
            'sqi': 'sq',
            'hye': 'hy',
            'tur': 'tr',

            'ell': 'gre',
            'srp': 'hrv',
            'nno': None,
            'nob': None,
        }

    def version(self, code):
        return "1.14alpha"

    def scriptpath(self, code):
        return ''

    def path(self, code):
        return '%s/index.php' % self.scriptpath(code)

    def apipath(self, code):
        return '%s/api.php' % self.scriptpath(code)
