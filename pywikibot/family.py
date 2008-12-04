# -*- coding: utf-8  -*-

__version__='$Id$'

import config2 as config
import logging
import re
import urllib

from datetime import datetime, timedelta

logger = logging.getLogger("wiki")

# Parent class for all wiki families

class Family:
    def __init__(self):
        self.name = None
            # Updated from http://meta.wikimedia.org/wiki/Interwiki_sorting_order
        self.alphabetic = [
            'aa', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc',
            'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'bm',
            'bn', 'zh-min-nan', 'map-bms', 'ba', 'be', 'be-x-old', 'bh',
            'bcl', 'bi', 'bar', 'bo', 'bs', 'br', 'bg', 'bxr', 'ca', 'cv',
            'ceb', 'cs', 'ch', 'ny', 'sn', 'tum', 'cho', 'co', 'za', 'cy',
            'da', 'pdc', 'de', 'dv', 'nv', 'dsb', 'dz', 'mh', 'et', 'el',
            'eml', 'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'fo',
            'hif', 'fr', 'fy', 'ff', 'fur', 'ga', 'gan', 'gv', 'gd', 'gl',
            'ki', 'glk', 'gu', 'got', 'zh-classical', 'hak', 'xal', 'ko',
            'ha', 'haw', 'hy', 'hi', 'ho', 'hsb', 'hr', 'io', 'ig', 'ilo',
            'bpy', 'id', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is',
            'it', 'he', 'jv', 'kl', 'pam', 'kn', 'kr', 'ka', 'ks', 'csb',
            'kk', 'kw', 'rw', 'ky', 'rn', 'sw', 'kv', 'kg', 'ht', 'kj',
            'ku', 'lad', 'lbe', 'lo', 'la', 'lv', 'lb', 'lt', 'lij', 'li',
            'ln', 'jbo', 'lg', 'lmo', 'hu', 'mk', 'mg', 'ml', 'mt', 'mi',
            'mr', 'mzn', 'ms', 'cdo', 'mdf', 'mo', 'mn', 'mus', 'my', 'nah',
            'na', 'fj', 'nl', 'nds-nl', 'cr', 'ne', 'new', 'ja', 'nap',
            'ce', 'pih', 'no', 'nn', 'nrm', 'nov', 'oc', 'or', 'om', 'ng',
            'hz', 'ug', 'uz', 'pa', 'pi', 'pag', 'pap', 'ps', 'km', 'pms',
            'nds', 'pl', 'pt', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm',
            'qu', 'ru', 'sah', 'se', 'sm', 'sa', 'sg', 'sc', 'sco', 'stq',
            'st', 'tn', 'sq', 'scn', 'si', 'simple', 'sd', 'ss', 'sk', 'cu',
            'sl', 'szl', 'so', 'sr', 'sh', 'srn', 'su', 'fi', 'sv', 'tl',
            'ta', 'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'vi', 'ti',
            'tg', 'tpi', 'to', 'chr', 'chy', 've', 'tr', 'tk', 'tw', 'udm',
            'bug', 'uk', 'ur', 'vec', 'vo', 'fiu-vro', 'wa', 'vls', 'war',
            'wo', 'wuu', 'ts', 'ii', 'yi', 'yo', 'zh-yue', 'cbk-zam', 'diq',
            'zea', 'bat-smg', 'zh',
        ]

        self.langs = {}
        # The timedelta to GMT of the server.
        # Exemple for a server running CET :
        # timedelta(hours=+1)
        self.servergmtoffset = timedelta()

        # letters that can follow a wikilink and are regarded as part of
        # this link
        # This depends on the linktrail setting in LanguageXx.php and on
        # [[MediaWiki:Linktrail]].
        # Note: this is a regular expression.
        self.linktrails = {
           '_default': u'[a-z]*',
           'de': u'[a-zäöüß]*',
           'da': u'[a-zæøå]*',
           'fi': u'[a-zåäö]*',
           'fr': u'[a-zàâçéèêîôû]*',
           'he': u'[a-zא-ת]*',
           'it': u'[a-zàèéìòù]*',
           'kk': u'[a-zäçéğıïñöşüýа-яёәғіқңөұүһʺʹ]*',
           'nl': u'[a-zäöüïëéèéàç]*',
           'pt': u'[a-záâàãéêíóôõúüç]*',
           'ru': u'[a-zа-я]*',
        }

        # Wikimedia wikis all use "bodyContent" as the id of the <div>
        # element that contains the actual page content; change this for
        # wikis that use something else (e.g., mozilla family)
        self.content_id = "bodyContent"

        # A dictionary where keys are family codes that can be used in
        # inter-family interwiki links. Values are not used yet.
        # Generated from http://toolserver.org/~daniel/interwiki-en.txt:
        # remove interlanguage links from file, then run
        # f = open('interwiki-en.txt')
        # for line in f.readlines():
        #     s = line[:line.index('\t')]
        #     print (("            '%s':" % s).ljust(20) + ("'%s'," % s))
        
        # TODO: replace this with API interwikimap call
        self.known_families = {
            'abbenormal':       'abbenormal',
            'aboutccc':         'aboutccc',
            'acadwiki':         'acadwiki',
            'acronym':          'acronym',
            'advogato':         'advogato',
            'airwarfare':       'airwarfare',
            'aiwiki':           'aiwiki',
            'ajaxxab':          'ajaxxab',
            'alife':            'alife',
            'allwiki':          'allwiki',
            'annotation':       'annotation',
            'annotationwiki':   'annotationwiki',
            'archivecompress':  'archivecompress',
            'archivestream':    'archivestream',
            'arxiv':            'arxiv',
            'aspienetwiki':     'aspienetwiki',
            'atmwiki':          'atmwiki',
            'b':                'wikibooks',
            'battlestarwiki':   'battlestarwiki',
            'bemi':             'bemi',
            'benefitswiki':     'benefitswiki',
            'biblewiki':        'biblewiki',
            'bluwiki':          'bluwiki',
            'bmpcn':            'bmpcn',
            'boxrec':           'boxrec',
            'brasilwiki':       'brasilwiki',
            'brazilwiki':       'brazilwiki',
            'brickwiki':        'brickwiki',
            'bridgeswiki':      'bridgeswiki',
            'bryanskpedia':     'bryanskpedia',
            'bswiki':           'bswiki',
            'bugzilla':         'bugzilla',
            'buzztard':         'buzztard',
            'bytesmiths':       'bytesmiths',
            'c2':               'c2',
            'c2find':           'c2find',
            'cache':            'cache',
            'canyonwiki':       'canyonwiki',
            'canwiki':          'canwiki',
            'Ĉej':              'Ĉej',
            'cellwiki':         'cellwiki',
            'changemakers':     'changemakers',
            'chapter':          'chapter',
            'cheatswiki':       'cheatswiki',
            'chej':             'chej',
            'ciscavate':        'ciscavate',
            'cityhall':         'cityhall',
            'ckwiss':           'ckwiss',
            'cliki':            'cliki',
            'cmwiki':           'cmwiki',
            'cndbname':         'cndbname',
            'cndbtitle':        'cndbtitle',
            'codersbase':       'codersbase',
            'colab':            'colab',
            'comixpedia':       'comixpedia',
            'commons':          'commons',
            'communityscheme':  'communityscheme',
            'consciousness':    'consciousness',
            'corpknowpedia':    'corpknowpedia',
            'cpanelwiki':       'cpanelwiki',
            'choralwiki':       'choralwiki',
            'craftedbycarol':   'craftedbycarol',
            'crazyhacks':       'crazyhacks',
            'creationmatters':  'creationmatters',
            'creatureswiki':    'creatureswiki',
            'cxej':             'cxej',
            'dawiki':           'dawiki',
            'dcdatabase':       'dcdatabase',
            'dcma':             'dcma',
            'dejanews':         'dejanews',
            'delicious':        'delicious',
            'demokraatia':      'demokraatia',
            'devmo':            'devmo',
            'dictionary':       'dictionary',
            'dict':             'dict',
            'disinfopedia':     'disinfopedia',
            'diveintoosx':      'diveintoosx',
            'dndwiki':          'dndwiki',
            'docbook':          'docbook',
            'dolphinwiki':      'dolphinwiki',
            'doom_wiki':        'doom_wiki',
            'drae':             'drae',
            'drumcorpswiki':    'drumcorpswiki',
            'dwellerswiki':     'dwellerswiki',
            'dwjwiki':          'dwjwiki',
            'ebwiki':           'ebwiki',
            'eĉei':             'eĉei',
            'echei':            'echei',
            'echolink':         'echolink',
            'ecoreality':       'ecoreality',
            'ecxei':            'ecxei',
            'editcount':        'editcount',
            'efnetceewiki':     'efnetceewiki',
            'efnetcppwiki':     'efnetcppwiki',
            'efnetpythonwiki':  'efnetpythonwiki',
            'efnetxmlwiki':     'efnetxmlwiki',
            'elibre':           'elibre',
            'eljwiki':          'eljwiki',
            'emacswiki':        'emacswiki',
            'encyclopediadramatica':'encyclopediadramatica',
            'energiewiki':      'energiewiki',
            'eokulturcentro':   'eokulturcentro',
            'evowiki':          'evowiki',
            'fanimutationwiki': 'fanimutationwiki',
            'finalempire':      'finalempire',
            'finalfantasy':     'finalfantasy',
            'finnix':           'finnix',
            'firstwiki':        'firstwiki',
            'flickruser':       'flickruser',
            'floralwiki':       'floralwiki',
            'foldoc':           'foldoc',
            'forthfreak':       'forthfreak',
            'foundation':       'foundation',
            'foxwiki':          'foxwiki',
            'freebio':          'freebio',
            'freebsdman':       'freebsdman',
            'freeculturewiki':  'freeculturewiki',
            'freefeel':         'freefeel',
            'freekiwiki':       'freekiwiki',
            'gamewiki':         'gamewiki',
            'ganfyd':           'ganfyd',
            'gatorpedia':       'gatorpedia',
            'gausswiki':        'gausswiki',
            'gentoo-wiki':      'gentoo',
            'genwiki':          'genwiki',
            'glencookwiki':     'glencookwiki',
            'globalvoices':     'globalvoices',
            'glossarwiki':      'glossarwiki',
            'glossarywiki':     'glossarywiki',
            'golem':            'golem',
            'google':           'google',
            'googlegroups':     'googlegroups',
            'gotamac':          'gotamac',
            'greencheese':      'greencheese',
            'guildwiki':        'guildwiki',
            'h2wiki':           'h2wiki',
            'hammondwiki':      'hammondwiki',
            'haribeau':         'haribeau',
            'herzkinderwiki':   'herzkinderwiki',
            'hewikisource':     'hewikisource',
            'hkmule':           'hkmule',
            'holshamtraders':   'holshamtraders',
            'hrwiki':           'hrwiki',
            'hrfwiki':          'hrfwiki',
            'humancell':        'humancell',
            'hupwiki':          'hupwiki',
            'iawiki':           'iawiki',
            'imdbname':         'imdbname',
            'imdbtitle':        'imdbtitle',
            'infoanarchy':      'infoanarchy',
            'infobase':         'infobase',
            'infosecpedia':     'infosecpedia',
            'iso639-3':         'iso639-3',
            'iuridictum':       'iuridictum',
            'jameshoward':      'jameshoward',
            'jargonfile':       'jargonfile',
            'javanet':          'javanet',
            'javapedia':        'javapedia',
            'jefo':             'jefo',
            'jiniwiki':         'jiniwiki',
            'jspwiki':          'jspwiki',
            'jstor':            'jstor',
            'kamelo':           'kamelo',
            'karlsruhe':        'karlsruhe',
            'kerimwiki':        'kerimwiki',
            'kinowiki':         'kinowiki',
            'kmwiki':           'kmwiki',
            'knowhow':          'knowhow',
            'kontuwiki':        'kontuwiki',
            'koslarwiki':       'koslarwiki',
            'lanifexwiki':      'lanifexwiki',
            'linuxwiki':        'linuxwiki',
            'linuxwikide':      'linuxwikide',
            'liswiki':          'liswiki',
            'lojban':           'lojban',
            'lollerpedia':      'lollerpedia',
            'lovebox':          'lovebox',
            'lqwiki':           'lqwiki',
            'lugkr':            'lugkr',
            'lurkwiki':         'lurkwiki',
            'lutherwiki':       'lutherwiki',
            'lvwiki':           'lvwiki',
            'm':                'meta',
            'm-w':              'm-w',
            'mail':             'mail',
            'marveldatabase':   'marveldatabase',
            'mathsongswiki':    'mathsongswiki',
            'mbtest':           'mbtest',
            'meatball':         'meatball',
            'mediazilla':       'mediazilla',
            'memoryalpha':      'memoryalpha',
            'meta':             'meta',
            'metareciclagem':   'metareciclagem',
            'metaweb':          'metaweb',
            'metawiki':         'metawiki',
            'metawikipedia':    'metawikipedia',
            'mineralienatlas':  'mineralienatlas',
            'mjoo':             'mjoo',
            'moinmoin':         'moinmoin',
            'mozcom':           'mozcom',
            'mozillawiki':      'mozillawiki',
            'mozillazinekb':    'mozillazinekb',
            'mozwiki':          'mozwiki',
            'musicbrainz':      'musicbrainz',
            'muweb':            'muweb',
            'mw':               'mw',
            'mwod':             'mwod',
            'mwot':             'mwot',
            'myspace':          'myspace',
            'mytips':           'mytips',
            'n':                'wikinews',
            'netvillage':       'netvillage',
            'nkcells':          'nkcells',
            'nomad':            'nomad',
            'nosmoke':          'nosmoke',
            'nost':             'nost',
            'nswiki':           'nswiki',
            'oeis':             'oeis',
            'oldwikisource':    'oldwikisource',
            'onelook':          'onelook',
            'ourpeachtreecorners':'ourpeachtreecorners',
            'openfacts':        'openfacts',
            'opensourcesportsdirectory':'opensourcesportsdirectory',
            'openwetware':      'openwetware',
            'openwiki':         'openwiki',
            'opera7wiki':       'opera7wiki',
            'organicdesign':    'organicdesign',
            'orgpatterns':      'orgpatterns',
            'orthodoxwiki':     'orthodoxwiki',
            'osi reference model':'osi reference model',
            'ourmedia':         'ourmedia',
            'paganwiki':        'paganwiki',
            'panawiki':         'panawiki',
            'pangalacticorg':   'pangalacticorg',
            'patwiki':          'patwiki',
            'perlconfwiki':     'perlconfwiki',
            'perlnet':          'perlnet',
            'personaltelco':    'personaltelco',
            'phwiki':           'phwiki',
            'phpwiki':          'phpwiki',
            'pikie':            'pikie',
            'planetmath':       'planetmath',
            'pmeg':             'pmeg',
            'pmwiki':           'pmwiki',
            'purlnet':          'purlnet',
            'pythoninfo':       'pythoninfo',
            'pythonwiki':       'pythonwiki',
            'pywiki':           'pywiki',
            'psycle':           'psycle',
            'q':                'wikiquote',
            'quakewiki':        'quakewiki',
            'qwiki':            'qwiki',
            'r3000':            'r3000',
            'rakwiki':          'rakwiki',
            'raec':             'raec',
            'redwiki':          'redwiki',
            'revo':             'revo',
            'rfc':              'rfc',
            'rheinneckar':      'rheinneckar',
            'robowiki':         'robowiki',
            'rowiki':           'rowiki',
            'rtfm':             'rtfm',
            's':                'wikisource',
            's23wiki':          's23wiki',
            'scoutpedia':       'scoutpedia',
            'seapig':           'seapig',
            'seattlewiki':      'seattlewiki',
            'seattlewireless':  'seattlewireless',
            'seeds':            'seeds',
            'senseislibrary':   'senseislibrary',
            'sep11':            'sep11',
            'shakti':           'shakti',
            'shownotes':        'shownotes',
            'siliconvalley':    'siliconvalley',
            'slashdot':         'slashdot',
            'slskrex':          'slskrex',
            'smikipedia':       'smikipedia',
            'sockwiki':         'sockwiki',
            'sourceforge':      'sourceforge',
            'sourcextreme':     'sourcextreme',
            'squeak':           'squeak',
            'stockphotoss':     'stockphotoss',
            'strikiwiki':       'strikiwiki',
            'susning':          'susning',
            'svgwiki':          'svgwiki',
            'swinbrain':        'swinbrain',
            'swingwiki':        'swingwiki',
            'tabwiki':          'tabwiki',
            'takipedia':        'takipedia',
            'tamriel':          'tamriel',
            'tavi':             'tavi',
            'tclerswiki':       'tclerswiki',
            'technorati':       'technorati',
            'tejo':             'tejo',
            'terrorwiki':       'terrorwiki',
            'tesoltaiwan':      'tesoltaiwan',
            'thelemapedia':     'thelemapedia',
            'theo':             'theo',
            'theopedia':        'theopedia',
            'theowiki':         'theowiki',
            'theppn':           'theppn',
            'thinkwiki':        'thinkwiki',
            'tibiawiki':        'tibiawiki',
            'tmbw':             'tmbw',
            'tmnet':            'tmnet',
            'tmwiki':           'tmwiki',
            'toyah':            'toyah',
            'trash!italia':     'trash!italia',
            'turismo':          'turismo',
            'tviv':             'tviv',
            'twiki':            'twiki',
            'twistedwiki':      'twistedwiki',
            'tyvawiki':         'tyvawiki',
            'uncyclopedia':     'uncyclopedia',
            'underverse':       'underverse',
            'unreal':           'unreal',
            'ursine':           'ursine',
            'usej':             'usej',
            'usemod':           'usemod',
            'v':                'wikiversity',
            'videoville':       'videoville',
            'villagearts':      'villagearts',
            'visualworks':      'visualworks',
            'vkol':             'vkol',
            'voipinfo':         'voipinfo',
            'w':                'wikipedia',
            'warpedview':       'warpedview',
            'webdevwikinl':     'webdevwikinl',
            'webisodes':        'webisodes',
            'webseitzwiki':     'webseitzwiki',
            'wiki':             'wiki',
            'wikia':            'wikia',
            'wikianso':         'wikianso',
            'wikibooks':        'wikibooks',
            'wikichristian':    'wikichristian',
            'wikicities':       'wikicities',
            'wikif1':           'wikif1',
            'wikifur':          'wikifur',
            'wikikto':          'wikikto',
            'wikimac-de':       'wikimac-de',
            'wikimac-fr':       'wikimac-fr',
            'wikimedia':        'wikimedia',
            'wikinews':         'wikinews',
            'wikinfo':          'wikinfo',
            'wikinurse':        'wikinurse',
            'wikipaltz':        'wikipaltz',
            'wikipedia':        'wikipedia',
            'wikipediawikipedia':'wikipediawikipedia',
            'wikiquote':        'wikiquote',
            'wikireason':       'wikireason',
            'wikisophia':       'wikisophia',
            'wikisource':       'wikisource',
            'wikiscripts':      'wikiscripts',
            'wikispecies':      'wikispecies',
            'wikiti':           'wikiti',
            'wikitravel':       'wikitravel',
            'wikitree':         'wikitree',
            'wikiveg':          'wikiveg',
            'wikiversity':      'wikiversity',
            'wikiwikiweb':      'wikiwikiweb',
            'wikiworld':        'wikiworld',
            'wikt':             'wiktionary',
            'wiktionary':       'wiktionary',
            'wipipedia':        'wipipedia',
            'wlug':             'wlug',
            'wlwiki':           'wlwiki',
            'wmania':           'wmania',
            'wookieepedia':     'wookieepedia',
            'world66':          'world66',
            'wowwiki':          'wowwiki',
            'wqy':              'wqy',
            'wurmpedia':        'wurmpedia',
            'wznan':            'wznan',
            'xboxic':           'xboxic',
            'ypsieyeball':      'ypsieyeball',
            'zrhwiki':          'zrhwiki',
            'zum':              'zum',
            'zwiki':            'zwiki',
            'zzz wiki':         'zzz wiki',
        }

        # A list of disambiguation template names in different languages
        self.disambiguationTemplates = {
            '_default': []
        }

        # A list with the name of the category containing disambiguation
        # pages for the various languages. Only one category per language,
        # and without the namespace, so add things like:
        # 'en': "Disambiguation"
        self.disambcatname = {}

        # On most wikis page names must start with a capital letter, but some
        # languages don't use this.
        self.nocapitalize = []

        # attop is a list of languages that prefer to have the interwiki
        # links at the top of the page.
        self.interwiki_attop = []
        # on_one_line is a list of languages that want the interwiki links
        # one-after-another on a single line
        self.interwiki_on_one_line = []
        # String used as separator between interwiki links and the text
        self.interwiki_text_separator = '\r\n\r\n'

        # Similar for category
        self.category_attop = []
        # on_one_line is a list of languages that want the category links
        # one-after-another on a single line
        self.category_on_one_line = []
        # String used as separator between category links and the text
        self.category_text_separator = '\r\n\r\n'
        # When both at the bottom should categories come after interwikilinks?
        self.categories_last = []

        # Which languages have a special order for putting interlanguage
        # links, and what order is it? If a language is not in
        # interwiki_putfirst, alphabetical order on language code is used.
        # For languages that are in interwiki_putfirst, interwiki_putfirst
        # is checked first, and languages are put in the order given there.
        # All other languages are put after those, in code-alphabetical
        # order.
        self.interwiki_putfirst = {}

        # Languages in interwiki_putfirst_doubled should have a number plus
        # a list of languages. If there are at least the number of interwiki
        # links, all languages in the list should be placed at the front as
        # well as in the normal list.
        self.interwiki_putfirst_doubled = {}  # THIS APPEARS TO BE UNUSED!

        # Some families, e. g. commons and meta, are not multilingual and
        # forward interlanguage links to another family (wikipedia).
        # These families can set this variable to the name of the target
        # family.
        self.interwiki_forward = None

        # Which language codes no longer exist and by which language code
        # should they be replaced. If for example the language with code xx:
        # now should get code yy:, add {'xx':'yy'} to obsolete. If all
        # links to language xx: should be removed, add {'xx': None}.
        self.obsolete = {}

        # Language codes of the largest wikis. They should be roughly sorted
        # by size.
        self.languages_by_size = []

        # Some languages belong to a group where the possibility is high that
        # equivalent articles have identical titles among the group.
        self.language_groups = {
            # languages using the arabic script (incomplete)
        'arab' : [
                'ar', 'ps', 'sd', 'ur',
                # languages using multiple scripts, including arabic
            'kk', 'ku', 'tt', 'ug'
            ],
            # languages that use chinese symbols
            'chinese': [
                'wuu', 'zh', 'zh-classical', 'zh-yue', 'gan', 'ii',
                # languages using multiple/mixed scripts, including chinese
        'ja', 'za'
            ],
            # languages that use the cyrillic alphabet
            'cyril': [
                'ab', 'av', 'ba', 'be', 'be-x-old', 'bg', 'bxr', 'ce', 'cu',
                'cv', 'kv', 'ky', 'mk', 'lbe', 'mdf', 'mn', 'mo', 'myv',
                'os', 'ru', 'sah', 'tg', 'tk', 'udm', 'uk', 'xal',
                # languages using multiple scripts, including cyrillic
                'ha', 'kk', 'sh', 'sr', 'tt'
            ],
            # languages that use the latin alphabet
            'latin': [
                'aa', 'af', 'ak', 'als', 'an', 'ang', 'ast', 'ay', 'bar',
                'bat-smg', 'bcl', 'bi', 'bm', 'br', 'bs', 'ca', 'cbk-zam',
                'cdo', 'ceb', 'ch', 'cho', 'chy', 'co', 'crh', 'cs', 'csb',
                'cy', 'da', 'de', 'diq', 'dsb', 'ee', 'eml', 'en', 'eo',
                'es', 'et', 'eu', 'ext', 'ff', 'fi', 'fiu-vro', 'fj', 'fo',
                'fr', 'frp', 'fur', 'fy', 'ga', 'gd', 'gl', 'gn', 'gv',
                'hak', 'haw', 'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hz',
                'ia', 'id', 'ie', 'ig', 'ik', 'ilo', 'io', 'is', 'it',
                'jbo', 'jv', 'kaa', 'kab', 'kg', 'ki', 'kj', 'kl', 'kr',
                'ksh', 'kw', 'la', 'lad', 'lb', 'lg', 'li', 'lij', 'lmo',
                'ln', 'lt', 'lv', 'map-bms', 'mg', 'mh', 'mi', 'ms', 'mt',
                'mus', 'na', 'nah', 'nap', 'nds', 'nds-nl', 'ng', 'nl',
                'nn', 'no', 'nov', 'nrm', 'nv', 'ny', 'oc', 'om', 'pag',
                'pam', 'pap', 'pdc', 'pih', 'pl', 'pms', 'pt', 'qu', 'rm',
                'rn', 'ro', 'roa-rup', 'roa-tara', 'rw', 'sc', 'scn', 'sco',
                'se', 'sg', 'simple', 'sk', 'sl', 'sm', 'sn', 'so', 'sq',
                'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'tet',
                'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tum', 'tw', 'ty',
                'uz', 've', 'vec', 'vi', 'vls', 'vo', 'wa', 'war', 'wo',
                'xh', 'yo', 'zea', 'zh-min-nan', 'zu',
                # languages using multiple scripts, including latin
                'az', 'chr', 'ha', 'iu', 'kk', 'ku', 'rmy', 'sh', 'sr',
                'tt', 'ug', 'za'
            ],
            # Scandinavian languages
            'scand': [
                'da', 'fo', 'is', 'no', 'sv'
            ],
        }

        # LDAP domain if your wiki uses LDAP authentication,
        # http://www.mediawiki.org/wiki/Extension:LDAP_Authentication
        self.ldapDomain = ()

        # Allows crossnamespace interwiki linking.
        # Lists the possible crossnamespaces combinations
        # keys are originating NS
        # values are dicts where:
        #   keys are the originating langcode, or _default
        #   values are dicts where:
        #     keys are the languages that can be linked to from the lang+ns, or
        #     '_default'; values are a list of namespace numbers
        self.crossnamespace = {}
        #### Examples :
        ## Allowing linking to pt' 102 NS from any other lang' 0 NS is
        # self.crossnamespace[0] = {
        #     '_default': { 'pt': [102]}
        # }
        ## While allowing linking from pt' 102 NS to any other lang' = NS is
        # self.crossnamespace[102] = {
        #     'pt': { '_default': [0]}
        # }

    def _addlang(self, code, location, namespaces = {}):
        """Add a new language to the langs and namespaces of the family.
           This is supposed to be called in the constructor of the family."""
        self.langs[code] = location
##
##        for num, val in namespaces.items():
##            self.namespaces[num][code]=val

    def get_known_families(self, site):
        return self.known_families

    def linktrail(self, code, fallback = '_default'):
        if self.linktrails.has_key(code):
            return self.linktrails[code]
        elif fallback:
            return self.linktrails[fallback]
        else:
            raise KeyError(
                "ERROR: linktrail in language %(language_code)s unknown"
                           % {'language_code': code})

##    def namespace(self, code, ns_number, fallback='_default', all=False):
##        if not self.isDefinedNS(ns_number):
##            raise KeyError(
##'ERROR: Unknown namespace %(ns_number)d for %(language_code)s:%(ns_name)s'
##                           % {'ns_number': ns_number,
##                              'language_code': code,
##                              'ns_name': self.name})
##        elif self.isNsI18N(ns_number, code):
##            v = self.namespaces[ns_number][code]
##            if type(v) is not list:
##                v = [v,]
##            if all and self.isNsI18N(ns_number, fallback):
##                v2 = self.namespaces[ns_number][fallback]
##                if type(v2) is list:
##                    v.extend(v2)
##                else:
##                    v.append(v2)
##        elif fallback and self.isNsI18N(ns_number, fallback):
##            v = self.namespaces[ns_number][fallback]
##            if type(v) is not list:
##                v = [v,]
##        else:
##            raise KeyError(
##'ERROR: title for namespace %(ns_number)d in language %(language_code)s unknown'
##                           % {'ns_number': ns_number,
##                              'language_code': code})
##        if all:
##            namespaces = list(set(v))
##            # Lowercase versions of namespaces
##            if code not in self.nocapitalize:
##                namespaces.extend([ns[0].lower() + ns[1:]
##                                   for ns in namespaces
##                                   if ns and ns[0].lower() != ns[0].upper()])
##            # Underscore versions of namespaces
##            namespaces.extend([ns.replace(' ', '_')
##                               for ns in namespaces if ns and ' ' in ns])
##            return tuple(namespaces)
##        else:
##            return v[0]
##
##    def isDefinedNS(self, ns_number):
##        """Return True if the namespace has been defined in this family."""
##        
##        return self.namespaces.has_key(ns_number)
##
##    def isNsI18N(self, ns_number, code):
##        """Return True if the namespace has been internationalized.
##
##        (it has a custom entry for a given language)
##
##        """
##        return self.namespaces[ns_number].has_key(code)
##
##    def isDefinedNSLanguage(self, ns_number, code, fallback='_default'):
##        """Return True if the namespace has been defined in this family
##        for this language or its fallback.
##        """
##        if not self.isDefinedNS(ns_number):
##            return False
##        elif self.isNsI18N(ns_number, code):
##            return True
##        elif fallback and self.isNsI18N(ns_number, fallback):
##            return True
##        else:
##            return False
##
##    def normalizeNamespace(self, code, value):
##        """Given a value, attempt to match it with all available namespaces,
##        with default and localized versions. Sites may have more than one
##        way to write the same namespace - choose the first one in the list.
##        If nothing can be normalized, return the original value.
##        """
##        for ns, items in self.namespaces.iteritems():
##            if items.has_key(code):
##                v = items[code]
##            elif items.has_key('_default'):
##                v = items['_default']
##            else:
##                continue
##            if type(v) is list:
##                if value in v: return v[0]
##            else:
##                if value == v: return v
##            try:
##                if value == self.namespace('_default', ns):
##                    return self.namespace(code, ns)
##            except KeyError:
##                pass
##        return value
##
##    def getNamespaceIndex(self, lang, namespace):
##        """Given a namespace, attempt to match it with all available
##        namespaces. Sites may have more than one way to write the same
##        namespace - choose the first one in the list. Returns namespace
##        index or None.
##        """
##        namespace = namespace.lower()
##        for n in self.namespaces.keys():
##            try:
##                nslist = self.namespaces[n][lang]
##                if type(nslist) != type([]):
##                    nslist = [nslist]
##                for ns in nslist:
##                    if ns.lower() == namespace:
##                        return n
##            except (KeyError,AttributeError):
##                # The namespace has no localized name defined
##                pass
##        if lang != '_default':
##            # This is not a localized namespace. Try if it
##            # is a default (English) namespace.
##            return self.getNamespaceIndex('_default', namespace)
##        else:
##            # give up
##            return None
##
    def disambig(self, code, fallback = '_default'):
        if self.disambiguationTemplates.has_key(code):
            return self.disambiguationTemplates[code]
        elif fallback:
            return self.disambiguationTemplates[fallback]
        else:
            raise KeyError(
"ERROR: title for disambig template in language %(language_code)s unknown"
                           % {'language_code': code})

    # Redirect code can be translated.
    # Note that redirect codes are case-insensitive, so it is enough
    # to enter the code in lowercase here.
    redirect = {
        'ar': [u'تحويل'],
        'be-x-old': [u'перанакіраваньне'],
        'bg': [u'виж'],
        'bs': [u'preusmjeri'],
        'cy': [u'ail-cyfeirio'],
        'el': [u'ΑΝΑΚΑΤΕΥΘΥΝΣΗ'],
        'et': [u'suuna'],
        'fa': [u'تغییرمسیر'],
        'fi': [u'ohjaus', u'uudelleenohjaus'],
        'ga': [u'athsheoladh'],
        'he': [u'הפניה'],
        'hu': [u'átirányítás'],
        'id': [u'alih'],
        'is': [u'tilvísun'],
        'jv': [u'alih'],
        'ka': [u'გადამისამართება'],
        'kk': [u'айдау'],
        'ko': [u'넘겨주기'],
        'mzn': [u'تغییرمسیر'],
        'nl': [u'DOORVERWIJZING'],
        'nn': [u'omdiriger'],
        'ru': [u'REDIRECT',             # localised version is not
               u'перенаправление',      # so usual, so put the default
               u'перенапр'],            # one as the most used.
        'sk': [u'presmeruj'],
        'sr': [u'преусмери', u'Преусмери'], # lowercase only doesn't work?
        'su': [u'redirected', u'alih'],
        'tt': [u'yünältü'],
        'yi': [u'ווייטערפירן']
    }

    # So can be pagename code
    pagename = {
        'bg': [u'СТРАНИЦА'],
        'he': [u'שם הדף'],
        'kk': [u'БЕТАТАУЫ'],
        'nn': ['SIDENAMN','SIDENAVN'],
        'ru': [u'НАЗВАНИЕСТРАНИЦЫ'],
        'sr': [u'СТРАНИЦА'],
        'tt': [u'BİTİSEME']
    }

    pagenamee = {
        'he': [u'שם הדף מקודד'],
        'kk': [u'БЕТАТАУЫ2'],
        'nn': ['SIDENAMNE','SIDENAVNE'],
        'ru': [u'НАЗВАНИЕСТРАНИЦЫ2'],
        'sr': [u'СТРАНИЦЕ']
    }

    def pagenamecodes(self,code):
        pos = ['PAGENAME']
        pos2 = []
        if code in self.pagename.keys():
            pos = pos + self.pagename[code]
        elif code == 'als':
            return self.pagenamecodes('de')
        elif code == 'bm':
            return self.pagenamecodes('fr')
        for p in pos:
            pos2 += [p,p.lower()]
        return pos2

    def pagename2codes(self,code):
        pos = ['PAGENAME']
        pos2 = []
        if code in self.pagenamee.keys():
            pos = pos + self.pagenamee[code]
        elif code == 'als':
            return self.pagename2codes('de')
        elif code == 'bm':
            return self.pagename2codes('fr')
        for p in pos:
            pos2 += [p,p.lower()]
        return pos2

    # Methods
    def protocol(self, code):
        """
        Can be overridden to return 'https'.
        Other protocols are not supported.
        """
        return 'http'

    def hostname(self, code):
        return self.langs[code]

    def scriptpath(self, code):
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        """
        return '/w'

    def path(self, code):
        return '%s/index.php' % self.scriptpath(code)

    def querypath(self, code):
        return '%s/query.php' % self.scriptpath(code)

    def apipath(self, code):
        return '%s/api.php' % self.scriptpath(code)

    def nicepath(self, code):
        return '/wiki/'

    def dbName(self, code):
        # returns the name of the MySQL database
        return '%s%s' % (code, self.name)

    # Which version of MediaWiki is used?
    def version(self, code):
        """Return MediaWiki version number as a string."""
        # Don't use this, use versionnumber() instead. This only exists
        # to not break family files.
        return '1.13alpha'

    def versionnumber(self, code):
        """Return an int identifying MediaWiki version.

        Currently this is implemented as returning the minor version
        number; i.e., 'X' in version '1.X.Y'

        """
        R = re.compile(r"(\d+).(\d+)")
        M = R.search(self.version(code))
        if not M:
            # Version string malformatted; assume it should have been 1.10
            return 10
        return 1000 * int(M.group(1)) + int(M.group(2)) - 1000

    def code2encoding(self, code):
        """Return the encoding for a specific language wiki"""
        return 'utf-8'

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wiki"""
        return self.code2encoding(code),

    # aliases
    def encoding(self, code):
        """Return the encoding for a specific language wiki"""
        return self.code2encoding(code)

    def encodings(self, code):
        """Return a list of historical encodings for a specific language
           wiki"""
        return self.code2encodings(code)

    def __cmp__(self, otherfamily):
        try:
            return cmp(self.name, otherfamily.name)
        except AttributeError:
            return cmp(id(self), id(otherfamily))

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return 'Family("%s")' % self.name

    def RversionTab(self, code):
        """Change this to some regular expression that shows the page we
        found is an existing page, in case the normal regexp does not work."""
        return None

    def has_query_api(self,code):
        """Is query.php installed in the wiki?"""
        return False

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)

    def server_time(self, code):
        """Return a datetime object representing server time"""
        # TODO : If the local computer time is wrong, result will be wrong
        return datetime.utcnow() + self.servergmtoffset

    def isPublic(self, code):
        """Does the wiki require logging in before viewing it?"""
        return True

    def post_get_convert(self, site, getText):
        """Does a conversion on the retrieved text from the wiki
        i.e. Esperanto X-conversion """
        return getText

    def pre_put_convert(self, site, putText):
        """Does a conversion on the text to insert on the wiki
        i.e. Esperanto X-conversion """
        return putText