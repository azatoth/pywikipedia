# -*- coding: utf-8 -*-

"""
Scripts to manage categories.

Syntax: python category.py action [-option]

where action can be one of these:
 * add      - mass-add a category to a list of pages
 * remove   - remove category tag from all pages in a category
 * move     - move all pages in a category to another category
 * tidy     - tidy up a category by moving its articles into subcategories
 * tree     - show a tree of subcategories of a given category
 * listify  - make a list of all of the articles that are in a category

and option can be one of these:
 * -person     - sort persons by their last name (for action 'add')
 * -rebuild    - reset the database
 * -from:      - The category to move from (for the move option)
                 Also, the category to remove from in the remove option
                 Also, the category to make a list of in the listify option
 * -to:        - The category to move to (for the move option)
               - Also, the name of the list to make in the listify option
         NOTE: If the category names have spaces in them you may need to use a
         special syntax in your shell so that the names aren't treated as separate
         parameters.  For instance, in BASH, use single quotes, e.g. -from:'Polar bears'
 * -batch      - Don't prompt to delete emptied categories (do it automatically).
 * -summary:   - Pick a custom edit summary for the bot.
 * -inplace    - Use this flag to change categories in place rather than
                 rearranging them.
 * -delsum     - An option for remove, this specifies to use the custom edit
                 summary as the deletion reason (rather than a canned deletion reason)
 * -overwrite  - An option for listify, this overwrites the current page with the
                 list even if something is already there.
 * -showimages - An option for listify, this displays images rather than linking them
                 in the list.
 * -talkpages  - An option for listify, this outputs the links to talk pages of the
                 pages to be listified in addition to the pages themselves.
 * -recurse    - Recurse through all subcategories of categories.


For the actions tidy and tree, the bot will store the category structure locally
in category.dump. This saves time and server load, but if it uses these data
later, they may be outdated; use the -rebuild parameter in this case.

For example, to create a new category from a list of persons, type:

  python category.py add -person

and follow the on-screen instructions.


Or to do it all from the command-line, use the following syntax:

  python category.py move -from:US -to:'United States'

This will move all pages in the category US to the category United States.

"""

#
# (C) Rob W.W. Hooft, 2004
# (C) Daniel Herding, 2004
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#
import re, sys, string, pickle, bz2
import wikipedia, catlib, config, pagegenerators

# Summary messages
msg_add={
    'da':u'Robot: Tilføjer [[Kategori:%s]]',
    'de':u'Bot: Ergänze [[Kategorie:%s]]',
    'en':u'Adding [[Category:%s]]',
    'es':u'Bot: Añadida [[Categoría:%s]]',
    'id':u'Bot: Menambahkan [[Kategori:%s]]',
    'fi':u'Botti lisäsi luokkaan [[Luokka:%s]]',
    'fr':u'Robot : ajoute [[Catégorie:%s]]',
    'he':u'רובוט: מוסיף [[קטגוריה:%s]]',
    'ia':u'Robot: Addition de [[Categoria:%s]]',
    'is':u'Vélmenni: Bæti við [[Flokkur:%s]]',
    'lt':u'robotas: Pridedama [[Kategorija:%s]]',
    'nds':u'Kat-Bot: [[Kategorie:%s]] rin',
    'nl':u'Bot: [[Categorie:%s]] toegevoegd',
    'no':u'Robot: Legger til [[Kategori:%s]]',
    'pl':u'Robot dodaje [[Kategoria:%s]]',
    'pt':u'Bot: Adicionando [[Categoria:%s]]',
    'sr':u'Бот: Додаје [[Категорија:%s]]',
    'sv':u'Robot: Lägger till [[Kategori:%s]]',
    }

msg_change={
    'da':u'Robot: Ændrer %s',
    'de':u'Bot: Ändere %s',
    'en':u'Robot: Changing %s',
    'es':u'Bot: Cambiada %s',
    'id':u'Bot: Mengganti %s',
    'fi':u'Botti vaihtoi luokan %s',
    'fr':u'Robot : modifie [[%s]]',
    'he':u'רובוט: משנה %s',
    'ia':u'Robot: Modification de %s',
    'is':u'Vélmenni: Breyti flokknum [[Flokkur:%s]]',
    'lt':u'robotas: Keičiama %s',
    'nds':u'Kat-Bot: %s utwesselt',
    'nl':u'Bot: Wijziging %s',
    'no':u'Robot: Endrer %s',
    'pt':u'Bot: Modificando [[Categoria:%s]]',
    'pl':u'Robot przenosi %s',
    'sr':u'Бот: Измена категорије %s',
    'sv':u'Robot: Ändrar %s',
    }

deletion_reason_move = {
    'de':u'Bot: Kategorie wurde nach [[%s]] verschoben',
    'en':u'Robot: Category was moved to [[%s]]',
    'fr':u'Robot : catégorie déplacée sur [[%s]]',
    'he':u'רובוט: הקטגוריה הועברה לשם [[%s]]',
    'ia':u'Robot: Categoria transferite a [[%s]]',
    'id':u'Bot: Kategori dipindahkan ke [[%s]]',
    'lt':u'robotas: Kategorija pervadinta į [[%s]]',
    'nds':u'Kat-Bot: Kategorie na [[%s]] schaven',
    'nl':u'Bot: Categorie is hernoemd naar [[%s]]',
    'no':u'Robot: Kategorien ble flyttet til [[%s]]',
    'pt':u'Bot: Categoria [[%s]] foi movida',
    'pl':u'Robot przenosi kategorię do [[%s]]',
    'sr':u'Бот: Категорија премештена у [[%s]]',
    'sv':u'Robot: Kategori flyttades till [[%s]]',
    }

cfd_templates = {
    'en':['cfd', 'cfr', 'cfru', 'cfr-speedy', 'cfm', 'cfdu'],
    }

class CategoryDatabase:
    '''
    This is a temporary knowledge base saving for each category the contained
    subcategories and articles, so that category pages do not need to
    be loaded over and over again
    '''
    def __init__(self, rebuild = False, filename = 'category.dump.bz2'):
        if rebuild:
            self.rebuild()
        else:
            try:

                f = bz2.BZ2File(filename, 'r')
                wikipedia.output(u'Reading dump from %s' % filename)
                databases = pickle.load(f)
                f.close()
                # keys are categories, values are 2-tuples with lists as entries.
                self.catContentDB = databases['catContentDB']
                # like the above, but for supercategories
                self.superclassDB = databases['superclassDB']
                del databases
            except:
                # If something goes wrong, just rebuild the database
                self.rebuild()

    def rebuild(self):
        self.catContentDB={}
        self.superclassDB={}

    def getSubcats(self, supercat):
        '''
        For a given supercategory, return a list of Categorys for all its
        subcategories.
        Saves this list in a temporary database so that it won't be loaded from the
        server next time it's required.
        '''
        # if we already know which subcategories exist here
        if self.catContentDB.has_key(supercat):
            return self.catContentDB[supercat][0]
        else:
            subcatlist = supercat.subcategoriesList()
            articlelist = supercat.articlesList()
            # add to dictionary
            self.catContentDB[supercat] = (subcatlist, articlelist)
            return subcatlist

    def getArticles(self, cat):
        '''
        For a given category, return a list of Pages for all its articles.
        Saves this list in a temporary database so that it won't be loaded from the
        server next time it's required.
        '''
        # if we already know which articles exist here
        if self.catContentDB.has_key(cat):
            return self.catContentDB[cat][1]
        else:
            subcatlist = cat.subcategoriesList()
            articlelist = cat.articlesList()
            # add to dictionary
            self.catContentDB[cat] = (subcatlist, articlelist)
            return articlelist

    def getSupercats(self, subcat):
        # if we already know which subcategories exist here
        if self.superclassDB.has_key(subcat):
            return self.superclassDB[subcat]
        else:
            supercatlist = subcat.supercategoriesList()
            # add to dictionary
            self.superclassDB[subcat] = supercatlist
            return supercatlist

    def dump(self, filename = 'category.dump.bz2'):
        '''
        Saves the contents of the dictionaries superclassDB and catContentDB to disk.
        '''
        wikipedia.output(u'Dumping to %s, please wait...' % filename)
        f = bz2.BZ2File(filename, 'w')
        databases = {
            'catContentDB': self.catContentDB,
            'superclassDB': self.superclassDB
        }
        # store dump to disk in binary format
        try:
            pickle.dump(databases, f, protocol=pickle.HIGHEST_PROTOCOL)
        except pickle.PicklingError:
            pass
        f.close()

def sorted_by_last_name(catlink, pagelink):
        '''
        given a Category, returns a Category which has an explicit sort key which
        sorts persons by their last names.
        Trailing words in brackets will be removed.
        Example: If category_name is 'Author' and pl is a Page to
        [[Alexandre Dumas (senior)]], this function will return this Category:
        [[Category:Author|Dumas, Alexandre]]
        '''
        page_name = pagelink.title()
        site = pagelink.site()
        # regular expression that matches a name followed by a space and
        # disambiguation brackets. Group 1 is the name without the rest.
        bracketsR = re.compile('(.*) \(.+?\)')
        match_object = bracketsR.match(page_name)
        if match_object:
            page_name = match_object.group(1)
        split_string = page_name.split(' ')
        if len(split_string) > 1:
            # pull last part of the name to the beginning, and append the rest after a comma
            # e.g. "John von Neumann" becomes "Neumann, John von"
            sorted_key = split_string[-1] + ', ' + string.join(split_string[:-1], ' ')
            # give explicit sort key
            return wikipedia.Page(site, catlink.title() + '|' + sorted_key)
        else:
            return wikipedia.Page(site, catlink.title())

def add_category(sort_by_last_name = False):
    '''
    A robot to mass-add a category to a list of pages.
    '''
    print "This bot has two modes: you can add a category link to all"
    print "pages mentioned in a List that is now in another wikipedia page"
    print "or you can add a category link to all pages that link to a"
    print "specific page. If you want the second, please give an empty"
    print "answer to the first question."
    listpageTitle = wikipedia.input(u'Wiki page with list of pages to change:')
    site = wikipedia.getSite()
    pages = []
    if listpageTitle:
        try:
            listpage = wikipedia.Page(site, listpageTitle)
            pages = listpage.linkedPages()
        except wikipedia.NoPage:
            wikipedia.output(u'%s could not be loaded from the server.' % listpage.aslink())
        except wikipedia.IsRedirectPage:
            wikipedia.output(u'%s is a redirect to %s.' % (listpage.aslink(), listpage.getRedirectTarget()))
    else:
        referredPage = wikipedia.input(u'Wikipedia page that is now linked to:')
        page = wikipedia.Page(wikipedia.getSite(), referredPage)
        pages = [p for p in page.getReferences()]
    wikipedia.output(u'  ==> %i pages to process\n' % len(pages))
    if len(pages) > 0:
        newcatTitle = wikipedia.input(u'Category to add (do not give namespace):')
        if not wikipedia.getSite().nocapitalize:
            newcatTitle = newcatTitle[:1].capitalize() + newcatTitle[1:]

        # set edit summary message
        wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), msg_add) % newcatTitle)

        cat_namespace = wikipedia.getSite().category_namespaces()[0]

        answer = ''
        for page in pages:
            if answer != 'a':
                answer = ''

            while answer not in ('y','n','a'):
                answer = wikipedia.input(u'%s [y/n/a(ll)]:' % (page.aslink()))
                if answer == 'a':
                    confirm = ''
                    while confirm not in ('y','n'):
                        confirm = wikipedia.input(u'This should be used if and only if you are sure that your links are correct! Are you sure? [y/n]:')
                    if confirm == 'n':
                        answer = ''

            if answer == 'y' or answer == 'a':
                try:
                    cats = page.categories()
                except wikipedia.NoPage:
                    wikipedia.output(u"%s doesn't exist yet. Ignoring." % (page.title()))
                    pass
                except wikipedia.IsRedirectPage,arg:
                    redirTarget = wikipedia.Page(site,arg.args[0])
                    wikipedia.output(u"WARNING: %s is redirect to %s. Ignoring." % (page.title(), redirTarget.title()))
                else:
                    wikipedia.output(u"Current categories:")
                    for cat in cats:
                        wikipedia.output(u"* %s" % cat.title())
                    catpl = wikipedia.Page(site, cat_namespace + ':' + newcatTitle)
                    if sort_by_last_name:
                        catpl = sorted_by_last_name(catpl, page)
                    if catpl in cats:
                        wikipedia.output(u"%s is already in %s." % (page.title(), catpl.title()))
                    else:
                        wikipedia.output(u'Adding %s' % catpl.aslink())
                        cats.append(catpl)
                        text = page.get()
                        text = wikipedia.replaceCategoryLinks(text, cats)
                        try:
                            page.put(text)
                        except wikipedia.EditConflict:
                            wikipedia.output(u'Skipping %s because of edit conflict' % (page.title()))

class CategoryMoveRobot:
    def __init__(self, oldCatTitle, newCatTitle, batchMode = False, editSummary = '', inPlace = False, moveCatPage = True):
        self.editSummary = editSummary
        self.oldCat = catlib.Category(wikipedia.getSite(), 'Category:' + oldCatTitle)
        self.newCatTitle = newCatTitle
        self.inPlace = inPlace
        self.moveCatPage = moveCatPage
        self.batchMode = batchMode
        # set edit summary message
        if self.editSummary:
            wikipedia.setAction(self.editSummary)
        else:
            wikipedia.setAction(wikipedia.translate(wikipedia.getSite(),msg_change) % self.oldCat.title())

    def run(self):
        newCat = catlib.Category(wikipedia.getSite(), 'Category:' + self.newCatTitle)
        gen = pagegenerators.CategorizedPageGenerator(self.oldCat, recurse = False)
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        for article in preloadingGen:
            catlib.change_category(article, self.oldCat, newCat, inPlace=self.inPlace)

        # TODO: create subcategory generator
        subcategories = self.oldCat.subcategoriesList(recurse = False)
        if len(subcategories) == 0:
            wikipedia.output(u'There are no subcategories in category ' + self.oldCat.title())
        else:
            for subcategory in subcategories:
                catlib.change_category(subcategory, self.oldCat, newCat, inPlace=self.inPlace)
        if self.oldCat.exists() and self.moveCatPage:
            # try to copy page contents to new cat page
            if self.oldCat.copyAndKeep(self.newCatTitle, wikipedia.translate(wikipedia.getSite(), cfd_templates)):
                if self.oldCat.isEmpty():
                    reason = wikipedia.translate(wikipedia.getSite(), deletion_reason_move) % self.newCatTitle
                    if self.batchMode:
                        self.oldCat.delete(reason, False)
                    else:
                        self.oldCat.delete(reason, True)
                else:
                    wikipedia.output('Couldn\'t copy contents of %s because %s already exists.' % (self.oldCat.title(), self.newCatTitle))

class CategoryListifyRobot:
    '''
    Creates a list containing all of the members in a category.
    '''
    listify_msg={
        'en':u'Robot: Listifying from %s (%d entries)',
        'nl':u'Bot: Lijst van %s (%d pagina\'s)',
        'sv':u'Robot: Skapar en lista från %s (%d)'
    }

    def __init__(self, catTitle, listTitle, editSummary, overwrite = False, showImages = False, subCats = False, talkPages = False, recurse = False):
        self.editSummary = editSummary
        self.overwrite = overwrite
        self.showImages = showImages
        self.cat = catlib.Category(wikipedia.getSite(), 'Category:' + catTitle)
        self.list = wikipedia.Page(wikipedia.getSite(), listTitle)
        self.subCats = subCats
        self.talkPages = talkPages
        self.recurse = recurse

    def run(self):
        listOfArticles = self.cat.articlesList(recurse = self.recurse)
        if self.subCats:
            listOfArticles += self.cat.subcategoriesList()
        if self.editSummary:
            wikipedia.setAction(self.editSummary)
        else:
            wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), self.listify_msg) % (self.cat.title(), len(listOfArticles)))

        listString = ""
        for article in listOfArticles:
            if (not article.isImage() or self.showImages) and not article.isCategory():
                if self.talkPages and not article.isTalkPage():
                    listString = listString + "*[[%s]] -- [[%s|talk]]\n" % (article.title(), article.toggleTalkPage().title())
                else:
                    listString = listString + "*[[%s]]\n" % article.title()
            else:
                if self.talkPages and not article.isTalkPage():
                    listString = listString + "*[[:%s]] -- [[%s|talk]]\n" % (article.title(), article.toggleTalkPage().title())
                else:
                    listString = listString + "*[[:%s]]\n" % article.title()
        if self.list.exists() and not self.overwrite:
            wikipedia.output(u'Page %s already exists, aborting.' % self.list.title())
        else:
            self.list.put(listString)

class CategoryRemoveRobot:
    '''
    Removes the category tag from all pages in a given category and from the
    category pages of all subcategories, without prompting.
    Does not remove category tags pointing at subcategories.
    '''
    deletion_reason_remove = {
        'de':u'Bot: Kategorie wurde aufgelöst',
        'en':u'Robot: Category was disbanded',
        'he':u'רובוט: הקטגוריה פורקה',
        'ia':u'Robot: Categoria esseva dissolvite',
        'nds':u'Kat-Bot: Kategorie is nu oplööst',
        'nl':u'Bot: Categorie is opgeheven',
        'pt':u'Bot: Categoria foi unida',
        'sv':u'Robot: Kategorin upplöstes',
    }

    msg_remove={
        'da':u'Robot: Fjerner fra %s',
        'de':u'Bot: Entferne aus %s',
        'en':u'Robot: Removing from %s',
        'es':u'Bot: Eliminada de la %s',
        'he':u'רובוט: מסיר מהקטגוריה %s',
        'ia':u'Robot: Eliminate de %s',
        'is':u'Vélmenni: Fjarlægi [[Flokkur:%s]]',
        'nds':u'Kat-Bot: rut ut %s',
        'nl':u'Bot: Verwijderd uit %s',
        'pt':u'Bot: Removendo [[Categoria:%s]]',
        'sr':u'Бот: Уклањање из категорије [[Категорија:%s|%s]]',
        'sv':u'Robot: Tar bort från %s',
    }

    def __init__(self, catTitle, batchMode = False, editSummary = '', useSummaryForDeletion = False):
        self.editSummary = editSummary
        self.cat = catlib.Category(wikipedia.getSite(), 'Category:' + catTitle)
        # get edit summary message
        self.useSummaryForDeletion = useSummaryForDeletion
        self.batchMode = batchMode
        if self.editSummary:
            wikipedia.setAction(self.editSummary)
        else:
            wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), self.msg_remove) % self.cat.title())

    def run(self):
        articles = self.cat.articlesList(recurse = 0)
        if len(articles) == 0:
            wikipedia.output(u'There are no articles in category %s' % self.cat.title())
        else:
            for article in articles:
                catlib.change_category(article, self.cat, None)
        # Also removes the category tag from subcategories' pages
        subcategories = self.cat.subcategoriesList(recurse = 0)
        if len(subcategories) == 0:
            wikipedia.output(u'There are no subcategories in category %s' % self.cat.title())
        else:
            for subcategory in subcategories:
                catlib.change_category(subcategory, self.cat, None)
        if self.cat.exists() and self.cat.isEmpty():
            if self.useSummaryForDeletion:
                reason = self.editSummary
            else:
                reason = wikipedia.translate(wikipedia.getSite(), self.deletion_reason_remove)
            if self.batchMode:
                self.cat.delete(reason, False)
            else:
                self.cat.delete(reason, True)

class CategoryTidyRobot:
    """
    Script to help a human to tidy up a category by moving its articles into
    subcategories

    Specify the category name on the command line. The program will pick up the
    page, and look for all subcategories and supercategories, and show them with
    a number adjacent to them. It will then automatically loop over all pages
    in the category. It will ask you to type the number of the appropriate
    replacement, and perform the change robotically.

    If you don't want to move the article to a subcategory or supercategory, but to
    another category, you can use the 'j' (jump) command.

    Typing 's' will leave the complete page unchanged.

    Typing '?' will show you the first few bytes of the current page, helping
    you to find out what the article is about and in which other categories it
    currently is.

    Important:
     * this bot is written to work with the MonoBook skin, so make sure your bot
       account uses this skin
    """
    def __init__(self, catTitle, catDB):
        self.catTitle = catTitle
        self.catDB = catDB

        # This is a purely interactive robot. We set the delays lower.
        wikipedia.get_throttle.setDelay(1)
        wikipedia.put_throttle.setDelay(10)

    def move_to_category(self, article, original_cat, current_cat):
        '''
        Given an article which is in category original_cat, ask the user if
        it should be moved to one of original_cat's subcategories.
        Recursively run through subcategories' subcategories.
        NOTE: current_cat is only used for internal recursion. You should
        always use current_cat = original_cat.
        '''
        wikipedia.output(u'')
        # Show the title of the page where the link was found.
        # Highlight the title in purple.
        colors = [None] * 14 + [13] * len(article.title()) + [None] * 15 + [13] * len(current_cat.title())
        wikipedia.output(u'Treating page %s, currently in %s' % (article.title(), current_cat.title()), colors = colors)

        # Determine a reasonable amount of context to print
        try:
            full_text = article.get(get_redirect = True)
        except wikipedia.NoPage:
            wikipedia.output(u'Page %s not found.' % article.title())
            return
        try:
            contextLength = full_text.index('\n\n')
        except ValueError: # substring not found
            contextLength = 500
        if full_text.startswith(u'[['): # probably an image
            # Add extra paragraph.
            contextLength = full_text.index('\n\n', contextLength+2)
        if contextLength > 1000 or contextLength < 0:
            contextLength = 500
        print
        wikipedia.output(full_text[:contextLength])
        print

        subcatlist = self.catDB.getSubcats(current_cat)
        supercatlist = self.catDB.getSupercats(current_cat)
        print
        if len(subcatlist) == 0:
            print 'This category has no subcategories.'
            print
        if len(supercatlist) == 0:
            print 'This category has no supercategories.'
            print
        # show subcategories as possible choices (with numbers)
        for i in range(len(supercatlist)):
            # layout: we don't expect a cat to have more than 10 supercats
            wikipedia.output(u'u%d - Move up to %s' % (i, supercatlist[i].title()))
        for i in range(len(subcatlist)):
            # layout: we don't expect a cat to have more than 100 subcats
            wikipedia.output(u'%2d - Move down to %s' % (i, subcatlist[i].title()))
        print ' j - Jump to another category'
        print ' n - Skip this article'
        print ' r - Remove this category tag'
        print ' ? - Print first part of the page (longer and longer)'
        wikipedia.output(u'Enter - Save category as %s' % current_cat.title())

        flag = False
        while not flag:
            print ''
            choice=wikipedia.input(u'Choice:')
            if choice == 'n':
                flag = True
            elif choice == '':
                wikipedia.output(u'Saving category as %s' % current_cat.title())
                if current_cat == original_cat:
                    print 'No changes necessary.'
                else:
                    catlib.change_category(article, original_cat, current_cat)
                flag = True
            elif choice == 'j':
                newCatTitle = wikipedia.input(u'Please enter the category the article should be moved to:')
                newCat = catlib.Category(wikipedia.getSite(), 'Category:' + newCatTitle)
                # recurse into chosen category
                self.move_to_category(article, original_cat, newCat)
                flag = True
            elif choice == 'r':
                # remove the category tag
                catlib.change_category(article, original_cat, None)
                flag = True
            elif choice == '?':
                contextLength += 500
                print
                wikipedia.output(full_text[:contextLength])
                print

                # if categories possibly weren't visible, show them additionally
                # (maybe this should always be shown?)
                if len(full_text) > contextLength:
                    print ''
                    print 'Original categories: '
                    for cat in article.categories():
                        wikipedia.output(u'* %s' % cat.title())
            elif choice[0] == 'u':
                try:
                    choice=int(choice[1:])
                except ValueError:
                    # user pressed an unknown command. Prompt him again.
                    continue
                self.move_to_category(article, original_cat, supercatlist[choice])
                flag = True
            else:
                try:
                    choice=int(choice)
                except ValueError:
                    # user pressed an unknown command. Prompt him again.
                    continue
                # recurse into subcategory
                self.move_to_category(article, original_cat, subcatlist[choice])
                flag = True

    def run(self):
        cat = catlib.Category(wikipedia.getSite(), 'Category:' + self.catTitle)

        # get edit summary message
        wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), msg_change) % cat.title())

        articles = cat.articlesList(recurse = False)
        if len(articles) == 0:
            wikipedia.output(u'There are no articles in category ' + catTitle)
        else:
            preloadingGen = pagegenerators.PreloadingGenerator(iter(articles))
            for article in preloadingGen:
                wikipedia.output(u'\n===================================================================')
                self.move_to_category(article, cat, cat)

class CategoryTreeRobot:
    '''
    Robot to create tree overviews of the category structure.

    Parameters:
        * catTitle - The category which will be the tree's root.
        * catDB    - A CategoryDatabase object
        * maxDepth - The limit beyond which no subcategories will be listed.
                     This also guarantees that loops in the category structure
                     won't be a problem.
        * filename - The textfile where the tree should be saved; None to print
                     the tree to stdout.
    '''

    def __init__(self, catTitle, catDB, filename = None, maxDepth = 10):
        self.catTitle = catTitle
        self.catDB = catDB
        self.filename = filename
        # TODO: make maxDepth changeable with a parameter or config file entry
        self.maxDepth = maxDepth

    def treeview(self, cat, currentDepth = 0, parent = None):
        '''
        Returns a multi-line string which contains a tree view of all subcategories
        of cat, up to level maxDepth. Recursively calls itself.

        Parameters:
            * cat - the Category of the node we're currently opening
            * currentDepth - the current level in the tree (for recursion)
            * parent - the Category of the category we're coming from
        '''

        # Translations to say that the current category is in more categories than
        # the one we're coming from
        also_in_cats = {
            'da': u'(også i %s)',
            'de': u'(auch in %s)',
            'en': u'(also in %s)',
            'fr': u'(également dans %s)',
            'he': u'(גם בקטגוריות %s)',
            'ia': u'(equalmente in %s)',
            'is': u'(einnig í %s)',
            'nl': u'(ook in %s)',
            'pt': u'(também em %s)',
            'sv': u'(också i %s)',
            'ср': u'(такође у %s)',
            }

        result = u'#' * currentDepth
        result += '[[:%s|%s]]' % (cat.title(), cat.title().split(':', 1)[1])
        result += ' (%d)' % len(self.catDB.getArticles(cat))
        # We will remove an element of this array, but will need the original array
        # later, so we create a shallow copy with [:]
        supercats = self.catDB.getSupercats(cat)[:]
        # Find out which other cats are supercats of the current cat
        try:
            supercats.remove(parent)
        except:
            pass
        if supercats != []:
            supercat_names = []
            for i in range(len(supercats)):
                # create a list of wiki links to the supercategories
                supercat_names.append('[[:%s|%s]]' % (supercats[i].title(), supercats[i].title().split(':', 1)[1]))
                # print this list, separated with commas, using translations given in also_in_cats
            result += ' ' + wikipedia.translate(wikipedia.getSite(), also_in_cats) % ', '.join(supercat_names)
        result += '\n'
        if currentDepth < self.maxDepth:
            for subcat in self.catDB.getSubcats(cat):
                # recurse into subdirectories
                result += self.treeview(subcat, currentDepth + 1, parent = cat)
        else:
            if self.catDB.getSubcats(cat) != []:
                # show that there are more categories beyond the depth limit
                result += '#' * (currentDepth + 1) + '[...]\n'
        return result

    def run(self):
        """
        Prints the multi-line string generated by treeview or saves it to a file.

        Parameters:
            * catTitle - the title of the category which will be the tree's root
            * maxDepth - the limit beyond which no subcategories will be listed
        """
        cat = catlib.Category(wikipedia.getSite(), 'Category:' + self.catTitle)
        tree = self.treeview(cat)
        if filename:
            wikipedia.output(u'Saving results in %s' % filename)
            import codecs
            f = codecs.open(filename, 'a', 'utf-8')
            f.write(tree)
            f.close()
        else:
            wikipedia.output(tree, toStdout = True)

if __name__ == "__main__":
    fromGiven = False
    toGiven = False
    batchMode = False
    editSummary = ''
    inPlace = False
    overwrite = False
    showImages = False
    talkPages = False
    recurse = False

    #If this is set to true then the custom edit summary given for removing
    #categories from articles will also be used as the deletion reason.
    useSummaryForDeletion = False
    try:
        catDB = CategoryDatabase()
        action = None
        sort_by_last_name = False
        restore = False
        for arg in wikipedia.handleArgs():
            if arg == 'add':
                action = 'add'
            elif arg == 'remove':
                action = 'remove'
            elif arg == 'move':
                action = 'move'
            elif arg == 'tidy':
                action = 'tidy'
            elif arg == 'tree':
                action = 'tree'
            elif arg == 'listify':
                action = 'listify'
            elif arg == '-person':
                sort_by_last_name = True
            elif arg == '-rebuild':
                catDB.rebuild()
            elif arg.startswith('-from:'):
                oldCatTitle = arg[len('-from:'):]
                fromGiven = True
            elif arg.startswith('-to:'):
                newCatTitle = arg[len('-to:'):]
                toGiven = True
            elif arg == '-batch':
                batchMode = True
            elif arg == '-inplace':
                inPlace = True
            elif arg == '-delsum':
                useSummaryForDeletion = True
            elif arg == '-overwrite':
                overwrite = True
            elif arg == '-showimages':
                showImages = True
            elif arg.startswith('-summary:'):
                editSummary = arg[len('-summary:'):]
            elif arg == '-talkpages':
                talkPages = True
            elif arg == '-recurse':
                recurse = True

        if action == 'add':
            add_category(sort_by_last_name)
        elif action == 'remove':
            if (fromGiven == False):
                oldCatTitle = wikipedia.input(u'Please enter the name of the category that should be removed:')
            bot = CategoryRemoveRobot(oldCatTitle, batchMode, editSummary, useSummaryForDeletion)
            bot.run()
        elif action == 'move':
            if (fromGiven == False):
                oldCatTitle = wikipedia.input(u'Please enter the old name of the category:')
            if (toGiven == False):
                newCatTitle = wikipedia.input(u'Please enter the new name of the category:')
            bot = CategoryMoveRobot(oldCatTitle, newCatTitle, batchMode, editSummary, inPlace)
            bot.run()
        elif action == 'tidy':
            catTitle = wikipedia.input(u'Which category do you want to tidy up?')
            bot = CategoryTidyRobot(catTitle, catDB)
            bot.run()
        elif action == 'tree':
            catTitle = wikipedia.input(u'For which category do you want to create a tree view?')
            filename = wikipedia.input(u'Please enter the name of the file where the tree should be saved, or press enter to simply show the tree:')
            bot = CategoryTreeRobot(catTitle, catDB, filename)
            bot.run()
        elif action == 'listify':
            if (fromGiven == False):
                oldCatTitle = wikipedia.input(u'Please enter the name of the category to listify:')
            if (toGiven == False):
                newCatTitle = wikipedia.input(u'Please enter the name of the list to create:')
            bot = CategoryListifyRobot(oldCatTitle, newCatTitle, editSummary, overwrite, showImages, subCats = True, talkPages = talkPages, recurse = recurse)
            bot.run()
        else:
            wikipedia.showHelp('category')
    finally:
        catDB.dump()
        wikipedia.stopme()
