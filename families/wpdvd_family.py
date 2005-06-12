# -*- coding: utf-8  -*-

import urllib
import family, config

# A temporary wiki used to review articles for a DVD version of the German
# Wikipedia

class Family(family.Family):
    
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wpdvd'
        # Known wikipedia languages, given as a dictionary mapping the language code
        # to the hostname of the site hosting that wikipedia. For human consumption,
        # the full name of the language is given behind each line as a comment
        self.langs = {
            'de':'dvd.wikidev.net',   # German, DVD review wiki
            
            'aa':'aa.wikipedia.org',   # Afar
            'ab':'ab.wikipedia.org',   # Abkhazian
            'af':'af.wikipedia.org',   # Afrikaans
            'als':'als.wikipedia.org', # Alsatian
            'am':'am.wikipedia.org',   # Amharic
            'an':'an.wikipedia.org',   # Aragonese
            'ang':'ang.wikipedia.org', # Anglo-Saxon
            'ar':'ar.wikipedia.org',   # Arabic
            'as':'as.wikipedia.org',   # Assamese
            'ast':'ast.wikipedia.org', # Asturian
            'av':'av.wikipedia.org',   # Avar
            'ay':'ay.wikipedia.org',   # Aymara
            'az':'az.wikipedia.org',   # Azerbaijan
            'ba':'ba.wikipedia.org',   # Bashkir
            'be':'be.wikipedia.org',   # Belorussian
            'bg':'bg.wikipedia.org',   # Bulgarian
            'bh':'bh.wikipedia.org',   # Bhojpuri
            'bi':'bi.wikipedia.org',   # Bislama (currently also used by Bitruscan)
            'bn':'bn.wikipedia.org',   # Bengali
            'bo':'bo.wikipedia.org',   # Tibetan
            'br':'br.wikipedia.org',   # Breton
            'bs':'bs.wikipedia.org',   # Bosnian
            'ca':'ca.wikipedia.org',   # Catalan
            'ch':'ch.wikipedia.org',   # Schweizerdeutsch
            'cho':'cho.wikipedia.org', # Choctaw
            'chr':'chr.wikipedia.org', # Cherokee
            'co':'co.wikipedia.org',   # Corsican
            'cr':'cr.wikipedia.org',   # Cree?
            'cs':'cs.wikipedia.org',   # Czech
            'csb':'csb.wikipedia.org', # Kashubian
            'cv':'cv.wikipedia.org',   # Chuvash
            'cy':'cy.wikipedia.org',   # Welsh
            'da':'da.wikipedia.org',   # Danish
            'dk':'da.wikipedia.org',   # Danish (wrong name)
            'dv':'dv.wikipedia.org',   # Dhihevi
            'dz':'dz.wikipedia.org',   # Dzongkha
            'ee':'ee.wikipedia.org',   # Ewe
            'el':'el.wikipedia.org',   # Greek
            'en':'en.wikipedia.org',   # English
            'eo':'eo.wikipedia.org',   # Esperanto
            'es':'es.wikipedia.org',   # Spanish
            'et':'et.wikipedia.org',   # Estonian
            'eu':'eu.wikipedia.org',   # Basque
            'fa':'fa.wikipedia.org',   # Farsi
            'fi':'fi.wikipedia.org',   # Finnish
            'fj':'fj.wikipedia.org',   # Fijian
            'fo':'fo.wikipedia.org',   # Faroese
            'fr':'fr.wikipedia.org',   # French
            'fy':'fy.wikipedia.org',   # Frisian
            'ga':'ga.wikipedia.org',   # Irish Gaelic
            'gd':'gd.wikipedia.org',   # Scottish Gaelic
            'gl':'gl.wikipedia.org',   # Galician
            'gn':'gn.wikipedia.org',   # Guarani
            'got':'got.wikipedia.org', # Gothic
            'gu':'gu.wikipedia.org',   # Gujarati
            'gv':'gv.wikipedia.org',   # Manx
            'ha':'ha.wikipedia.org',   # Hausa
            'haw':'haw.wikipedia.org', # Hawaiian
            'he':'he.wikipedia.org',   # Hebrew
            'hi':'hi.wikipedia.org',   # Hindi
            'hr':'hr.wikipedia.org',   # Croatian
            'ht':'ht.wikipedia.org',   # Haitian
            'hu':'hu.wikipedia.org',   # Hungarian
            'hy':'hy.wikipedia.org',   # Armenian
            'ia':'ia.wikipedia.org',   # Interlingua
            'id':'id.wikipedia.org',   # Indonesian
            'ie':'ie.wikipedia.org',   # Interlingue
            'ik':'ik.wikipedia.org',   # Inupiak
            'io':'io.wikipedia.org',   # Ido
            'is':'is.wikipedia.org',   # Icelandic
            'it':'it.wikipedia.org',   # Italian
            'iu':'iu.wikipedia.org',   # Inuktitut
            'ja':'ja.wikipedia.org',   # Japanese
            'jbo':'jbo.wikipedia.org', # Lojban
            'jp':'ja.wikipedia.org',   # Japanese (incorrect code)
            'jv':'jv.wikipedia.org',   # Javanese
            'ka':'ka.wikipedia.org',   # Georgian
            'kk':'kk.wikipedia.org',   # Kazakh
            'kl':'kl.wikipedia.org',   # Kalaallisut
            'km':'km.wikipedia.org',   # Khmer
            'kn':'kn.wikipedia.org',   # Kannada
            'ko':'ko.wikipedia.org',   # Korean
            'ks':'ks.wikipedia.org',   # Ekspreso, but should become Kashmiri
            'ku':'ku.wikipedia.org',   # Kurdish
            'kw':'kw.wikipedia.org',   # Cornish
            'ky':'ky.wikipedia.org',   # Kirghiz
            'la':'la.wikipedia.org',   # Latin
            'lb':'lb.wikipedia.org',   # Luxembourgish
            'li':'li.wikipedia.org',   # Limburgs
            'ln':'ln.wikipedia.org',   # Lingala
            'lo':'lo.wikipedia.org',   # Lao
            'lt':'lt.wikipedia.org',   # Latvian
            'lv':'lv.wikipedia.org',   # Livonian
            'mg':'mg.wikipedia.org',   # Malagasy
            'mi':'mi.wikipedia.org',   # Maori
            'minnan':'zh-min-nan.wikipedia.org', # Min-Nan
            'zh-min-nan':'zh-min-nan.wikipedia.org', # Min-Nan (old code)
            'mk':'mk.wikipedia.org',   # Macedonian
            'ml':'ml.wikipedia.org',   # Malayalam
            'mn':'mn.wikipedia.org',   # Mongolian
            'mo':'mo.wikipedia.org',   # Moldovan
            'mr':'mr.wikipedia.org',   # Marathi
            'ms':'ms.wikipedia.org',   # Malay
            'mt':'mt.wikipedia.org',   # Maltese
            'mus':'mus.wikipedia.org', # Muscogee
            'my':'my.wikipedia.org',   # Burmese
            'na':'na.wikipedia.org',   # Nauruan
            'nah':'nah.wikipedia.org', # Nahuatl
            'nb':'no.wikipedia.org',   # Norse - new code for Bokmal to distinguish from Nynorsk
            'nds':'nds.wikipedia.org', # Lower Saxon
            'ne':'ne.wikipedia.org',   # Nepalese
            'ng':'ng.wikipedia.org',   # Ndonga
            'nl':'nl.wikipedia.org',   # Dutch
            'nn':'nn.wikipedia.org',   # Norse (nynorsk)
            'no':'no.wikipedia.org',   # Norse (bokmal)
            'nv':'nv.wikipedia.org',   # Navajo
            'ny':'ny.wikipedia.org',   # Chichewa
            'oc':'oc.wikipedia.org',   # Occitan
            'om':'om.wikipedia.org',   # Oromo
            'or':'or.wikipedia.org',   # Oriya
            'pa':'pa.wikipedia.org',   # Punjabi
            'pi':'pi.wikipedia.org',   # Pali
            'pl':'pl.wikipedia.org',   # Polish
            'ps':'ps.wikipedia.org',   # Pashto (Afghan)
            'pt':'pt.wikipedia.org',   # Portuguese
            'qu':'qu.wikipedia.org',   # Quechua
            'rm':'rm.wikipedia.org',   # Romansch
            'rn':'rn.wikipedia.org',   # Kirundi
            'ro':'ro.wikipedia.org',   # Romanian
            'roa-rup':'roa-rup.wikipedia.org', # Aromanian
            'ru':'ru.wikipedia.org',   # Russian
            'rw':'rw.wikipedia.org',   # Kinyarwanda
            'sa':'sa.wikipedia.org',   # Sanskrit
            'sc':'sc.wikipedia.org',   # Sardinian
            'scn':'scn.wikipedia.org', # Sicilian
            'sd':'sd.wikipedia.org',   # Sindhi
            'se':'se.wikipedia.org',   # Saami
            'sg':'sg.wikipedia.org',   # Sango
            'sh':'sh.wikipedia.org',   # OBSOLETE, Serbocroatian
            'si':'si.wikipedia.org',   # Sinhalese
            'simple':'simple.wikipedia.org', # Simple English
            'sk':'sk.wikipedia.org',   # Slovakian
            'sl':'sl.wikipedia.org',   # Slovenian
            'sm':'sm.wikipedia.org',   # Samoan
            'sn':'sn.wikipedia.org',   # Shona
            'so':'so.wikipedia.org',   # Somali
            'sq':'sq.wikipedia.org',   # Albanian
            'sr':'sr.wikipedia.org',   # Serbian
            'ss':'ss.wikipedia.org',   # Swati
            'st':'st.wikipedia.org',   # Sesotho
            'su':'su.wikipedia.org',   # Sundanese
            'sv':'sv.wikipedia.org',   # Swedish
            'sw':'sw.wikipedia.org',   # Swahili
            'ta':'ta.wikipedia.org',   # Tamil
            'te':'te.wikipedia.org',   # Telugu
            'test':'test.wikipedia.org',
            'tg':'tg.wikipedia.org',   # Tajik
            'th':'th.wikipedia.org',   # Thai
            'ti':'ti.wikipedia.org',   # Tigrinya
            'tk':'tk.wikipedia.org',   # Turkmen
            'tl':'tl.wikipedia.org',   # Tagalog
            #'tlh':'tlh.wikipedia.org', # Klingon
            'tn':'tn.wikipedia.org',   # Tswana
            'to':'to.wikipedia.org',   # Tongan
            'tokipona':'tokipona.wikipedia.org', # Toki Pona
            'tpi':'tpi.wikipedia.org', # Tok Pisin
            'tr':'tr.wikipedia.org',   # Turkish
            'ts':'ts.wikipedia.org',   # Tsonga
            'tt':'tt.wikipedia.org',   # Tatar
            'tum':'tum.wikipedia.org', # Tumbuka
            'tw':'tw.wikipedia.org',   # Twi (variety of Akan)
            'ug':'ug.wikipedia.org',   # Uyghur
            'uk':'uk.wikipedia.org',   # Ukrainian
            'ur':'ur.wikipedia.org',   # Urdu
            'uz':'uz.wikipedia.org',   # Uzbek
            've':'ve.wikipedia.org',   # Venda
            'vi':'vi.wikipedia.org',   # Vietnamese
            'vo':'vo.wikipedia.org',   # Volapuk
            'wa':'wa.wikipedia.org',   # Walon
            'wo':'wo.wikipedia.org',   # Wolof
            'xh':'xh.wikipedia.org',   # isiXhosa
            'yi':'yi.wikipedia.org',   # Yiddish
            'yo':'yo.wikipedia.org',   # Yoruba
            'za':'za.wikipedia.org',   # Zhuang
            'zh':'zh.wikipedia.org',   # Chinese
            'zh-cn':'zh.wikipedia.org', # Simplified Chinese
            'zh-tw':'zh.wikipedia.org', # Traditional Chinese
            'zu':'zu.wikipedia.org',   # Zulu
            }

        # Most namespaces are inherited from family.Family.
        self.namespaces[4] = {
            '_default': u'Wikipedia',
        }
        self.namespaces[5] = {
            '_default': u'Wikipedia talk',
            'de': u'Wikipedia Diskussion',
            'pt': u'Wikipedia_Discussão',
            'es': u'Wikipedia Discusión',
        }
        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.
            
        self.nocapitalize = ['tlh','tokipona']
            
        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.
        
        alphabetic = ['aa','af','ar','an','roa-rup','as','ast','ay','az','bg',
                    'be','bn','bh','bi','bo','bs','br','ca','chr','ny','cho','co','cs',
                    'cy','da','de','dv','als','et','el','en','es','eo','eu','ee',
                    'fa','fo','fr','fy','ga','gv','gd','gl','got','gn','gu','ko',
                    'ha','haw','hy','hi','hr','io','id','ia','xh','is','zu','it',
                    'he','jv','kn','ka','csb','ks','kk','kw','km','ky','sw',
                    'ku','lo','la','lv','lt','lb','ln','jbo','hu','mk','mg',
                    'ml','mt','mi','mr','ms','minnan','mn','mus','my','nah','na',
                    'nv','cr','nl','ne','ja','no','nb','nn','oc','om','ug','pi',
                    'ps','nds','pl','pt','pa','ro','rm','qu','ru','se','sa',
                    'st','sq','scn','si','simple','sd','sk','sl','sr','su','fi',
                    'sv','tl','tg','ta','tt','te','th','tlh','tk','tw','vi',
                    'tokipona','tpi','to','tn','tr','ur','uk','uz','vo','wa',
                    'yi','yo','za','zh','zh-cn','zh-tw']
            
        self.interwiki_putfirst = {
            'en': alphabetic,
            'fr': alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': alphabetic,
            'simple': alphabetic,
            'fi': alphabetic
            }
            
        self.obsolete = {'sh':'hr',
                    'dk':'da',
                    'tlh':'none',
                    'zh-min-nan':'minnan',
                    'nb':'no',
                    'jp':'ja',
                    'test':'none',
                    'tokipona':'none',
                    'zh-tw':'zh',
                    'zh-cn':'zh'}
            
        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wikimedia family.
        
        self.biglangs = ['de', 'en', 'es', 'fr', 'it', 'ja', 'nl', 'pl', 'pt', 'sv']
        
        self.biglangs2 = self.biglangs + [
            'ca', 'da', 'eo', 'et', 'fi', 'no', 'ro', 'sl', 'zh']
        
        self.biglangs3 = self.biglangs2 + [
            'af', 'bg', 'cs', 'he', 'hr', 'hu', 'id', 'la', 'ms', 'ru', 'uk', 'wa']
        
        self.biglangs4 = self.biglangs3 + [
            'ast', 'bs', 'cy', 'el', 'eu', 'fy', 'gl', 'ia', 'io', 'is',
            'ko', 'ku', 'lb', 'lt', 'nn', 'simple', 'sk', 'sr', 'tr', 'tt']
        
        self.seriouslangs = self.biglangs4 + [
            'als', 'an', 'ang', 'ar', 'be', 'csb', 'fa', 'fo', 'ga', 'gd',
            'hi', 'ie', 'jv', 'kn', 'ks', 'kw', 'lv', 'mi', 'minnan', 'ml', 'nds',
            'oc', 'sa', 'scn', 'sq', 'su', 'ta', 'th', 'tl', 'ur', 'vi']
        
        # other groups of language that we might want to do at once
            
        self.cyrilliclangs = ['be', 'bg', 'mk', 'ru', 'sr', 'uk'] # languages in Cyrillic
        
        # Languages that are coded in iso8859-1
        self.latin1 = ['en', 'sv', 'nl', 'da', 'dk']
        
        # Languages that used to be coded in iso8859-1
        self.latin1old = ['de', 'et', 'es', 'ia', 'la', 'af', 'cs', 'fr', 'pt', 'sl', 'bs', 'fy',
                    'vi', 'lt', 'fi', 'it', 'no', 'simple', 'gl', 'eu',
                    'nds', 'co', 'mi', 'mr', 'id', 'lv', 'sw', 'tt', 'uk', 'vo',
                    'ga', 'na', 'es', 'test']

    # Methods
    
    def hostname(self, code):
        return 'dvd.wikidev.net'
    
    def path(self, code):
        return '/'

    # Which version of MediaWiki is used?

    def version(self, code):
        return "1.4"

    def put_address(self, code, name):
        return '%s%s?action=submit' % (self.path(code), name)

    def get_address(self, code, name):
        return '%s%s?redirect=no' % (self.path(code), name)

    def edit_address(self, code, name):
        return '%s%s?action=edit' % (self.path(code), name)

    def purge_address(self, code, name):
        return '%s%s?redirect=no&action=purge' % (self.path(code), name)

    def references_address(self, code, name):
        return '%s%s:Whatlinkshere?target=%s&limit=%d' % (self.path(code), self.special_namespace_url(code), name, config.special_page_limit)

    def upload_address(self, code):
        return '%s%s:Upload' % (self.path(code), self.special_namespace_url(code))

    def maintenance_address(self, code, maintenance_page, default_limit = True):
        if default_limit:
            return '%s%s:Maintenance?subfunction=%s' % (self.path(code), self.special_namespace_url(code), maintenance_page)
        else:
            return '%s%s:Maintenance?subfunction=%s&limit=%d' % (self.path(code), self.special_namespace_url(code), maintenance_page, config.special_page_limit)

    def double_redirects_address(self, code, default_limit = True):
        if default_limit:
            return '%s%s:DoubleRedirects' % (self.path(code), self.special_namespace_url(code))
        else:
            return '%s%s:DoubleRedirects?limit=%d' % (self.path(code), self.special_namespace_url(code), config.special_page_limit)

    def broken_redirects_address(self, code, default_limit = True):
        if default_limit:
            return '%s%s:BrokenRedirects' % (self.path(code), self.special_namespace_url(code))
        else:
            return '%s%s:BrokenRedirects?limit=%d' % (self.path(code), self.special_namespace_url(code), config.special_page_limit)

    def allmessages_address(self, code):
        return "%s%s:Allmessages?ot=html" % (self.path(code), self.special_namespace_url(code))

    def login_address(self, code):
        return '%s%s:Userlogin?action=submit' % (self.path(code), self.special_namespace_url(code))

    def move_address(self, code):
        return '%s%s:Movepage?action=submit' % (self.path(code), self.special_namespace_url(code))

    def delete_address(self, code, name):
        return '%s%s?action=delete' % (self.path(code), name)

    def version_history_address(self, code, name):
        return '%s%s?action=history&limit=%d' % (self.path(code), name, config.special_page_limit)

    def export_address(self, code):
        return '%s%s:Export' % (self.path(code), self.special_namespace_url(code))

    def allpagesname(self, code, start):
        # This is very ugly: to get all pages, the wikipedia code
        # 'fakes' getting a page with the returned name.
        # This will need to be fixed someday.
        if self.version(code)=="1.2":
            return '%s:Allpages?printable=yes&from=%s' % (
                self.special_namespace_url(code), start)
        else:
            return '%s:Allpages?from=%s' % (
                self.special_namespace_url(code), start)
        
        
        
    def code2encoding(self, code):
        """Return the encoding for a specific language wikipedia"""
        if code in self.latin1:
            return 'iso8859-1'
        return 'utf-8'
    
    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wikipedia"""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso-8859-2'
        if code == 'ru':
            return 'utf-8', 'iso-8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso8859-1'
        return self.code2encoding(code),
