#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This script keeps track of image deletions and delinks removed files 
from (any) wiki. Usage
on protected pages or pages containing blacklisted external links cannot
be processed.

This script is run by [[commons:User:Siebrand]] on the toolserver. It should
not be run by other users without prior contact.

Although the classes are called CommonsDelinker and Delinker, it is in fact
a general delinker/replacer, also suitable for local use.

Please refer to delinker.txt for full documentation.
"""
#
# 
# (C) Kyle/Orgullomoore, 2006-2007
# (C) Siebrand Mazeland, 2006-2007
# (C) Bryan Tong Minh, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
# This script requires MySQLdb and simplejson. Tested with:
# * Python 2.4.4, MySQLdb 1.2.1_p, simplejson 1.3
# * Python 2.5, MySQLdb 1.2.2, simplejson 1.5 (recommended)
# TODO:
# * Don't replace within <nowiki /> tags
# * Make as many config settings site dependend
# BUGS:
# * There is a problem with images in the es.wikisource project namespace.
#   The exact problem is described somewhere in Bryan's IRC logs, but it is
#   unknown where exactly.

import sys, os, threading, time
import traceback
import re, cgitb

import threadpool
import checkusage

import wikipedia
import config
	
def wait_callback(object):
	output(u'Connection has been lost in %s. Attempting reconnection.' % repr(object), False)
	if hasattr(object, 'error'):
		output(u'Error was %s: %s' % tuple(object.error))
def universal_unicode(s):
	if type(s) is str:
		return s.decode('utf-8', 'ignore')
	return unicode(s)
def connect_database():
	engine = config.CommonsDelinker['sql_engine']
	kwargs = config.CommonsDelinker['sql_config'].copy()
	if engine == 'mysql':
		import mysql_autoconnection
		# This setting is required for MySQL
		kwargs['charset'] = 'utf8'
		# Work around for a bug in MySQLdb 1.2.1_p. This version will
		# set use_unicode for all connections to the value of the first
		# initialized connection. This bug is not relevant for MySQLdb
		# versions 1.2.2 and upwards. The connection character set must
		# be set to utf8 however, to prevent INSERTs to be converted to
		# the standard MySQL character set.
		kwargs['use_unicode'] = False
		kwargs['callback'] = wait_callback
		
		return mysql_autoconnection.connect(**kwargs)
	# TODO: Add support for sqlite3
	raise RuntimeError('Unsupported database engine %s' % engine)

class Delinker(threadpool.Thread):
	# TODO: Method names could use some clean up
	def __init__(self, pool, CommonsDelinker):
		threadpool.Thread.__init__(self, pool)
		self.CommonsDelinker = CommonsDelinker
		self.sql_layout = self.CommonsDelinker.config.get('sql_layout', 'new')
		
	def delink_image(self, image, usage, timestamp, admin, reason, replacement = None):
		""" Performs the delink for image on usage. """
		output(u'%s Usage of %s: %s' % (self, image, usage))
		
		skipped_images = {}
		for (lang, family), pages in usage.iteritems():
			site = self.CommonsDelinker.get_site(lang, family)
			
			try:
				summary = self.get_summary(site, image, admin, reason, replacement)
				
				for page_namespace, page_title, title in pages:
					if (site.lang, site.family.name) == (self.CommmonsDelinker.site.lang,
							self.CommmonsDelinker.site.family.name) and \
							(page_namespace, page_title) == (6, image):
						continue
						
					if self.CommonsDelinker.set_edit(str(site), title):
						# The page is currently being editted. Postpone.
						if (lang, family) not in skipped_images:
							skipped_images[(lang, family)] = []
						skipped_images[(lang, family)].append(
							(page_namespace, page_title, title))
					else:
						# Delink the image
						output(u'%s Delinking %s from %s' % (self, image, site))
						
						try:
							result = self.replace_image(image, site, title, summary, replacement)
						finally:
							self.CommonsDelinker.unset_edit(str(site), title)
						
						# Add to logging queue
						if self.sql_layout == 'new':
							self.CommonsDelinker.Loggers.append((timestamp, image, 
								site.lang, site.family.name, page_namespace, page_title,
								result, replacement))
						else:
							self.CommonsDelinker.Loggers.append((timestamp, image, site.hostname(), 
								page_namespace, page_title, result, replacement))
			finally:
				self.CommonsDelinker.unlock_site(site)
		
		if skipped_images:
			time.sleep(self.CommonsDelinker.config['timeout'])
			return self.delink_image(image, skipped_images, timestamp, admin, reason, replacement)
		elif replacement:
			# Let them know that we are done replacing.
			self.CommonsDelinker.Loggers.append((timestamp, image, replacement))
			
	def replace_image(self, image, site, page_title, summary, replacement = None):
		""" The actual replacement. Giving None as argument for replacement
		will delink instead of replace."""
		
		page = wikipedia.Page(site, page_title)
		
		# TODO: Per site config.
		if page.namespace() in self.CommonsDelinker.config['delink_namespaces']:
			try:
				text = page.get(nofollow_redirects = True)
			except wikipedia.NoPage:
				return 'failed'
			new_text = text
			
			def create_regex(s):
				s = re.escape(s)
				return ur'(?:[%s%s]%s)' % (s[0].upper(), s[0].lower(), s[1:])
			def create_regex_i(s):
				return ur'(?:%s)' % u''.join([u'[%s%s]' % (c.upper(), c.lower()) for c in s])
			
			namespaces = ('Image', 'Media') + site.namespace(6, all = True) + site.namespace(-2, all = True)
			r_namespace = ur'\s*(?:%s)\s*\:\s*' % u'|'.join(map(create_regex_i, namespaces))
			# Note that this regex creates a group!
			r_image = u'(%s)' % create_regex(image).replace(r'\_', '[ _]')
			
			def simple_replacer(match):
				if replacement == None:
					return u''
				else:
					groups = list(match.groups())
					groups[1] = replacement
					return u''.join(groups)
					
			# Previously links in image descriptions will cause 
			# unexpected behaviour: [[Image:image.jpg|thumb|[[link]] in description]]
			# will truncate at the first occurence of ]]. This cannot be
			# fixed using one regular expression.
			# This means that all ]] after the start of the image
			# must be located. If it then does not have an associated
			# [[, this one is the closure of the image.
			
			r_simple_s = u'(\[\[%s)%s' % (r_namespace, r_image)
			r_s = '\[\['
			r_e = '\]\]'
			# First determine where wikilinks start and end
			image_starts = [match.start() for match in re.finditer(r_simple_s, text)]
			link_starts = [match.start() for match in re.finditer(r_s, text)]
			link_ends = [match.end() for match in re.finditer(r_e, text)]
				
			r_simple = u'(\[\[%s)%s(.*)' % (r_namespace, r_image)
			replacements = []
			for image_start in image_starts:
				current_link_starts = [link_start for link_start in link_starts 
					if link_start > image_start]
				current_link_ends = [link_end for link_end in link_ends 
					if link_end > image_start]
				end = image_start
				if current_link_ends: end = current_link_ends[0]
				
				while current_link_starts and current_link_ends:
					start = current_link_starts.pop(0)
					end = current_link_ends.pop(0)
					if end <= start and end > image_start:
						# Found the end of the image
						break
				
				# Add the replacement to the todo list. Doing the
				# replacement right know would alter the indices.
				replacements.append((new_text[image_start:end],
					re.sub(r_simple, simple_replacer, 
					new_text[image_start:end])))
			
			# Perform the replacements
			for old, new in replacements:
				if old: new_text = new_text.replace(old, new)
			
			# Remove the image from galleries
			r_galleries = ur'(?s)(\<%s\>)(.*?)(\<\/%s\>)' % (create_regex_i('gallery'), 
				create_regex_i('gallery'))
			r_gallery = ur'(?m)^((?:%s)?)%s(\s*(?:\|.*?)?\s*)$' % (r_namespace, r_image)
			def gallery_replacer(match):
				return ur'%s%s%s' % (match.group(1), re.sub(r_gallery, 
					simple_replacer, match.group(2)), match.group(3))
			new_text = re.sub(r_galleries, gallery_replacer, new_text)
			
			if text == new_text:
				# All previous steps did not work, so the image is
				# likely embedded in a complicated template.
				r_templates = ur'(?s)(\{\{.*?\}\})'
				r_complicated = u'(?s)((?:%s)?)%s' % (r_namespace, r_image)
				
				def template_replacer(match):
					return re.sub(r_complicated, simple_replacer, match.group(1))
				new_text = re.sub(r_templates, template_replacer, text)
			
			if text != new_text:
				# Save to the wiki
				# Code for checking user page existance has been moved
				# to summary() code, to avoid checking the user page
				# for each removal.
				try:
					if config.CommonsDelinker.get('save_diff', False):
						# Save a diff
						import difflib
						diff = difflib.context_diff(
							text.encode('utf-8').splitlines(True),
							new_text.encode('utf-8').splitlines(True))
						f = open((u'diff/%s-%s-%s.txt' % (page_title.replace('/', '-'),
							site.dbName(), page.editTime())).encode('utf-8', 'ignore'), 'w')
						f.writelines(diff)
						f.close()
					
					if self.CommonsDelinker.config.get('edit', True) and not \
							((self.CommonsDelinker.site.lang == 'commons') ^ \
							(config.usernames.get('commons', {}).get(
							'commons') == 'CommonsDelinker')):
						page.put(new_text, summary)
					return 'ok'
				except wikipedia.EditConflict:
					# Try again
					output(u'Got EditConflict trying to remove %s from %s:%s.' % \
						(image, site, page_title))
					return self.replace_image(image, site, page_title, summary, replacement = None)
				except (wikipedia.LockedPage, wikipedia.PageNotSaved):
					return 'failed'
			else:
				return 'skipped'
		return 'skipped'
			
		
		
	def do(self, args):
		try:
			self.delink_image(*args)
		except:
			output(u'An exception occured in %s' % self, False)
			traceback.print_exc(file = sys.stderr)
		
	def get_summary(self, site, image, admin, reason, replacement):
		""" Get the summary template and substitute the 
		correct values."""
		# FIXME: Don't insert commons: on local delink
		# FIXME: Hardcode is EVIL
		if replacement:
			tlp = self.CommonsDelinker.SummaryCache.get(site, 'replace-I18n')
		else:
			tlp = self.CommonsDelinker.SummaryCache.get(site, 'summary-I18n')
		
		tlp = tlp.replace('$1', image)
		if replacement:
			tlp = tlp.replace('$2', replacement)
			tlp = tlp.replace('$3', unicode(admin))
			tlp = tlp.replace('$4', unicode(reason).replace('[[', '[[w:commons:'))
		else:
			tlp = tlp.replace('$2', unicode(admin))
			tlp = tlp.replace('$3', reason.replace('[[', '[[w:commons:'))
		
		return tlp
		
class SummaryCache(object):
	""" Object to thread-safe cache summary templates. """
	def __init__(self, CommonsDelinker):
		self.summaries = {}
		self.lock = threading.Lock()
		self.CommonsDelinker = CommonsDelinker
		
	def get(self, site, type, key = None):
		# This can probably also provide something for 
		# localised settings, but then it first needs to 
		# check whether the page is sysop only.
		if not key:
			key = str(site)
			
		self.lock.acquire()
		try:
			if type not in self.summaries:
				self.summaries[type] = {}
			if key in self.summaries[type]:
				if (time.time() - self.summaries[type][key][1]) < \
						self.CommonsDelinker.config['summary_cache']:
					# Return cached result
					return self.summaries[type][key][0]
					
			output(u'%s Fetching new summary for %s' % (self, site))
			
			# FIXME: evil
			if self.CommonsDelinker.config['global']:
				self.check_user_page(site)
			page = wikipedia.Page(site, '%s%s' % \
				(self.CommonsDelinker.config['local_settings'], type))
			try:
				# Fetch the summary template, follow redirects
				i18n = page.get(get_redirect = True)
				self.summaries[type][key] = (i18n, time.time())
				return i18n
			except wikipedia.NoPage:
				pass
		finally:
			self.lock.release()
			
		# No i18n available, but it may be available in the wikipedia
		# of that language. Only do so for wiktionary, wikibooks,
		# wikiquote, wikisource, wikinews, wikiversity
		# This will cause the bot to function even on special wikis
		# like mediawiki.org and meta and species.
		output(u'%s Using default summary for %s' % (self, site))
				
		if site.family.name != 'wikipedia' and self.CommonsDelinker.config['global']:
			if site.family.name in ('wiktionary', 'wikibooks', 'wikiquote', 
					'wikisource', 'wikinews', 'wikiversity'):
				newsite = self.CommonsDelinker.get_site(site.lang, 
					wikipedia.Family('wikipedia'))
				return self.get(newsite, type, key = key)
		return self.CommonsDelinker.config['default_settings'].get(type, '')
				
	def check_user_page(self, site):
		"Check whether a userpage exists. Only used for CommonsDelinker."
		try:
			# Make sure the userpage is not empty
			# Note: if wikis delete the userpage, it's there own fault
			filename = 'canedit.cdl'
			try:
				f = open(filename, 'r')
			except IOError:
				# Don't care
				return
			ftxt = f.read()
			f.close()
			if not '#' + str(site) in ftxt:
				username = config.usernames[site.family.name][site.lang] 
				
				userpage = wikipedia.Page(site, 'User:' + username)
				# Removed check for page existence. If it is not in our 
				# database we can safely assume that we have no user page
				# there. In case there is, we will just overwrite it once.
				# It causes no real problems, but it is one call to the 
				# servers less.
				# TODO: Config setting?
				userpage.put('#REDIRECT [[m:User:CommonsDelinker]]', '')
				
				f = open(filename, 'a')
				f.write('#' + str(site))
				f.close()
		except wikipedia.LockedPage:
			# User page is protected, continue anyway
			pass	
			
class CheckUsage(threadpool.Thread):
	def __init__(self, pool, CommonsDelinker):
		threadpool.Thread.__init__(self, pool)
		self.CommonsDelinker = CommonsDelinker
		# Not really thread safe, but we should only do read operations...
		self.site = CommonsDelinker.site
		
	def run(self):
		self.connect()
		threadpool.Thread.run(self)
		
	def connect(self):
		config = self.CommonsDelinker.config
		if config['global']:
			# Note: global use requires MySQL
			self.CheckUsage = checkusage.CheckUsage(limit = sys.maxint,
				mysql_kwargs = config['sql_config'],
				use_autoconn = True, 
				http_callback = wait_callback,
				mysql_callback = wait_callback)
		else:
			self.CheckUsage = checkusage.CheckUsage(sys.maxint,
				http_callback = wait_callback, no_db = True)
		
		
	def check_usage(self, image, timestamp, admin, reason, replacement):
		""" Check whether this image needs to be delinked. """
		
		# Check whether the image still is deleted on Commons.
		# BUG: This also returns true for images with a page, but
		# without the image itself. Can be fixed by querying query.php
		# instead of api.php. Also should this be made as an exits() 
		# method of checkusage.CheckUsage?
		if self.site.shared_image_repository() != (None, None):
			shared_image_repository = self.CommonsDelinker.get_site(*self.site.shared_image_repository())
			try:
				if self.CheckUsage.exists(shared_image_repository, image) \
						and not bool(replacement):
					output(u'%s %s exists on the shared image repository!' % (self, image))
					return
			finally:
				self.CommonsDelinker.unlock_site(shared_image_repository)
		if self.CheckUsage.exists(self.site, image) and \
				not bool(replacement):
			output(u'%s %s exists again!' % (self, image))
			return
		
		
		if self.CommonsDelinker.config['global']:
			usage = self.CheckUsage.get_usage(image)
			usage_domains = {}
			
			count = 0
			# Sort usage per domain
			for (lang, family), (page_namespace, page_title, title) in usage:
				if (lang, family) not in usage_domains:
					usage_domains[(lang, family)] = []
				usage_domains[(lang, family)].append((page_namespace, page_title, title))
				count += 1
		else:
			#FIX!
			usage_domains = {(self.site.lang, self.site.family.name): 
				list(self.CheckUsage.get_usage_live(self.site, 
					image))}
			count = len(usage_domains[(self.site.lang, self.site.family.name)])
			
		output(u'%s %s used on %s pages' % (self, image, count))
		
		if count:
			# Pass the usage to the Delinker pool along with other arguments
			self.CommonsDelinker.Delinkers.append((image, usage_domains, 
				timestamp, admin, reason, replacement))
		elif replacement:
			# Record replacement done
			self.CommonsDelinker.Loggers.append((timestamp, image, replacement))
		
	def do(self, args):
		try:
			self.check_usage(*args)
		except:
			# Something unexpected happened. Report and die.
			output('An exception occured in %s' % self, False)
			traceback.print_exc(file = sys.stderr)
			self.exit()
			self.CommonsDelinker.thread_died()
		
class Logger(threadpool.Thread):
	def __init__(self, pool, CommonsDelinker):
		threadpool.Thread.__init__(self, pool)
		self.CommonsDelinker = CommonsDelinker
		self.sql_layout = self.CommonsDelinker.config.get('sql_layout', 'new')
		
	def run(self):
		self.connect()
		threadpool.Thread.run(self)
		
	def connect(self):
		self.database = connect_database()
		self.cursor = self.database.cursor()
		
		
	def log_result_legacy(self, timestamp, image, domain, namespace, page, status = "ok", newimage = None):
		# TODO: Make sqlite3 ready
		
		# The original delinker code cached log results,
		# in order to limit the number of connections.
		# However, since we are now using persistent
		# connections, we can safely insert the result
		# on the fly.
		output(u'%s Logging %s for %s on %s' % (self, repr(status), image, page))
		
		# There is no need to escape each parameter if
		# a parametrized call is made.		
		self.cursor.execute("""INSERT INTO %s (timestamp, img, wiki, page_title,
	namespace, status, newimg) VALUES
	(%%s, %%s, %%s, %%s, %%s, %%s, %%s)""" % self.CommonsDelinker.config['log_table'],
			(timestamp, image, domain, page, namespace, status, newimage))
		self.database.commit()
			
	def log_result_new(self, timestamp, image, site_lang, site_family, 
			page_namespace, page_title, status = 'ok', new_image = None):
				
		output(u'%s Logging %s for %s on %s' % (self, repr(status), image, page_title))

		self.cursor.execute("""INSERT INTO %s (timestamp, image, site_lang, site_family,
	page_namespace, page_title, status, new_image) VALUES
	(%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)""" % self.CommonsDelinker.config['log_table'],
			(timestamp, image, site_lang, site_family, page_namespace, page_title, 
				status, new_image))
		self.database.commit()
			
	def log_replacement(self, timestamp, old_image, new_image):
		# TODO: Same as above
		
		output(u'Replacing %s by %s done' % (old_image, new_image))
		self.cursor.execute("""UPDATE %s SET status = 'done' WHERE 
			timestamp = %%s AND old_image = %%s AND 
			new_image = %%s""" % self.CommonsDelinker.config['replacer_table'],
			(timestamp, old_image, new_image))
		self.database.commit()
		
	def do(self, args):
		try:
			if len(args) == 3:
				self.log_replacement(*args)
			else:
				if self.sql_layout == 'new':
					self.log_result_new(*args)
				else:
					self.log_result_legacy(*args)
		except:
			# Something unexpected happened. Report and die.
			output('An exception occured in %s' % self, False)
			traceback.print_exc(file = sys.stderr)
			self.exit()
			self.CommonsDelinker.thread_died()
			
class CommonsDelinker(object):
	def __init__(self):
		self.config = config.CommonsDelinker
		self.site = wikipedia.getSite()
		self.site.forceLogin()
		
		# Initialize workers
		self.CheckUsages = threadpool.ThreadPool(CheckUsage)
		[self.CheckUsages.add_thread(self) for i in xrange(self.config['checkusage_instances'])]
		
		self.Delinkers = threadpool.ThreadPool(Delinker)
		[self.Delinkers.add_thread(self) for i in xrange(self.config['delinker_instances'])]
			
		self.Loggers = threadpool.ThreadPool(Logger)
		[self.Loggers.add_thread(self) for i in xrange(self.config['logger_instances'])]
		
		self.http = checkusage.HTTP(self.site.hostname())
		
		self.edit_list = []
		self.editLock = threading.Lock()
		
		self.sites = {}
		self.siteLock = threading.Lock()
		
		self.SummaryCache = SummaryCache(self)
		
		if self.config.get('enable_replacer', False):
			self.connect_mysql()
			
		if self.config.get('no_sysop', False):
			# Don't edit as sysop
			if hasattr(config, 'sysopnames'):
				config.sysopnames = dict([(fam, {}) for fam in config.sysopnames.keys()])
				
		self.last_check = time.time()
		
		#if 'bot' in self.site.userGroups:
		#	self.log_limit = '5000'
		#else:
		#	self.log_limit = '500'
		self.log_limit = '500'
		
	def connect_mysql(self):
		self.database = connect_database()
		self.cursor = self.database.cursor()
		
	def set_edit(self, domain, page):
		""" Make sure the bot does not create edit 
		conflicts with itself."""
		self.editLock.acquire()
		being_editted = (domain, page) in self.edit_list
		if not being_editted:
			self.edit_list.append((domain, page))
		self.editLock.release()
		return being_editted
	def unset_edit(self, domain, page):
		""" Done editting. """
		self.editLock.acquire()
		self.edit_list.remove((domain, page))
		self.editLock.release()
		
	def get_site(self, code, fam):
		# Threadsafe replacement of wikipedia.getSite 
		key = '%s:%s' % (code, fam)
		self.siteLock.acquire()
		try:
			if key not in self.sites:
				self.sites[key] = []
			for site, used in self.sites[key]:
				if not used:
					self.sites[key][self.sites[key].index((site, False))] = (site, True)
					return site
			site = wikipedia.Site(code, fam)
			self.sites[key].append((site, True))
			return site
		finally:
			self.siteLock.release()
	def unlock_site(self, site):
		key = '%s:%s' % (site.lang, site.family.name)
		self.siteLock.acquire()
		try:
			self.sites[key][self.sites[key].index((site, True))] = (site, False)
		finally:
			self.siteLock.release()
		
		
	def read_deletion_log(self):
		ts_format = '%Y-%m-%dT%H:%M:%SZ'
		wait = self.config['delink_wait']
		exclusion = self.config['exclude_string']
		
		ts_from = self.last_check
		# Truncate -> int()
		ts_end = int(time.time())
		self.last_check = ts_end
		
		# Format as a Mediawiki timestamp and substract a
		# certain wait period.
		ts_from_s = time.strftime(ts_format, time.gmtime(ts_from - wait + 1))
		ts_end_s = time.strftime(ts_format, time.gmtime(ts_end - wait))
		
		try:
			# Assume less than 500 deletion have been made between
			# this and the previous check of the log. If this is not 
			# the case, timeout should be set lower.
			result = self.http.query_api(self.site.hostname(), self.site.apipath(),
				action = 'query', list = 'logevents', letype = 'delete', 
				lelimit = self.log_limit, lestart = ts_from_s, leend = ts_end_s, 
				ledir = 'newer')
			logevents = result['query']['logevents']
		except Exception, e:
			if type(e) in (SystemError, KeyboardInterrupt): raise			
			# Something happened, but since it is a network error,
			# it will not be critical. In order to prevent data loss
			# the last_check timestamp has to be set correctly.
			self.last_check = ts_from
			output('Warning! Unable to read deletion logs', False)
			output('%s: %s' % (e.__class__.__name__, str(e)), False)
			return time.sleep(self.config['timeout'])
		
		for logevent in logevents:
			if logevent['ns'] == 6 and logevent['action'] == 'delete':
				if exclusion not in logevent.get('comment', ''):
					timestamp = logevent['timestamp']
					timestamp = timestamp.replace('-', '')
					timestamp = timestamp.replace(':', '')
					timestamp = timestamp.replace('T', '')
					timestamp = timestamp.replace('Z', '')
					
					output(u'Deleted image: %s' % logevent['title'])
					self.CheckUsages.append((checkusage.strip_ns(logevent['title']),
						timestamp, logevent['user'], logevent.get('comment', ''),
						None))
				else:
					output(u'Skipping deleted image: %s' % logevent['title'])
					
	def read_replacement_log(self):
		# TODO: Make sqlite3 ready
		# TODO: Single process replacer
		update = """UPDATE %s SET status = %%s WHERE id = %%s""" % \
			self.config['replacer_table']
		self.cursor.execute("""SELECT id, timestamp, old_image, new_image, user, comment
			FROM %s WHERE status = 'pending'""" % self.config['replacer_table'])
		result = ([universal_unicode(s) for s in i] for i in self.cursor.fetchall())


		for id, timestamp, old_image, new_image, user, comment in result:
			# TODO: remove code; should now be part of the replacer
			if (not old_image.lower().endswith('.svg')) and \
					new_image.lower().endswith('.svg'):
				output(u'Refused to replace %s by %s' % (old_image, new_image))
				self.cursor.execute(update, ('refused', id))
			else:
				self.CheckUsages.append((old_image, timestamp, user, comment, new_image))
				output(u'Replacing %s by %s'  % (old_image, new_image))
				self.cursor.execute(update, ('ok', id))
			
		self.database.commit()
			
	def start(self):
		# Gracefully exit all threads on SIG_INT or SIG_TERM
		threadpool.catch_signals()
		
		# Start threads
		self.Loggers.start()
		self.Delinkers.start()
		self.CheckUsages.start()
		
		# Give threads some time to initialize
		time.sleep(self.config['timeout'])
		output(u'All workers started')
		
		if self.config.get('monitor'):
			# For debugging a special monitor may be used.
			# This monitor is optional, and will be used if
			# a configuration variable monitor is set and True.
			import monitor
			monitor.Monitor(self).start()
		
		# Main loop
		while True:
			if self.config.get('enable_delinker', True):
				if 'deletion_log_table' in self.config:
					if not self.read_deletion_log_db():
						self.read_deletion_log()
				else:
					self.read_deletion_log()
			if self.config.get('enable_replacer', False):
				self.read_replacement_log()
				
			time.sleep(self.config['timeout'])
			
	def thread_died(self):
		# A thread died, it may be possible that we cannot 
		# function any more. Currently only for CheckUsages
		# and Loggers. Delinkers should not be able to die.
		cu = 0
		self.CheckUsages.jobLock.acquire()
		for thread in self.CheckUsages.threads:
			if thread.isAlive() and not thread.quit:
				cu += 1
		self.CheckUsages.jobLock.release()
		lg = 0
		self.Loggers.jobLock.acquire()
		for thread in self.Loggers.threads:
			if thread.isAlive() and not thread.quit:
				lg += 1
		unlogged = self.Loggers.jobQueue[:]
		self.Loggers.jobLock.release()
		
		# We can no longer function if we have only one
		# CheckUsage or zero Loggers available. 
		# TODO: config settings?
		if cu <= 1:
			output(u'ERROR!!! Too few CheckUsages left to function', False)
			threadpool.terminate()
		if lg <= 0:
			output(u'ERROR!!! Too few Loggers left to function', False)
			print >>sys.stderr, 'Currently unlogged:', unlogged
			threadpool.terminate()
			
def output(message, toStdout = True):
	message = time.strftime('[%Y-%m-%d %H:%M:%S] ') + message
	wikipedia.output(message, toStdout = toStdout)
	if toStdout:
		sys.stdout.flush()
	else:
		sys.stderr.flush()
			
if __name__ == '__main__':	
	output(u'Running ' + __version__)
	CD = CommonsDelinker()
	output(u'This bot runs from: ' + str(CD.site))
	
	re._MAXCACHE = 4
	
	args = wikipedia.handleArgs()
	if '-since' in args:
		# NOTE: Untested
		ts_format = '%Y-%m-%d %H:%M:%S'
		try:
			since = time.strptime(
				args[args.index('-since') + 1], 
				ts_format)
		except ValueError:
			if args[args.index('-since') + 1][0] == '[' and \
					len(args) != args.index('-since') + 2:
				since = time.strptime('%s %s' % \
					args[args.index('-since') + 1],
					'[%s]' % ts_format)
			else:
				raise ValueError('Incorrect time format!')
		output(u'Reading deletion log since [%s]' %\
			time.strftime(ts_format, since))
		CD.last_check = time.mktime(since)
	
	try:
		try:
			CD.start()
		except Exception, e:
			if type(e) not in (SystemExit, KeyboardInterrupt):
				output('An exception occured in the main thread!', False)
				traceback.print_exc(file = sys.stderr)
				threadpool.terminate()
	finally:
		output(u'Stopping CommonsDelinker')
		wikipedia.stopme()
		# Flush the standard streams
		sys.stdout.flush()
		sys.stderr.flush()
