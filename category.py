# -*- coding: utf-8 -*-

"""
Scripts to manage categories.

This bot has the following functions, which must be given as command line
arguments:

    add  - mass-add a category to a list of pages
    tidy - tidy up a category by moving its articles into subcategories
    rename - move all pages in a category to another category

For example, to add a new category, 

See comments below for details.
"""

#
# (C) Rob W.W. Hooft, 2004
# (C) Daniel Herding, 2004
#
# Distribute under the terms of the PSF license.
# 
import re, sys
import wikipedia, config, catlib, interwiki


# Summary message
msg={
    'en':'Robot: Changing category: %s',
    'de':'Bot: \xc4ndere Kategorie: %s',
    }

"""
A robot to mass-add a category to a list of pages.

Just run this robot without any additional arguments.

"""
def add_category():
    print "This bot has two modes: you can add a category link to all"
    print "pages mentioned in a List that is now in another wikipedia page"
    print "or you can add a category link to all pages that link to a"
    print "specific page. If you want the second, please give an empty"
    print "answer to the first question."
    listpage = raw_input('Wikipedia page with list of pages to change: ')
    if listpage:
        pl = wikipedia.PageLink(wikipedia.mylang, listpage)
        pagenames = pl.links()
    else:
        refpage = raw_input('Wikipedia page that is now linked to: ')
        pl = wikipedia.PageLink(wikipedia.mylang, refpage)
        pagenames = wikipedia.getReferences(pl)
    print "  ==> %d pages to process"%len(pagenames)
    print
    newcat = raw_input('Category to add (do not give namespace) : ')
    newcat = unicode(newcat, config.console_encoding)
    newcat = newcat.encode(wikipedia.code2encoding(wikipedia.mylang))
    newcat = newcat[:1].capitalize() + newcat[1:]

    print newcat
    ns = wikipedia.family.category_namespaces(wikipedia.mylang)
    
    catpl = wikipedia.PageLink(wikipedia.mylang, ns[0].encode(wikipedia.code2encoding(wikipedia.mylang))+':'+newcat)
    print "Will add %s"%catpl.aslocallink()

    answer = ''
    for nm in pagenames:
        pl2 = wikipedia.PageLink(wikipedia.mylang, nm)
        if answer != 'a':
	    answer = ''
        while answer not in ('y','n','a'):
            answer = raw_input("%s [y/n/a(ll)] : "%(pl2.asasciilink()))
            if answer == 'a':
                confirm = ''
		while confirm not in ('y','n'):
	            confirm = raw_input("This should be used if and only if you are sure that your links are correct !!! Are you sure ? [y/n] : ")
	
	if answer == 'y' or answer == 'a':
            try:
	        cats = pl2.categories()
            except wikipedia.NoPage:
	    	print "%s doesn't exit yet. Ignoring."%(pl2.aslocallink())
		pass
            except wikipedia.IsRedirectPage,arg:
	    	pl3 = wikipedia.PageLink(wikipedia.mylang,arg.args[0])
		print "WARNING: %s is redirect to [[%s]]. Ignoring."%(pl2.aslocallink(),pl3.aslocallink())
	    else:
                print "Current categories: ",cats
                if catpl in cats:
                    print "%s already has %s"%(pl.aslocallink(),catpl.aslocallink())
                else:
                    cats.append(catpl)
                    text = pl2.get()
                    text = wikipedia.replaceCategoryLinks(text, cats)
                    pl2.put(text, comment = catpl.aslocallink().encode(wikipedia.code2encoding(wikipedia.mylang)))


def rename_category():
    # given an article which is in category old_cat, moves it to
    # category new_cat. Moves subcategories of old_cat to new_cat
    # as well.
    def move_to_category(article, old_cat, new_cat):
        cats = article.categories()
        cats.remove(old_cat)
        cats.append(new_cat)
        text = article.get()
        text = wikipedia.replaceCategoryLinks(text, cats)
        print "Changing page %s" %(article)
        article.put(text)
        
    old_title = raw_input('Please enter the old name of the category: ')
    old_cat = catlib.CatLink(old_title)
    new_title = raw_input('Please enter the new name of the category: ')
    new_cat = catlib.CatLink(new_title)
    
    # get edit summary message
    wikipedia.setAction(msg[wikipedia.chooselang(wikipedia.mylang,msg)] % old_title)
    
    articles = old_cat.articles(recurse = 0)
    if len(articles) == 0:
        print 'There are no articles in category ' + old_title
    else:
        for article in articles:
            move_to_category(article, old_cat, new_cat)
    
    subcategories = old_cat.subcategories(recurse = 0)
    if len(subcategories) == 0:
        print 'There are no subcategories in category ' + old_title
    else:
        for subcategory in subcategories:
            move_to_category(subcategory, old_cat, new_cat)

"""
Script to help a human to tidy up a category by moving its articles into
subcategories

Specify the category name on the command line. The program will
pick up the page, and look for all subcategories, and show them with
a number adjacent to them. It will then automatically loop over all pages
in the category. It will ask you to type the number of the appropriate
replacement, and perform the change robotically.

Multiple references in one page will be scanned in order, but typing 'n' on
any one of them will leave the complete page unchanged; it is not possible to
leave only one reference unchanged.

Important:
 * every category page must contain some text; otherwise an edit box will be
   displayed instead of an article list, and the bot won't work
 * this bot is written to work with the MonoBook skin, so make sure your bot
   account uses this skin
"""

def tidy_category():
    # This is a temporary knowledge base (dictionary data type) for all known
    # supercategory-subcategory relationships, so that category pages don't need to
    # be loaded over and over again

    # This is a purely interactive robot. We set the delays lower.
    wikipedia.get_throttle.setDelay(5)
    wikipedia.put_throttle.setDelay(10)

    subclassDB={}
    
    # for a given supercategory, return a list of all its subcategories.
    # save this list in a temporary database so that it won't be loaded from the
    # server next time it's required.
    def get_subcats(supercat):
        # if we already know which subcategories exist here
        if subclassDB.has_key(supercat):
            return subclassDB[supercat]
        else:
            subcatlist = supercat.subcategories()
            # add to dictionary
            subclassDB[supercat] = subcatlist
            return subcatlist
    
    # given an article which is in category original_cat, ask the user if it should
    # be moved to one of original_cat's subcategories. Recursively run through
    # subcategories' subcategories.
    # NOTE: current_cat is only used for internal recursion. You should always use
    # current_cat = original_cat.
    def move_to_subcategory(article, original_cat, current_cat):
        print
        print 'Treating page ' + article.ascii_linkname() + ', currently in category ' + current_cat.ascii_linkname()
        subcatlist = get_subcats(current_cat)
        print
        if len(subcatlist) == 0:
            print 'This category has no subcategories.'
            print
        for i in range(len(subcatlist)):
            print '%d - Move to %s' % (i, subcatlist[i])
        print 'Enter - Save category as ' + current_cat.ascii_linkname()
        
        choice=raw_input("Choice: ")
        if choice == '':
            print 'Saving category as ' + current_cat.ascii_linkname()
            if current_cat == original_cat:
                print 'No changes necessarry.'
            else:
                # Save the changes
                cats = article.categories()
                cats.remove(original_cat)
                cats.append(current_cat)
                text = article.get()
                text = wikipedia.replaceCategoryLinks(text, cats)
                print "Changing page %s" %(article)
                article.put(text)
        else:
            try:
                choice=int(choice)
            except ValueError:
                pass
            # recurse into subcategory
            move_to_subcategory(article, original_cat, subcatlist[choice])
    
    # begin main part of tidy_category
    cat_title = raw_input('Which category do you want to tidy up? ')
    catlink = catlib.CatLink(cat_title)
    
    # get edit summary message
    wikipedia.setAction(msg[wikipedia.chooselang(wikipedia.mylang,msg)] % cat_title)
    
    
    articles = catlink.articles(recurse = 0)
    if len(articles) == 0:
        print 'There are no articles in category ' + cat_title
    else:
        for article in articles:
            print
            print '==================================================================='
            move_to_subcategory(article, catlink, catlink)



if __name__ == "__main__":
    for arg in sys.argv[1:]:
        if wikipedia.argHandler(arg):
            pass
        elif arg == "add":
            add_category()
        elif arg == "rename":
            rename_category()
        elif arg == "tidy":
            tidy_category()