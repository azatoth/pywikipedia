﻿# -*- coding: utf-8  -*-

import urllib
import family, config

# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia

class Family(family.Family):
    name = 'wikipedia'
    # Known wikipedia languages, given as a dictionary mapping the language code
    # to the hostname of the site hosting that wikipedia. For human consumption,
    # the full name of the language is given behind each line as a comment
    langs = {
        'aa':'aa.wikipedia.org',   # Afar
        'af':'af.wikipedia.org',   # Afrikaans
        'als':'als.wikipedia.org', # Alsatian
        'an':'an.wikipedia.org',   # Aragonese
        'ang':'ang.wikipedia.org', # Anglo-Saxon
        'ar':'ar.wikipedia.org',   # Arabic
        'as':'as.wikipedia.org',   # Assamese
        'ast':'ast.wikipedia.org', # Asturian
        'ay':'ay.wikipedia.org',   # Aymara
        'az':'az.wikipedia.org',   # Azerbaijan
        'be':'be.wikipedia.org',   # Belorussian
        'bg':'bg.wikipedia.org',   # Bulgarian
        'bh':'bh.wikipedia.org',   # Bhojpuri
        'bi':'bi.wikipedia.org',   # Bislama (currently also used by Bitruscan)
        'bn':'bn.wikipedia.org',   # Bengali
        'bo':'bo.wikipedia.org',   # Tibetan
        'br':'br.wikipedia.org',   # Breton
        'bs':'bs.wikipedia.org',   # Bosnian
        'ca':'ca.wikipedia.org',   # Catalan
        'chr':'chr.wikipedia.org', # Cherokee
        'co':'co.wikipedia.org',   # Corsican
        'cs':'cs.wikipedia.org',   # Czech
        'csb':'csb.wikipedia.org', # Kashubian
        'cy':'cy.wikipedia.org',   # Welsh
        'da':'da.wikipedia.org',   # Danish
        'de':'de.wikipedia.org',   # German
        'dk':'da.wikipedia.org',   # Danish (wrong name)
        'ee':'ee.wikipedia.org',   # Ewe
        'el':'el.wikipedia.org',   # Greek
        'en':'en.wikipedia.org',   # English
        'eo':'eo.wikipedia.org',   # Esperanto
        'es':'es.wikipedia.org',   # Spanish
        'et':'et.wikipedia.org',   # Estonian
        'eu':'eu.wikipedia.org',   # Basque
        'fa':'fa.wikipedia.org',   # Farsi
        'fi':'fi.wikipedia.org',   # Finnish
        'fo':'fo.wikipedia.org',   # Faroese
        'fr':'fr.wikipedia.org',   # French
        'fy':'fy.wikipedia.org',   # Frisian
        'ga':'ga.wikipedia.org',   # Irish Gaelic
        'gd':'gd.wikipedia.org',   # Scottish Gaelic
        'gl':'gl.wikipedia.org',   # Galician
        'gn':'gn.wikipedia.org',   # Guarani
        'gu':'gu.wikipedia.org',   # Gujarati
        'gv':'gv.wikipedia.org',   # Manx
        'ha':'ha.wikipedia.org',   # Hausa
        'he':'he.wikipedia.org',   # Hebrew
        'hi':'hi.wikipedia.org',   # Hindi
        'hr':'hr.wikipedia.org',   # Croatian
        'hu':'hu.wikipedia.org',   # Hungarian
        'hy':'hy.wikipedia.org',   # Armenian
        'ia':'ia.wikipedia.org',   # Interlingua
        'id':'id.wikipedia.org',   # Indonesian
        'ie':'ie.wikipedia.org',   # Interlingue
        'io':'io.wikipedia.org',   # Ido
        'is':'is.wikipedia.org',   # Icelandic
        'it':'it.wikipedia.org',   # Italian
        'ja':'ja.wikipedia.org',   # Japanese
        'jbo':'jbo.wikipedia.org', # Lojban
        'jv':'jv.wikipedia.org',   # Javanese
        'ka':'ka.wikipedia.org',   # Georgian
        'kk':'kk.wikipedia.org',   # Kazakh
        'km':'km.wikipedia.org',   # Khmer
        'kn':'kn.wikipedia.org',   # Kannada
        'ko':'ko.wikipedia.org',   # Korean
        'ks':'ks.wikipedia.org',   # Ekspreso, but should become Kashmiri
        'ku':'ku.wikipedia.org',   # Kurdish
        'kw':'kw.wikipedia.org',   # Cornish
        'ky':'ky.wikipedia.org',   # Kirghiz
        'la':'la.wikipedia.org',   # Latin
        'lb':'lb.wikipedia.org',   # Luxembourgish
        'ln':'ln.wikipedia.org',   # Lingala
        'lo':'lo.wikipedia.org',   # Lao
        'lt':'lt.wikipedia.org',   # Latvian
        'lv':'lv.wikipedia.org',   # Livonian
        'mg':'mg.wikipedia.org',   # Malagasy
        'mi':'mi.wikipedia.org',   # Maori
        'minnan':'zh-min-nan.wikipedia.org', # Min-Nan
        'mk':'mk.wikipedia.org',   # Macedonian
        'ml':'ml.wikipedia.org',   # Malayalam
        'mn':'mn.wikipedia.org',   # Mongolian
        'mr':'mr.wikipedia.org',   # Marathi
        'ms':'ms.wikipedia.org',   # Malay
        'mt':'mt.wikipedia.org',   # Maltese
        'my':'my.wikipedia.org',   # Burmese
        'na':'na.wikipedia.org',   # Nauruan
        'nah':'nah.wikipedia.org', # Nahuatl
        'nb':'no.wikipedia.org',   # Norse - new code for Bokmal to distinguish from Nynorsk
        'nds':'nds.wikipedia.org', # Lower Saxon
        'ne':'ne.wikipedia.org',   # Nepalese
        'nl':'nl.wikipedia.org',   # Dutch
        'nn':'nn.wikipedia.org',   # Nynorsk
        'no':'no.wikipedia.org',   # Norwegian
        'nv':'nv.wikipedia.org',   # Navajo
        'oc':'oc.wikipedia.org',   # Occitan
        'om':'om.wikipedia.org',   # Oromo
        'pa':'pa.wikipedia.org',   # Punjabi
        'pi':'pi.wikipedia.org',   # Pali
        'pl':'pl.wikipedia.org',   # Polish
        'ps':'ps.wikipedia.org',   # Pashto (Afghan)
        'pt':'pt.wikipedia.org',   # Portuguese
        'qu':'qu.wikipedia.org',   # Quechua
        'rm':'rm.wikipedia.org',   # Romansch
        'ro':'ro.wikipedia.org',   # Romanian
        'roa-rup':'roa-rup.wikipedia.org', # Aromanian
        'ru':'ru.wikipedia.org',   # Russian
        'sa':'sa.wikipedia.org',   # Sanskrit
        'sd':'sd.wikipedia.org',   # Sindhi
        'se':'se.wikipedia.org',   # Saami
        'sh':'sh.wikipedia.org',   # OBSOLETE, Serbocroatian
        'si':'si.wikipedia.org',   # Sinhalese
        'simple':'simple.wikipedia.org', # Simple English
        'sk':'sk.wikipedia.org',   # Slovakian
        'sl':'sl.wikipedia.org',   # Slovenian
        'sq':'sq.wikipedia.org',   # Albanian
        'sr':'sr.wikipedia.org',   # Serbian
        'st':'st.wikipedia.org',   # Sesotho
        'su':'su.wikipedia.org',   # Sundanese
        'sv':'sv.wikipedia.org',   # Swedish
        'sw':'sw.wikipedia.org',   # Swahili
        'ta':'ta.wikipedia.org',   # Tamil
        'te':'te.wikipedia.org',   # Telugu
        'test':'test.wikipedia.org',
        'tg':'tg.wikipedia.org',   # Tajik
        'th':'th.wikipedia.org',   # Thai
        'tk':'tk.wikipedia.org',   # Turkmen
        'tl':'tl.wikipedia.org',   # Tagalog
        'tlh':'tlh.wikipedia.org', # Klingon
        'tn':'tn.wikipedia.org',   # Tswana
        'to':'to.wikipedia.org',   # Tongan
        'tokipona':'tokipona.wikipedia.org', # Toki Pona
        'tpi':'tpi.wikipedia.org', # Tok Pisin
        'tr':'tr.wikipedia.org',   # Turkish
        'tt':'tt.wikipedia.org',   # Tatar
        'ug':'ug.wikipedia.org',   # Uyghur
        'uk':'uk.wikipedia.org',   # Ukrainian
        'ur':'ur.wikipedia.org',   # Urdu
        'uz':'uz.wikipedia.org',   # Uzbek
        'vi':'vi.wikipedia.org',   # Vietnamese
        'vo':'vo.wikipedia.org',   # Volapuk
        'wa':'wa.wikipedia.org',   # Walon
        'xh':'xh.wikipedia.org',   # isiXhosa
        'yi':'yi.wikipedia.org',   # Yiddish
        'yo':'yo.wikipedia.org',   # Yoruba
        'za':'za.wikipedia.org',   # Zhuang
        'zh':'zh.wikipedia.org',   # Chinese
        'zh-cn':'zh.wikipedia.org', # Simplified Chinese
        'zh-tw':'zh.wikipedia.org', # Traditional Chinese
        'zu':'zu.wikipedia.org',   # Zulu
        }

    # All namespaces are inherited from family.Family.
        
    # Redirect code can be translated, but is only in one language now.
    
    redirect = {
        'cy': 'ail-cyfeirio',
        }
        
    # On most Wikipedias page names must start with a capital letter, but some
    # languages don't use this.
        
    nocapitalize = ['tlh','tokipona']
        
    # Which languages have a special order for putting interlanguage links,
    # and what order is it? If a language is not in interwiki_putfirst,
    # alphabetical order on language code is used. For languages that are in
    # interwiki_putfirst, interwiki_putfirst is checked first, and
    # languages are put in the order given there. All other languages are put
    # after those, in code-alphabetical order.
    
    alphabetic = ['aa','af','ar','an','roa-rup','as','ast','ay','az','bg',
                  'be','bn','bh','bi','bo','bs','br','ca','chr','co','cs',
                  'cy','da','de','als','et','el','en','es','eo','eu','ee',
                  'fa','fo','fr','fy','ga','gv','gd','gl','gn','gu','ko',
                  'ha','hy','hi','hr','io','id','ia','xh','is','zu','it',
                  'he','jv','kn','ka','csb','ks','kk','kw','km','ky','sw',
                  'ku','lo','la','lv','lt','lb','ln','jbo','hu','mk','mg',
                  'ml','mt','mi','mr','ms','minnan','mn','my','nah','na',
                  'nv','nl','ne','ja','no','nb','nn','oc','om','ug','pi',
                  'ps','nds','pl','pt','pa','ro','rm','qu','ru','se','sa',
                  'st','sq','si','simple','sd','sk','sl','sr','su','fi',
                  'sv','tl','tg','ta','tt','te','th','tlh','tk','tw','vi',
                  'tokipona','tpi','to','tn','tr','ur','uk','uz','vo','wa',
                  'yi','yo','za','zh','zh-cn','zh-tw']
        
    interwiki_putfirst = {
        'en': alphabetic,
        'fr': alphabetic,
        'hu': ['en'],
        'pl': alphabetic,
        'simple': alphabetic,
        'fi': ['ab','aa','af','am','ar','an','roa-rup','as','ast','gn','ay',
               'az','id','jv','ms','su','ban','bal','bn','ba','be','mr','bh',
               'bi','bo','nb','bs','br','bug','bg','ca','chr','cs','ch','che',
               'sn','co','za','cy','da','de','di','dz','et','el','en','als',
               'es','eo','eu','fa','fo','fr','fy','ga','gv','sm','gd','gl',
               'gay','gu','ko','ha','hy','hi','hr','iba','io','ia','iu','ik',
               'xh','zu','is','it','he','kl','kn','ka','csb','ks','kaw','kw',
               'kk','rw','ky','rn','sw','ku','lo','la','ls','lv','lt','li','ln',
               'jbo','mad','hu','mak','mk','ml','mg','mt','mi','min','minnan',
               'mo','mn','my','nah','na','nv','fj','ng','nl','ne','ja','no','nn',
               'oc','or','om','ug','pi','pa','ps','km','lo','nds','pl','pt','ro',
               'rm','qu','ru','se','sa','sg','st','tn','sq','si','simple','sd','ss',
               'sk','sl','sr','fi','sv','tl','ta','tt','te','th','ti','tlh',
               'vi','tg','tokipona','tpi','to','tr','tk','tw','ur','uk','uz',
               'vo','wa','wo','ts','yi','yo','zh','zh-tw','zh-cn']
        }
        
    obsolete = ['sh', 'dk', 'tlh']
        
    # A few selected big languages for things that we do not want to loop over
    # all languages. This is only needed by the titletranslate.py module, so
    # if you carefully avoid the options, you could get away without these
    # for another wikimedia family.
    
    biglangs = ['da', 'de', 'en', 'es', 'fr', 'it', 'ja', 'nl', 'pl', 'sv']
    
    biglangs2 = biglangs + [
        'ca', 'eo', 'et', 'fi', 'he', 'no', 'pt', 'ro', 'sl', 'zh']
    
    biglangs3 = biglangs2 + [
        'af', 'bg', 'cs', 'cy', 'hr', 'hu', 'ia', 'id', 'la', 'ms',
        'simple', 'wa']
    
    biglangs4 = biglangs3 + [
        'ast', 'eu', 'fy', 'gl', 'io', 'is', 'ko', 'ku', 'lt', 'nds',
        'oc', 'sk', 'sr', 'su', 'tr', 'ru', 'uk']
    
    seriouslangs = biglangs4 + [
        'ar', 'be', 'bs', 'csb', 'el', 'fa', 'ga', 'hi', 'jv', 'lb', 'lv',
        'mi', 'minnan', 'sa', 'ta', 'th', 'tokipona', 'tt', 'ur', 'vi']
    
    # other groups of language that we might want to do at once
        
    cyrilliclangs = ['be', 'bg', 'mk', 'ru', 'sr', 'uk'] # languages in Cyrillic
    
    # Languages that are coded in iso-8859-1
    latin1 = ['en', 'sv', 'nl', 'da', 'dk']
    
    # Languages that used to be coded in iso-8859-1
    latin1old = ['de', 'et', 'es', 'ia', 'la', 'af', 'cs', 'fr', 'pt', 'sl', 'bs', 'fy',
                 'vi', 'lt', 'fi', 'it', 'no', 'simple', 'gl', 'eu',
                 'nds', 'co', 'mr', 'id', 'lv', 'sw', 'tt', 'uk', 'vo',
                 'ga', 'na', 'es', 'test']

    def version(self, code):
        if code=="test":
            return "1.4"
        else:
            return "1.3"
        
    def code2encoding(self, code):
        """Return the encoding for a specific language wikipedia"""
        if code in self.latin1:
            return 'iso-8859-1'
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
            return 'utf-8', 'iso-8859-1'
        return self.code2encoding(code),

