# -*- coding: utf-8  -*-

import config, urllib

# Parent class for all wiki families

class Family(object):
    # Note that if mylang is 'commons', it is automatically added.
    langs = {}
        
    # Translation used on all Wikipedias for the different namespaces.
    # (Please sort languages alphabetically)
    # You only need to enter translations that differ from _default.
    namespaces = {
        -2: {
            '_default': u'Media',
        },
        -1: {
            '_default': u'Special',
            'af': u'Spesiaal',
            'ar': u'خاص',
            'bg': u'Специални',
            'bn': u'বিশেষ',
            'ca': u'Especial',
            'cs': u'Speciální',
            'csb': u'Specjalnô',
            'cy': u'Arbennig',
            'da': u'Speciel',
            'de': u'Spezial',
            'eo': u'Speciala',
            'es': u'Especial',
            'et': u'Eri',
            'fa': u'ویژه',
            'fi': u'Toiminnot',
            'fy': u'Wiki',
            'ga': u'Speisialta',
            'he': u'מיוחד',
            'hi': u'विशेष',
            'hu': u'Speciális',
            'id': u'Istimewa',
            'it': u'Speciale',
            'ja': u'特別',
            'ko': u'특수기능',
            'la': u'Specialis',
            'ms': u'Istimewa',
            'nb': u'Spesial',
            'nl': u'Speciaal',
            'no': u'Spesial',
            'oc': u'Especial',
            'pl': u'Specjalna',
            'pt': u'Especial',
            'ru': u'Специальные',
            'sk': u'Špeciálne',
            'sl': u'Posebno',
            'sq': u'Speciale',
            'sr': u'Посебно',
            'uk': u'Спеціальні',
            'ta': u'சிறப்பு',
            'th': u'พิเศษ',
            'wa': u'Sipeciås',
        },
        0: {
            '_default': None,
        },
        1: {
            '_default': 'Talk',
            'de': u'Diskussion',
            'nl': u'Overleg',
        },
        2: {
            '_default': u'User',
            'de': u'Benutzer',
            'nl': u'Gebruiker',
        },
        3: {
            '_default': u'User talk',
            'de': u'Benutzer Diskussion',
        },
        4: {
            '_default': u'Wikipedia',
        },
        5: {
            '_default': u'Wikipedia talk',
            'de': u'Wikipedia Diskussion',
        },
        6: {
            # TODO: convert all percent-encoded titles to plaintext
            '_default': u'Image',
            'af': u'Beeld',
            'ar': u'صورة',
            'bg': u'Картинка',
            #'bn': To be checked,
            'ca': u'Imatge',
            'cs': u'Soubor',
            'csb': u'Òbrôzk',
            'cy': u'Delwedd',
            'da': u'Billede',
            'de': u'Bild',
            'eo': u'Dosiero',
            'es': u'Imagen',
            'et': u'Pilt',
            'fa': u'تصویر',
            'fi': u'Kuva',
            'fr': u'Image',
            'fy': u'Ofbyld',
            'ga': u'Íomhá',
            'he': u'תמונה',
            'hi': u'चित्र',
            'hu': u'Kép',
            'ia': u'Imagine',
            'id': u'Imej',
            'it': u'Immagine',
            'ja': u'画像',
            'ko': u'그림',
            'la': u'Imago',
            'ms': u'Imej',
            'nb': u'Bilde',
            'nl': u'Afbeelding',
            'no': u'Bilde',
            'oc': u'Image',
            'pl': u'Grafika',
            'pt': u'Imagem',
            'ro': u'Imagine',
            'ru': u'Изображение',
            'sk': u'Obrázok',
            'sl': u'Slika',
            'sq': u'Figura',
            'sr': u'Слика',
            'sv': u'Bild',
            'ta': u'படிமம்',
            'th': u'ภาพ',
            'wa': u'Imådje',
        },
        7: {
            '_default': u'Image talk',
            'de': u'Bild Diskussion',        
        },
        8: {
            '_default': u'MediaWiki',
            'bg': u'МедияУики',
        },
        9: {
            '_default': u'MediaWiki talk',
            'de': u'MediaWiki Diskussion',
        },
        10: {
            '_default':u'Template',
            'de':u'Vorlage',
            'es':u'Plantilla',
            'nl':u'Sjabloon'
        },
        11: {
            '_default': u'Template talk',
            'de': u'Vorlage Diskussion',
        },
        12: {
            '_default': u'Help',
            'de': u'Hilfe',
        },
        13: {
            '_default': u'Help talk',
            'de': u'Hilfe Diskussion',
        },
        14: {
            '_default': u'Category',
            'bg': u'Категория',
            'ca': u'Categoria',
            'cs': u'Kategorie',
            'da': u'Kategori',
            'de': u'Kategorie',
            'eo': u'Kategorio',
            'es': u'Categoría',
            'fr': u'Catégorie',
            'hu': u'Kategória',
            'is': u'Flokkur',
            'it': u'Categoria',
            'nl': u'Categorie',
            'no': u'Kategori',
            'pl': u'Kategoria',
            'pt': u'Categoria',
            'sv': u'Kategori',
            'tlh':u'Segh',
            'tt': u'Törkem',
            'wa': u'Categoreye',
            },

        
        15: {
            '_default': u'Category talk',
            'bg'  :     u'Категория беседа',
            'ca'  :     u'Categoria Discussió',
            'cs'  :     u'Kategorie diskuse',
            'de'  :     u'Kategorie Diskussion',
            'eo'  :     u'Kategoria diskuto',
            'es'  :     u'Categoría Discusión',
            'fr'  :     u'Discussion Catégorie',
            'hu'  :     u'Kategória vita',
            'is'  :     u'Flokkaspjall',
            'it'  :     u'Discussioni categoria',
            'nl'  :     u'Overleg categorie',
            'no'  :     u'Kategoridiskusjon',
            'pl'  :     u'Dyskusja kategorii',
            'pt'  :     u'Categoria Discussão',
            'sv'  :     u'Kategoridiskussion',
            'tlh' :     u'Segh ja\'chuq',
            'tt'  :     u'Törkem bäxäse',
            'wa'  :     u'Categoreye copene',
        },
    }

    def _addlang(self, code, location, namespaces = {}):
        """Add a new language to the langs and namespaces of the family.
           This is supposed to be called in the constructor of the family."""
        self.langs[code] = location
        
        for num, val in namespaces.items():
            self.namespaces[num][code]=val
        
    def namespace(self, code, namespace_number, fallback = '_default'):
        if self.namespaces[namespace_number].has_key(code):
            return self.namespaces[namespace_number][code]
        elif fallback:
            return self.namespaces[namespace_number][fallback]
        else:
            raise KeyError('ERROR: title for namespace %d in language %s unknown' % (namespace_number, code))  
    
    # Returns the title of the special namespace in language 'code', taken from
    # dictionary above.
    # If the dictionary doesn't contain a translation, it will use language
    # 'fallback' (or, if fallback isn't given, MediaWiki default).
    # If you want the bot to crash in case of an unknown namespace name, use
    # fallback = None.
    def special_namespace(self, code, fallback = '_default'):
        return self.namespace(code, -1, fallback)
    
    def special_namespace_url(self, code, fallback = '_default'):
        encoded_title = self.namespace(code, -1, fallback).encode(self.code2encoding(code))
        return urllib.quote(encoded_title)
    
    def image_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 6, fallback)
    
    def image_namespace_url(self, code, fallback = '_default'):
        encoded_title = self.namespace(code, 6, fallback).encode(self.code2encoding(code))
        return urllib.quote(encoded_title)
    
    def mediawiki_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 8, fallback)
    
    def template_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 10, fallback)
     
    def category_namespace(self, code, fallback = '_default'):
        return self.namespace(code, 14, fallback)
    
    def category_namespaces(self, code):
        namespaces = []
        namespace_title = self.namespace(code, 14)
        namespaces.append(namespace_title)
        namespaces.append(namespace_title.lower())
        default_namespace_title = self.namespace('_default', 14)
        if namespace_title != default_namespace_title:
            namespaces.append(default_namespace_title)
            namespaces.append(default_namespace_title.lower())
        return namespaces

    # Redirect code can be translated, but is only in one language now.

    redirect = {}

    # On most Wikipedias page names must start with a capital letter, but some
    # languages don't use this.

    nocapitalize = []

    # Which languages have a special order for putting interlanguage links,
    # and what order is it? If a language is not in interwiki_putfirst,
    # alphabetical order on language code is used. For languages that are in
    # interwiki_putfirst, interwiki_putfirst is checked first, and
    # languages are put in the order given there. All other languages are put
    # after those, in code-alphabetical order.

    interwiki_putfirst = {}

    # Which languages do no longer exist and should trigger a warning?
    obsolete = []

    # A few selected big languages for things that we do not want to loop over
    # all languages. This is only needed by the titletranslate.py module, so
    # if you carefully avoid the options, you could get away without these
    # for another wikimedia family.

    biglangs = []

    biglangs2 = biglangs + []

    biglangs3 = biglangs2 + []

    biglangs4 = biglangs3 + []

    seriouslangs = biglangs4 + []

    # other groups of language that we might want to do at once

    # languages in Cyrillic
    cyrilliclangs = []

    # Methods
    
    def hostname(self, code):
        return self.langs[code]

    # Which version of MediaWiki is used?

    def version(self, code):
        return "1.3"

    def put_address(self, code, name):
        return '/w/wiki.phtml?title=%s&action=submit'%name

    def get_address(self, code, name):
        return '/w/wiki.phtml?title='+name+"&redirect=no"

    def references_address(self, code, name):
        return "/w/wiki.phtml?title=%s:Whatlinkshere&target=%s&limit=%d" % (self.special_namespace_url(code), name, config.special_page_limit)

    def upload_address(self, code):
        return '/wiki/%s:Upload'%self.special_namespace_url(code)

    def maintenance_address(self, code, maintenance_page, default_limit = True):
        if default_limit:
            return ('/w/wiki.phtml?title=%s:Maintenance&subfunction=' %
                    self.special_namespace_url(code)) + maintenance_page
        else:
            return ('/w/wiki.phtml?title=%s:Maintenance&subfunction=' %
                    self.special_namespace_url(code)) + maintenance_page + '&limit=' + str(config.special_page_limit)

    def allmessages_address(self, code):
        return ("/w/wiki.phtml?title=%s:Allmessages&ot=html" %
                self.special_namespace_url(code))

    def login_address(self, code):
        return ('/w/wiki.phtml?title=%s:Userlogin&amp;action=submit' %
                self.special_namespace_url(code))

    def move_address(self, code):
        return ('/w/wiki.phtml?title=%s:Movepage&action=submit' %
                self.special_namespace_url(code))

    def delete_address(self, code, name):
        return '/w/wiki.phtml?title=%s&action=delete' % name

    def export_address(self, code):
        return '/wiki/%s:Export' % self.special_namespace_url(code)

    def allpagesname(self, code, start):
        # This is very ugly: to get all pages, the wikipedia code
        # 'fakes' getting a page with the returned name.
        # This will need to be fixed someday.
        if self.version(code)=="1.2":
            return '%s:Allpages&printable=yes&from=%s' % (
                self.special_namespace_url(code), start)
        else:
            return '%s:Allpages&from=%s' % (
                self.special_namespace_url(code), start)

    def code2encoding(self, code):
        """Return the encoding for a specific language wikipedia"""
        return 'utf-8'

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wikipedia"""
        return self.code2encoding(code),

    def __cmp__(self, otherfamily):
        try:
            return cmp(self.name, otherfamily.name)
        except AttributeError:
            return cmp(id(self), id(otherfamily))
