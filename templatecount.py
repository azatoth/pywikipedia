"""
This script will display the list of pages transcluding a given list of templates.
It can also be used to simply count the number of pages (rather than listing each
individually).

Syntax: python templatecount.py command [arguments]

Command line options:

-count        Counts the number of times each template (passed in as an argument)
              is transcluded.
-list         Gives the list of all of the pages transcluding the templates (rather
              than just counting them).
-namespace:   Filters the search to a given namespace.  If this is specified
              multiple times it will search all given namespaces

Examples:

Counts how many times {{ref}} and {{note}} are transcluded in articles.

     python templatecount.py -count -namespace:0 ref note

Lists all the category pages that transclude {{cfd}} and {{cfdu}}.

     python templatecount.py -list -namespace:14 cfd cfdu

"""

import wikipedia, config
import replace, pagegenerators
import re, sys, string
import datetime

class TemplateCountRobot:
	#def __init__(self):
		#Nothing
	def countTemplates(self, templates, namespaces):
		mysite = wikipedia.getSite()
		finalText = [u'Number of transclusions per template',u'------------------------------------']
		total = 0
		for template in templates:
			gen = pagegenerators.ReferringPageGenerator(wikipedia.Page(mysite, mysite.template_namespace() + ':' + template), onlyTemplateInclusion = True)
			if namespaces:
				gen = pagegenerators.NamespaceFilterPageGenerator(gen, namespaces)
			count = 0
			for page in gen:
				count = count + 1
			finalText.append(u'%s: %d' % (template, count))
			total = total + count
		for line in finalText:
			wikipedia.output(line)
		wikipedia.output(u'TOTAL: %d' % total)
		wikipedia.output(u'Report generated on %s' % datetime.datetime.utcnow().isoformat())

	def listTemplates(self, templates, namespaces):
		mysite = wikipedia.getSite()
		count = 0
		finalText = [u'List of pages transcluding templates:']
		for template in templates:
			finalText.append(u'* %s' % template)
		finalText.append(u'------------------------------------')
		for template in templates:
			gen = pagegenerators.ReferringPageGenerator(wikipedia.Page(mysite, mysite.template_namespace() + ':' + template), onlyTemplateInclusion = True)
			if namespaces:
				gen = pagegenerators.NamespaceFilterPageGenerator(gen, namespaces)
			for page in gen:
				finalText.append(u'%s' % page.title())
				count = count + 1
		finalText.append(u'Total page count: %d' % count)
		for line in finalText:
			wikipedia.output(line)
		wikipedia.output(u'Report generated on %s' % datetime.datetime.utcnow().isoformat())

def main():
	operation = "None"
	doCount = False
	doList = False
	argsList = []
	namespaces = []

	for arg in wikipedia.handleArgs():
		if arg == '-count':
			operation = "Count"
		elif arg == '-list':
			operation = "List"
		elif arg.startswith('-namespace:'):
			namespaces.append(int(arg[len('-namespace:'):]))
		else:
			argsList.append(arg)

	if operation == "None":
		wikipedia.output(u'You did not give me anything to do, quitting.')
	else:
		robot = TemplateCountRobot()
		if not argsList:
			argsList = ['ref', 'note', 'ref label', 'note label']
		if operation == "Count":
			robot.countTemplates(argsList, namespaces)
		elif operation == "List":
			robot.listTemplates(argsList, namespaces)

if __name__ == "__main__":
	try:
		main()
	finally:
		wikipedia.stopme()
