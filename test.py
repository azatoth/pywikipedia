#
# Script to check language links for years A.D.
#
# (C) Rob W.W. Hooft, 2003
# Distribute under the terms of the GPL.

import re,sys,wikipedia
if 0:
    wikipedia.langs={'test':'test.wikipedia.org'}

    text=wikipedia.getPage('test','Robottest')
    text=text+'\nrobot was here\n'
    status,reason,data=wikipedia.putPage('test','Robottest',text)
    print status,reason

if 0:
    wikipedia.getPage('pt','HTTP')

x1='\xb1\xb3\xbf'
import codecs
encode_func, decode_func, stream_reader, stream_writer = codecs.lookup('iso-8859-2')
x2,l=decode_func(x1)
print repr(x2)

u2=wikipedia.link2url(x1,'pl')
print u2
