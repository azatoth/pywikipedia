# -*- coding: iso8859-1 -*-
"""
Library with functions needed for image treatment
"""

import re, sys, string, md5
import os
import httplib
import wikipedia, config, mediawiki_messages

copy_message = {
    'en':u"This image was copied from %s. The original description was:\r\n\r\n%s",
    'de':u"Dieses Bild wurde von %s kopiert. Die dortige Beschreibung lautete:\r\n\r\n%s",
    'nl':u"Afbeelding gekopieerd vanaf %s. De beschrijving daar was:\r\n\r\n%s",
    'pt':u"Esta imagem foi copiada de %s. A descri��o original foi:\r\n\r\n%s",
}

def post_multipart(host, selector, fields, files, cookies): # UGLY COPY
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.putheader("User-agent", "RobHooftWikiRobot/1.0")
    h.putheader('Host', host)
    if cookies:
        h.putheader('Cookie',cookies)
    h.endheaders()
    print "Uploading file..."
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    import mimetypes
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def get_image(original_url, source_site, original_description, keep=False, debug=False):
    """Gets the image at URL original_url, and uploads it to the home Wikipedia.
       original_description is the proposed description; if description is
       empty (''), asks for a description.
       source_site is the site the image is loaded from.
       if source_site is None, it indicates that the image is uploaded directly
       from the user's harddisk (via upload.py).
       Returns the filename which was used to upload the image
       If the upload fails, the user is asked whether to try again or not.
       If the user chooses not to retry, returns null.
    """
    # work with a copy of argument variables so we can reuse the
    # original ones if the upload fails
    fn = original_url
    description = original_description
    # Get file contents
    uo = wikipedia.MyURLopener()
    file = uo.open(fn)
    contents = file.read()
    if contents.find("The requested URL was not found on this server.") != -1:
        print "Couldn't download the image."
        return
    file.close()
    # Isolate the pure name
    if '/' in fn:
        fn = fn.split('/')[-1]
    if '\\' in fn:
        fn = fn.split('\\')[-1]
    # convert ISO 8859-1 to Unicode, or parse UTF-8. If source_site is None,
    # the filename is already in Unicode.
    if source_site != None:
        try:
            fn = unicode(fn, source_site.encoding())
        except TypeError:
            print >>sys.stderr, 'Type error in lib_images.py. This should not happen. Please report this problem.'
    if not keep:
        print "The filename on wikipedia will default to:", fn
        # ask newfn until it's valid
        ok = False
        # FIXME: these 2 belong somewhere else, presumably in family
        forbidden = '/' # to be extended
        allowed_formats = (u'jpg', u'jpeg', u'png', u'gif', u'svg', u'ogg')
        while not ok:
            ok = True
            newfn = wikipedia.input(u'Better name:')
            if newfn == "":
                newfn=fn
            ext = os.path.splitext(newfn)[1].lower().strip('.')
            for c in forbidden:
                if c in newfn:
                    print "Invalid character: %s. Please try again" % c
                    ok = False
            if ext not in allowed_formats and ok:
                ans = wikipedia.input(u"File is not is %s but %s. Continue [y/N]? " % (allowed_formats, ext))
                if not ans.lower().startswith('y'):
                    ok = False
        if newfn != '':
            fn = newfn
    # Wikipedia doesn't allow spaces in the file name.
    # Replace them here to avoid an extra confirmation form
    fn = fn.replace(' ', '_')
    # Convert the filename (currently Unicode) to the encoding used on the
    # target wiki
    fn = fn.encode(wikipedia.myencoding())
    # A proper description for the submission.
    if description=='':
        description = wikipedia.input(u'Give a description for the image:')
    else:
        print ("The suggested description is:")
        print
        wikipedia.output(description)
        print
        print ("Enter return to use this description, enter a text to add something")
        print ("at the end, or enter = followed by a text to replace the description.")
        newtext = wikipedia.input(u'Enter return, text or =text : ')
        if newtext=='':
            pass
        elif newtext.startswith('='):
            description=newtext[1:]
        else:
            description=description+' '+newtext

    formdata = {}
    formdata["wpUploadDescription"] = description
    if wikipedia.getSite().version() >= '1.4':
        formdata["wpUploadCopyStatus"] = wikipedia.input(u"Copyright status: ")
        formdata["wpUploadSource"] = wikipedia.input(u"Source of image: ")
    formdata["wpUploadAffirm"] = "1"
    formdata["wpUpload"] = "upload bestand"
    formdata["wpIgnoreWarning"] = "1"

    # try to encode the strings to the encoding used by the home Wikipedia.
    # if that's not possible (e.g. because there are non-Latin-1 characters and
    # the home Wikipedia uses Latin-1), convert all non-ASCII characters to
    # HTML entities.
    for key in formdata:
        assert isinstance(key, basestring), "ERROR: %s is not a string but %s" % (key, type(key))
        try:
            formdata[key] = formdata[key].encode(wikipedia.myencoding())
        except (UnicodeEncodeError, UnicodeDecodeError):
            formdata[key] = wikipedia.UnicodeToAsciiHtml(formdata[key]).encode(wikipedia.myencoding())

    # don't upload if we're in debug mode
    if not debug:
        mysite=wikipedia.getSite()
        returned_html = post_multipart(mysite.hostname(),
                              mysite.upload_address(),
                              formdata.items(),
                              (('wpUploadFile',fn,contents),),
                              cookies = mysite.cookies()         
                              )
        # do we know how the "success!" HTML page should look like?
        success_msg = mediawiki_messages.get('successfulupload')
        success_msgR = re.compile(re.escape(success_msg))
        if success_msgR.search(returned_html):
             print "Upload successful."
        else:
             # dump the HTML page
             print returned_html + "\n\n"
             # BUG: fn is str, not unicode, so this coercion fails if fn is not ASCII
             answer = raw_input(u"Upload of " + fn + " failed. Above you see the HTML page which was returned by MediaWiki. Try again? [y|N]")
             if answer in ["y", "Y"]:
                 return get_image(original_url, source_site, original_description, debug)
             else:
                 return
    return fn


def transfer_image(imagelink, debug=False):
    """Gets a wikilink to an image, downloads it and its description,
       and uploads it to another wikipedia.
       Returns the filename which was used to upload the image
       This function is used by imagetransfer.py and by copy_table.py
    """
    # convert HTML entities to encoding of the source wiki
    image_linkname = wikipedia.html2unicode(imagelink.linkname(), imagelink.site())
    image_linkname = image_linkname.encode('utf-8')
    if debug: print "--------------------------------------------------"
    if debug: print "Found image: %s"% image_linkname
    # need to strip off "Afbeelding:", "Image:" etc.
    # we only need the substring following the first colon
    filename = string.split(image_linkname, ":", 1)[1]
    if debug: print "Image filename is: %s " % filename
    # Spaces might occur, but internally they are represented by underscores.
    # Change the name now, because otherwise we get the wrong MD5 hash.
    # Also, the first letter should be capitalized
    filename = filename.replace(' ', '_')
    filename = filename[0].upper()+filename[1:]
    md5sum = md5.new(filename).hexdigest()
    if debug: print "MD5 hash is: %s" % md5sum
    # UGLY BUG: this assumes that the family is wikipedia!
    url = "http://" + imagelink.site().lang + ".wikipedia.org/upload/" + md5sum[0] + "/" + md5sum[:2] + "/" + filename
    if debug: print "URL should be: %s" % url
    # localize the text that should be printed on the image description page
    try:
        original_description = imagelink.get(read_only = True)
        description = wikipedia.translate(imagelink.site(), copy_message) % (repr(imagelink.site()), original_description)
        # add interwiki link
        description += "\r\n\r\n" + imagelink.aslink()
    except wikipedia.NoPage:
        description=''
        print "Image does not exist or description page is empty."
    except wikipedia.IsRedirectPage:
        description=''
        print "Image description page is redirect."
    try:
        return get_image(url, imagelink.site(), description, debug)    
    except wikipedia.NoPage:
        print "Page not found"
        return filename
