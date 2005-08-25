#!/usr/bin/python
# -*- coding: utf-8  -*-

'''
This module contains code to store Wiktionary content in Python objects.
The objects can output the content again in Wiktionary format by means of the wikiWrap methods

I'm currently working on a parser that can read the textual version in the various Wiktionary formats and store what it finds in the Python objects.

The data dictionaries will be moved to a separate file, later on. Right now it's practical to have everything together. They also still need to be expanded to contain more languages and more Wiktionary formats. Right now I like to keep everything together to keep my sanity.

The code is still very much alpha level and the scope of what it can do is still rather limited, only 3 parts of speech, only 2 different Wiktionary output formats, only langnames matrix for about 8 languages. On of the things on the todo list is to harvest the content of this matrix dictionary from the various Wiktionary projects. GerardM put them all in templates already.
'''


#from editarticle import EditArticle
#import wikipedia
import copy

isolangs = ['af','sq','ar','an','hy','ast','tay','ay','az','bam','eu','bn','my','bi','bs','br','bg','sro','ca','zh','chp','rmr','co','dgd','da','de','eml','en','eo','et','fo','fi','fr','cpf','fy','fur','gl','ka','el','gu','hat','haw','he','hi','hu','io','ga','is','gil','id','ia','it','ja','jv','ku','kok','ko','hr','lad','la','lv','ln','li','lt','lb','src','ma','ms','mg','mt','mnc','mi','mr','mh','mas','myn','mn','nah','nap','na','nds','no','ny','oc','uk','oen','grc','pau','pap','pzh','fa','pl','pt','pa','qu','rap','roh','ra','ro','ja-ro','ru','smi','sm','sa','sc','sco','sr','sn','si','sk','sl','so','sov','es','scn','su','sw','tl','tt','th','ti','tox','cs','che','tn','tum','tpn','tr','ts','tvl','ur','vi','vo','wa','cy','be','wo','xh','zu','sv']

wiktionaryformats = {
    'nl': {
        'langheader': u'{{-%%ISOLangcode%%-}}',
        'translang': u':*{{%%ISOLangcode%%}}',
        'beforeexampleterm': u"'''",
        'afterexampleterm': u"'''",
        'gender': u"{{%%gender%%}}",
        'posheader': {
                'noun': u'{{-noun-}}',
                'adjective': u'{{-adj-}}',
                'verb': u'{{-verb-}}',
                },
        'translationsheader': u"{{-trans-}}",
        'transbefore': u'{{top}}',
        'transinbetween': u'{{mid}}',
        'transafter': u'{{after}}',
        'transnoAtoM': u'<!-- Vertalingen van A tot M komen hier-->',
        'transnoNtoZ': u'<!-- Vertalingen van N tot Z komen hier-->',
        'synonymsheader': u"{{-syn-}}",
        'relatedheader': u'{{-rel-}}',
        },
    'en': {
        'langheader': u'==%%langname%%==',
        'translang': u'*%%langname%%',
        'beforeexampleterm': u"'''",
        'afterexampleterm': u"'''",
        'gender': u"''%%gender%%''",
        'posheader': {
                'noun': u'===Noun===',
                'adjective': u'===Adjective===',
                'verb': u'===Verb===',
                },
        'translationsheader': u"====Translations====",
        'transbefore': u'{{top}}',
        'transinbetween': u'{{mid}}',
        'transafter': u'{{after}}',
        'transnoAtoM': u'<!-- Translations from A tot M go here-->',
        'transnoNtoZ': u'<!-- Translations from N tot Z go here-->',
        'synonymsheader': u"====Synonyms====",
        'relatedheader': u'===Related words===',
        }
}

pos = {
    u'noun': u'noun',
    u'adjective': u'adjective',
    u'verb': u'verb',
}

otherheaders = {
    u'see also': u'seealso',
    u'see': u'seealso',
    u'translations': u'trans',
    u'trans': u'trans',
    u'synonyms': u'syn',
    u'syn': u'syn',
    u'antonyms': u'ant',
    u'ant': u'ant',
    u'pronunciation': u'pron',
    u'pron': u'pron',
    u'related terms': u'rel',
    u'rel': u'rel',
    u'acronym': u'acr',
    u'acr': u'acr',
    u'etymology': u'etym',
    u'etym': u'etym',
}

langnames = {
    'nl':    {
        'translingual' : u'Taalonafhankelijk',
        'nl' : u'Nederlands',
        'en' : u'Engels',
        'de' : u'Duits',
        'fr' : u'Frans',
        'it' : u'Italiaans',
        'eo' : u'Esperanto',
        'es' : u'Spaans',
        },
     'de':    {
        'translingual' : u'???',
        'nl' : u'Niederländisch',
        'en' : u'Englisch',
        'de' : u'Deutsch',
        'fr' : u'Französisch',
        'it' : u'Italienisch',
        'eo' : u'Esperanto',
        'es' : u'Spanisch',
        },
     'en':    {
        'translingual' : u'Translingual',
        'nl' : u'Dutch',
        'en' : u'English',
        'de' : u'German',
        'fr' : u'French',
        'it' : u'Italian',
        'eo' : u'Esperanto',
        'es' : u'Spanish',
        },
    'eo':    {
        'translingual' : u'???',
        'nl' : u'Nederlanda',
        'en' : u'Angla',
        'de' : u'Germana',
        'fr' : u'Franca',
        'it' : u'Italiana',
        'eo' : u'Esperanto',
        'es' : u'Hispana',
        },
    'it':    {
        'translingual' : u'???',
        'nl' : u'olandese',
        'en' : u'inglese',
        'de' : u'tedesco',
        'fr' : u'francese',
        'it' : u'italiano',
        'eo' : u'esperanto',
        'es' : u'spagnuolo',
        },
    'fr':    {
        'translingual' : u'???',
        'nl' : u'néerlandais',
        'en' : u'anglais',
        'de' : u'allemand',
        'fr' : u'français',
        'it' : u'italien',
        'eo' : u'espéranto',
        'es' : u'espagnol',
        },
    'es':    {
        'translingual' : u'???',
        'nl' : u'olandés',
        'en' : u'inglés',
        'de' : u'alemán',
        'fr' : u'francés',
        'it' : u'italiano',
        'eo' : u'esperanto',
        'es' : u'español',
        },
}

def invertlangnames():
    '''
    On the English Wiktionary it is customary to use full language names. For
    parsing we need a dictionary to efficiently convert these back to iso
    abbreviations.
    '''
    invertedlangnames = {}
    for ISOKey in langnames.keys():
        for ISOKey2 in langnames[ISOKey].keys():
            lowercaselangname=langnames[ISOKey][ISOKey2].lower()
            #Put in the names of the languages so we can easily do a reverse lookup lang name -> iso abbreviation
            invertedlangnames.setdefault(lowercaselangname, ISOKey2)
            # Now all the correct forms are in, but we also want to be able to find them when there are typos in them
            for index in range(1,len(lowercaselangname)):
                # So first we create all the possibilities with one letter gone
                invertedlangnames.setdefault(lowercaselangname[:index]+lowercaselangname[index+1:], ISOKey2)
                # Then we switch two consecutive letters
                invertedlangnames.setdefault(lowercaselangname[:index-1]+lowercaselangname[index]+lowercaselangname[index-1]+lowercaselangname[index+1:], ISOKey2)
                # There are of course other typos possible, but this caters for a lot of possibilities already
                # TODO One other treatment that would make sense is to filter out the accents.
    return invertedlangnames

def createPOSlookupDict():
    for key in pos.keys():
        lowercasekey=key.lower()
        value=pos[key]
        for index in range(1,len(lowercasekey)):
            # So first we create all the possibilities with one letter gone
            pos.setdefault(lowercasekey[:index]+lowercasekey[index+1:], value)
            # Then we switch two consecutive letters
            pos.setdefault(lowercasekey[:index-1]+lowercasekey[index]+lowercasekey[index-1]+lowercasekey[index+1:], value)
            # There are of course other typos possible, but this caters for a lot of possibilities already
    return pos

def createOtherHeaderslookupDict():
    for key in otherheaders.keys():
        lowercasekey=key.lower()
        value=otherheaders[key]
        for index in range(1,len(lowercasekey)):
            # So first we create all the possibilities with one letter gone
            otherheaders.setdefault(lowercasekey[:index]+lowercasekey[index+1:], value)
            # Then we switch two consecutive letters
            otherheaders.setdefault(lowercasekey[:index-1]+lowercasekey[index]+lowercasekey[index-1]+lowercasekey[index+1:], value)
            # There are of course other typos possible, but this caters for a lot of possibilities already
    return otherheaders

# A big thanks to Rob Hooft for the following class:
# It may not seem like much, but it magically allows the translations to be sorted on
# the names of the languages. I would never have thought of doing it like this myself.
class sortonname:
    '''
    This class sorts translations alphabetically on the name of the language,
    instead of on the iso abbreviation that is used internally.
    '''
    def __init__(self, lang):
        self.lang = lang

    def __call__(self, one, two):
        return cmp(self.lang[one], self.lang[two])

# this is setup
invertedlangnames=invertlangnames()
createPOSlookupDict()
createOtherHeaderslookupDict()

if __name__ == '__main__':

    temp()


    ofn = 'wiktionaryentry.txt'
    content = open(ofn).readlines()

    apage = WiktionaryPage(wikilang,pagetopic)
    apage.parseWikiPage(content)
