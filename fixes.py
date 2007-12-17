# -*- coding: utf-8  -*-
""" File containing all standard fixes """
__version__ = '$Id$'

help = """
                       * HTML       -  Convert HTML tags to wiki syntax, and
                                       fix XHTML.
                       * isbn        - Fix badly formatted ISBNs.
                       * syntax     -  Try to fix bad wiki markup. Do not run
                                       this in automatic mode, as the bot may
                                       make mistakes.
                       * syntax-safe - Like syntax, but less risky, so you can
                                       run this in automatic mode.
                       * case-de     - fix upper/lower case errors in German
                       * grammar-de  - fix grammar and typography in German
"""

fixes = {
	# These replacements will convert HTML to wiki syntax where possible, and
	# make remaining tags XHTML compliant.
	'HTML': {
		'regex': True,
		'msg': {
			'en':u'Robot: converting/fixing HTML',
			'de':u'Bot: konvertiere/korrigiere HTML',
			'fr':u'Robot: convertit/fixe HTML',
			'he':u'בוט: ממיר/מתקן HTML',
			'ia':u'Robot: conversion/reparation de HTML',
			'lt':u'robotas: konvertuojamas/taisomas HTML',
			'nl':u'Bot: conversie/reparatie HTML',
			'pl':u'Robot konwertuje/naprawia HTML',
			'pt':u'Bot: Corrigindo HTML',
			'sr':u'Бот: Поправка HTML-а'
		},
		'replacements': [
			# Everything case-insensitive (?i)
			# Keep in mind that MediaWiki automatically converts <br> to <br />
			# when rendering pages, so you might comment the next two lines out
			# to save some time/edits.
			#r'(?i)<br>':                      r'<br />',
			# linebreak with attributes
			#r'(?i)<br ([^>/]+?)>':            r'<br \1 />',
			(r'(?i)<b>(.*?)</b>',              r"'''\1'''"),
			(r'(?i)<strong>(.*?)</strong>',    r"'''\1'''"),
			(r'(?i)<i>(.*?)</i>',              r"''\1''"),
			(r'(?i)<em>(.*?)</em>',            r"''\1''"),
			# horizontal line without attributes in a single line
			(r'(?i)([\r\n])<hr[ /]*>([\r\n])', r'\1----\2'),
			# horizontal line without attributes with more text in the same line
			#(r'(?i) +<hr[ /]*> +',             r'\r\n----\r\n'),
			# horizontal line with attributes; can't be done with wiki syntax
			# so we only make it XHTML compliant
			(r'(?i)<hr ([^>/]+?)>',            r'<hr \1 />'),
			# a header where only spaces are in the same line
			(r'(?i)([\r\n]) *<h1> *([^<]+?) *</h1> *([\r\n])',  r"\1= \2 =\3"),
			(r'(?i)([\r\n]) *<h2> *([^<]+?) *</h2> *([\r\n])',  r"\1== \2 ==\3"),
			(r'(?i)([\r\n]) *<h3> *([^<]+?) *</h3> *([\r\n])',  r"\1=== \2 ===\3"),
			(r'(?i)([\r\n]) *<h4> *([^<]+?) *</h4> *([\r\n])',  r"\1==== \2 ====\3"),
			(r'(?i)([\r\n]) *<h5> *([^<]+?) *</h5> *([\r\n])',  r"\1===== \2 =====\3"),
			(r'(?i)([\r\n]) *<h6> *([^<]+?) *</h6> *([\r\n])',  r"\1====== \2 ======\3"),
			# TODO: maybe we can make the bot replace <p> tags with \r\n's.
		],
		'exceptions': {
			'inside-tags': [
				'nowiki',
				'comment',
				'math',
				'pre'
			],
		}
	},

	# Grammar fixes for German language
	'grammar-de': {
		'regex': True,
		'msg': {
			'de':u'Bot: korrigiere Grammatik',
		},
		'replacements': [
			#(u'([Ss]owohl) ([^,\.]+?), als auch',                                                            r'\1 \2 als auch'),
			#(u'([Ww]eder) ([^,\.]+?), noch', r'\1 \2 noch'),
			#
			# Vorsicht bei Substantiven, z. B. 3-Jähriger!
			(u'(\d+)(minütig|stündig|tägig|wöchig|jährig|minütlich|stündlich|täglich|wöchentlich|jährlich|fach|mal|malig|köpfig|teilig|gliedrig|geteilt|elementig|dimensional|bändig|eckig|farbig|stimmig)', r'\1-\2'),
			# zusammengesetztes Wort, Bindestrich wird durchgeschleift
			(u'(?<!\w)(\d+|\d+[\.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min|µm|mm|cm|dm|m|km|°C|kB|MB|TB|W|kW|MW|PS|Nm|eV|J|kcal|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)([²³]?-[\w\[])',           r'\1-\2\3'),
			# Größenangabe ohne Leerzeichen vor Einheit
			# weggelassen wegen vieler falsch Positiver: s, A, V, C, S, %
			(u'(?<!\w)(\d+|\d+[\.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min|µm|mm|cm|dm|m|km|°C|kB|MB|TB|W|kW|MW|PS|Nm|eV|J|kcal|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)(?=\W|²|³|$)',          r'\1 \2'),
			# Kein Leerzeichen zwischen Tag und Monat
			(u'(\d+)\.(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)', r'\1. \2'),
			# Keine führende Null beim Datum
			#(u'0(\d+)\. (Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)', r'\1. \2'),
			# Kein Leerzeichen nach Komma
			(u'([a-z](\]\])?,)((\[\[)?[a-zA-Z])',                                                                          r'\1 \3'),
			# Leerzeichen und Komma vertauscht
			(u'([a-z](\]\])?) ,((\[\[)?[a-zA-Z])',                                                                          r'\1, \3'),
			#(u'([a-z]\.)([A-Z])',                                                                             r'\1 \2'),
		],
		'exceptions': {
			'inside-tags': [
				'nowiki',
				'comment',
				'math',
				'pre',           # because of code examples
				'startspace',    # because of code examples
				'hyperlink',     # e.g. commas in URLs
				'gallery',       # because of filenames
			],
			'text-contains': [
				r'sic!',
			],
			'inside': [
				r'Ju 52/3m', # Flugzeugbezeichnung
				r'AH-1W',    # Hubschrauberbezeichnung
				r'\d+h \d+m', # Schreibweise für Zeiten, vor allem in Film-Infoboxen. Nicht korrekt, aber dafür schön kurz.
				r'(?i)\[\[(Bild|Image|Media):.+?\|', # Dateinamen auslassen
			],
			'title': [
				r'Arsen',  # chemische Formel
			],
		}
	},

	# Do NOT run this automatically!
	# Recommendation: First run syntax-safe automatically, afterwards
	# run syntax manually, carefully checking that you're not breaking
	# anything.
	'syntax': {
		'regex': True,
		'msg': {
			'de':u'Bot: Korrigiere Wiki-Syntax',
			'en':u'Bot: Fixing wiki syntax',
			'fr':u'Bot: Corrige wiki-syntaxe',
			'he':u'בוט: מתקן תחביר ויקי',
			'ia':u'Robot: Reparation de syntaxe wiki',
			'lt':u'robotas: Taisoma wiki sintaksė',
			'nl':u'Bot: reparatie wikisyntaxis',
			'pl':u'Robot poprawia wiki-składnię',
			'pt':u'Bot: Corrigindo sintaxe wiki',
			'sr':u'Бот: Поправка вики синтаксе',
		},
		'replacements': [
			# external link in double brackets
			(r'\[\[(?P<url>https?://[^\]]+?)\]\]',   r'[\g<url>]'),
			# external link starting with double bracket
			(r'\[\[(?P<url>https?://.+?)\]',   r'[\g<url>]'),
			# external link with forgotten closing bracket
			#(r'\[(?P<url>https?://[^\]\s]+)\r\n',  r'[\g<url>]\r\n'),
			# external link ending with double bracket.
			# do not change weblinks that contain wiki links inside
			# inside the description
			(r'\[(?P<url>https?://[^\[\]]+?)\]\](?!\])',   r'[\g<url>]'),
			# external link and description separated by a dash.
			# ATTENTION: while this is a mistake in most cases, there are some
			# valid URLs that contain dashes!
			(r'\[(?P<url>https?://[^\|\]\s]+?) *\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
			# wiki link closed by single bracket.
			# ATTENTION: There are some false positives, for example
			# Brainfuck code examples or MS-DOS parameter instructions.
			# There are also sometimes better ways to fix it than
			# just putting an additional ] after the link.
			(r'\[\[([^\[\]]+?)\](?!\])',  r'[[\1]]'),
			# wiki link opened by single bracket.
			# ATTENTION: same as above.
			(r'(?<!\[)\[([^\[\]]+?)\]\](?!\])',  r'[[\1]]'),
			# template closed by single bracket
			# ATTENTION: There are some false positives, especially in
			# mathematical context or program code.
			(r'{{([^{}]+?)}(?!})',       r'{{\1}}'),
		],
		'exceptions': {
			'inside-tags': [
				'nowiki',
				'comment',
				'math',
				'pre',
			],
			'text-contains': [
				r'http://.*?object=tx\|',               # regular dash in URL
				r'http://.*?allmusic\.com',             # regular dash in URL
				r'http://.*?allmovie\.com',             # regular dash in URL
				r'http://physics.nist.gov/',            # regular dash in URL
				r'http://www.forum-seniorenarbeit.de/', # regular dash in URL
				r'http://kuenstlerdatenbank.ifa.de/',   # regular dash in URL
				r'&object=med',                         # regular dash in URL
				r'\[CDATA\['                            # lots of brackets
			],
		}
	},

	# The same as syntax, but restricted to replacements that should
	# be safe to run automatically.
	'syntax-safe': {
		'regex': True,
		'msg': {
			'de':u'Bot: Korrigiere Wiki-Syntax',
			'en':u'Bot: Fixing wiki syntax',
			'fr':u'Bot: Corrige wiki-syntaxe',
			'he':u'בוט: מתקן תחביר ויקי',
			'ia':u'Robot: Reparation de syntaxe wiki',
			'lt':u'robotas: Taisoma wiki sintaksė',
			'nl':u'Bot: reparatie wikisyntaxis',
			'pl':u'Robot poprawia wiki-składnię',
			'pt':u'Bot: Corrigindo sintaxe wiki',
			'sr':u'Бот: Поправка вики синтаксе',
		},
		'replacements': [
			# external link in double brackets
			(r'\[\[(?P<url>https?://[^\]]+?)\]\]',   r'[\g<url>]'),
			# external link starting with double bracket
			(r'\[\[(?P<url>https?://.+?)\]',   r'[\g<url>]'),
			# external link with forgotten closing bracket
			#(r'\[(?P<url>https?://[^\]\s]+)\r\n',   r'[\g<url>]\r\n'),
			# external link and description separated by a dash, with
			# whitespace in front of the dash, so that it is clear that
			# the dash is not a legitimate part of the URL.
			(r'\[(?P<url>https?://[^\|\] \r\n]+?) +\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
			# dash in external link, where the correct end of the URL can
			# be detected from the file extension. It is very unlikely that
			# this will cause mistakes.
			(r'\[(?P<url>https?://[^\|\] ]+?(\.pdf|\.html|\.htm|\.php|\.asp|\.aspx|\.jsp)) *\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
		],
	},

	'case-de': { # German upper / lower case issues
		'regex': True,
		'msg': {
			'de':u'Bot: Korrigiere Groß-/Kleinschreibung',
		},
		'replacements': [
			(r'\batlantische(r|n|) Ozean', r'Atlantische\1 Ozean'),
			(r'\bdeutsche(r|n|) Bundestag\b', r'Deutsche\1 Bundestag'),
			(r'\bdeutschen Bundestags\b', r'Deutschen Bundestags'), # Aufpassen, z. B. 'deutsche Bundestagswahl'
			(r'\bdeutsche(r|n|) Reich\b', r'Deutsche\1 Reich'),
			(r'\bdeutschen Reichs\b', r'Deutschen Reichs'), # Aufpassen, z. B. 'deutsche Reichsgrenzen'
			(r'\bdritte(n|) Welt(?!krieg)', r'Dritte\1 Welt'),
			(r'\bdreißigjährige(r|n|) Krieg', r'Dreißigjährige\1 Krieg'),
			(r'\beuropäische(n|) Gemeinschaft', r'Europäische\1 Gemeinschaft'),
			(r'\beuropäische(n|) Kommission', r'Europäische\1 Kommission'),
			(r'\beuropäische(n|) Parlament', r'Europäische\1 Parlament'),
			(r'\beuropäische(n|) Union', r'Europäische\1 Union'),
			(r'\berste(r|n|) Weltkrieg', r'Erste\1 Weltkrieg'),
			(r'\bkalter(r|n|) Krieg', r'Kalte\1 Krieg'),
			(r'\bpazifische(r|n|) Ozean', r'Pazifische\1 Ozean'),
			(r'Tag der deutschen Einheit', r'Tag der Deutschen Einheit'),
			(r'\bzweite(r|n|) Weltkrieg', r'Zweite\1 Weltkrieg'),
		],
		'exceptions': {
			'inside-tags': [
				'nowiki',
				'comment',
				'math',
				'pre',
			],
			'text-contains': [
				r'sic!',
			],
		}
	},

	'vonbis': {
		'regex': True,
		'msg': {
			'de':u'Bot: Ersetze Binde-/Gedankenstrich durch "bis"',
		},
		'replacements': [
			# Bindestrich, Gedankenstrich, Geviertstrich
			(u'(von \d{3,4}) *(-|&ndash;|–|&mdash;|—) *(\d{3,4})', r'\1 bis \3'),
		],
	},

	# some disambiguation stuff for de:
	# python replace.py -fix:music -subcat:Album
	'music': {
		'regex': False,
		'msg': {
			'de':u'Bot: korrigiere Links auf Begriffsklärungen',
		},
		'replacements': [
			(u'[[CD]]', u'[[Audio-CD|CD]]'),
			(u'[[LP]]', u'[[Langspielplatte|LP]]'),
			(u'[[EP]]', u'[[Extended Play|EP]]'),
			(u'[[MC]]', u'[[Musikkassette|MC]]'),
			(u'[[Single]]', u'[[Single (Musik)|Single]]'),
		],
		'exceptions': {
			'inside-tags': [
				'hyperlink',
			]
		}
	},

	# format of dates of birth and death, for de:
	# python replace.py -fix:datum -ref:Vorlage:Personendaten
	'datum': {
		'regex': True,
		'msg': {
			'de': u'Bot: Korrigiere Datumsformat',
		},
		'replacements': [
			# space after birth sign w/ year
			#(u'\(\*(\d{3,4})', u'(* \\1'),
			## space after death sign w/ year
			#(u'†(\d{3,4})', u'† \\1'),
			#(u'&dagger;(\d{3,4})', u'† \\1'),
			## space after birth sign w/ linked date
			#(u'\(\*\[\[(\d)', u'(* [[\\1'),
			## space after death sign w/ linked date
			#(u'†\[\[(\d)', u'† [[\\1'),
			#(u'&dagger;\[\[(\d)', u'† [[\\1'),
			(u'\[\[(\d+\. (?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)) (\d{1,4})\]\]', u'[[\\1]] [[\\2]]'),
		],
		'exceptions': {
			'inside': [
				r'[[20. Juli 1944]]',
				r'[[17. Juni 1953]]',
				r'[[11. September 2001]]',
			],
		}
	},

	'isbn': {
		'regex': True,
		'msg': {
			'de': u'Bot: Korrigiere ISBN-Format',
			'en': u'Robot: Fixing ISBN format',
                        'he': u'בוט: מתקן פורמט ISBN',
			'es': u'Arreglando formato ISBN',
		},
		'replacements': [
			# colon
			(r'ISBN: (\d+)', r'ISBN \1'),
			# Spaces, dashes, or dots instead of hyphens as separators,
			# or spaces between digits and separators.
			# Note that these regular expressions also match valid ISBNs, but
			# these won't be changed.
			(ur'ISBN (978|979) *[\- –\.] *(\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d)(?!\d)', r'ISBN \1-\2-\3-\4-\5'), # ISBN13
			(r'ISBN (\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d|X|x)(?!\d)', r'ISBN \1-\2-\3-\4'), # ISBN10
		],
		'exceptions': {
			'inside-tags': [
				'comment',
			],
			'inside': [
				r'ISBN (\d(-?)){12}\d',    # matches valid ISBN-13s
				r'ISBN (\d(-?)){9}[\dXx]', # matches valid ISBN-10s
			],
		}
	},

	#Corrections for Arabic Wikipedia
	#And any Arabic wiki.
	#python replace.py -always -start:! -fix:correct-ar
	'correct-ar': {
		'regex': False,
		'msg': {
			'ar':u'تدقيق إملائي. 88 كلمة مستهدفة حاليًا.',
		},
		'replacements': [
			(u' ,', u' ،'),
			(u' إمرأة ', u' امرأة '),
			(u' الى ', u' إلى '),
			(u' إسم ', u' اسم '),
			(u' الأن ', u' الآن '),
			(u' اول ', u' أول '),
			(u' الة ', u' آلة '),
			(u' فى ', u' في '),
			(u' اثقل ', u' أثقل '),
			(u' إبن ', u' ابن '),
			(u' إبنة ', u' ابنة '),
			(u' إقتصاد ', u' اقتصاد '),
			(u' إجتماع ', u' اجتماع '),
			(u' انجيل ', u' إنجيل '),
			(u' اجماع ', u' إجماع '),
			(u' امريكا ', u' أمريكا '),
			(u' اوروبا ', u' أوروبا '),
			(u' انجلترا ', u' إنجلترا '),
			(u' اكتوبر ', u' أكتوبر '),
			(u' اسرائيل ', u' إسرائيل '),
			(u' المانيا ', u' ألمانيا '),
			(u' ايطاليا ', u' إيطاليا '),
			(u' ايران ', u' إيران '),
			(u' إستخراج ', u' استخراج '),
			(u' إستعمال ', u' استعمال '),
			(u' إستبدال ', u' استبدال '),
			(u' إشتراك ', u' اشتراك '),
			(u' إستعادة ', u' استعادة '),
			(u' إستقلال ', u' استقلال '),
			(u' إنتقال ', u' انتقال '),
			(u' إتحاد ', u' اتحاد '),
			(u' املاء ', u' إملاء '),
			(u' إستخدام ', u' استخدام '),
			(u' أحدى ', u' إحدى '),
			(u' لاكن ', u' لكن '),
			(u' الاردن ', u' الأردن '),
			(u' إثنان ', u' اثنان '),
			(u' شيئ ', u' شيء '),
			(u' إحتياط ', u' احتياط '),
			(u' إقتباس ', u' اقتباس '),
			(u' الامارات ', u' الإمارات '),
			(u' اكثر ', u' أكثر '),
			(u' افضل ', u' أفضل '),
			(u' اكبر ', u' أكبر '),
			(u' اشهر ', u' أشهر '),
			(u' ادارة ', u' إدارة '),
			(u' ابناء ', u' أبناء '),
			(u' الانصار ', u'  الأنصار '),
			(u' اشارة ', u' إشارة '),
			(u' إقرأ ', u' اقرأ '),
			(u' إمتياز ', u' امتياز '),
			(u' ارق ', u' أرق '),
			(u' أرثوذوكس ', u' أرثوذكس '),
			(u' الأرثوذوكس ', u' الأرثوذكس '),
			(u' أرثوذوكسية ', u' أرثوذكسية '),
			(u' الأرثوذوكسية ', u' الأرثوذكسية '),
			(u' الأرثوذوكسي ', u' الأرثوذكسي '),
			(u' ارثوذوكس ', u' أرثوذكس '),
			(u' ارثوذوكسي ', u' أرثوذكسي '),
			(u' ارثوذوكسية ', u' أرثوذكسية '),
			(u' الارثوذوكسية ', u' الأرثوذكسية '),
			(u' اللة ', u' الله '),
			(u' إختبار ', u' اختبار '),
			(u'== روابط خارجية ==', u'== وصلات خارجية =='),
			(u'==روابط خارجية==', u'== وصلات خارجية =='),
			(u' ارسال ', u' إرسال '),
			(u' إتصالات ', u' اتصالات '),
			(u' اسامة ', u' أسامة '),
			(u' ابراهيم ', u' إبراهيم '),
			(u' اسماعيل ', u' إسماعيل '),
			(u' ايوب ', u' أيوب '),
			(u' ايمن ', u' أيمن '),
			(u' ابو ', u' أبو '),
			(u' ابا ', u' أبا '),
			(u' اخو ', u' أخو '),
			(u' اخا ', u' أخا '),
			(u' اخي ', u' أخي '),
			(u' احد ', u' أحد '),
			(u' اربعاء ', u' أربعاء '),
			(u' اهم ', u' أهم '),
			(u' اوزبكستان ', u' أوزبكستان '),
			(u' اذربيجان ', u' أذربيجان '),
			(u' افغانستان ', u' أفغانستان '),
			(u' امجد ', u' أمجد '),
			(u' اوسط ', u' أوسط '),
			(u' اشقر ', u' أشقر '),
			(u' انور ', u' أنور '),
			(u' اصعب ', u' أصعب '),
			(u' اسهل ', u' أسهل '),
		]
	},
}
