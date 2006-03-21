# -*- coding: utf-8  -*-
import family
    
# The Lovetoknow internal family, for lovetoknow wikis, including those
# not yet open to the public.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)

        self.name = 'loveto'

        self.langs = {
            '1911': 'sandbox2',
            'recipes': 'recipes',
            }

        self.namespaces[4]['1911'] = 'LoveToKnow Watches'
        self.namespaces[5]['1911'] = 'LoveToKnow Watches Talk'

        self.namespaces[4]['recipes'] = 'LoveToKnow Recipes'
        self.namespaces[5]['recipes'] = 'Talk:LoveToKnow Recipes'
        
    # Which version of MediaWiki is used?

    def version(self, code):
        return "1.4.5"

    def hostname(self,code):
        return self.langs[code] + '.lovetoknow.com'

    def RversionTab(self, code):
        if code == '1911':
            return(r"action=history")
        else:
            return(r"table\>\s*\<script")


    def edit_address(self, code, name):
        if code == 'recipes':
            return '%s?title=%s&action=edit&masteredit=1' % (self.path(code), name)
        else:
            return '%s?title=%s&action=edit' % (self.path(code), name)
        
