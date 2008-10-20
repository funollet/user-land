#!/usr/bin/env python
# upload23.py
#   Uploads files to www.23hq.com.
#   (Nautilus script. Place it under ~/gnome2/nautilus-scripts/
#   and make executable).
#
# Jordi Funollet <jordi.f@ati.es>  Mon, 09 Jan 2006 16:35:01 +0100

"""Uploads files to a 23hq.com account. Authentication data must be
on a configuration file (Frob not yet implemented).
"""

# CHANGELOG
#
# Mon Oct 20 18:21:40 CEST 2008
# - Script abandoned. Similar functionality is provided by the
#   Fotofox Firefox extension (http://briks.si/projekti/fotofox/).
#
# Wed, 08 Feb 2006 03:12:49 +0100
# - Big refactoring. Dropped everything Mozilla-related.
# - Upload through /services/upload/.
# - Authenticating with username+password.
#
# Thu, 09 Feb 2006 01:15:22 +0100
# - Configuration in external file (with ConfigParser).
#
# Mon, 13 Feb 2006 14:41:32 +0100
# - Captured POST return into Account23.content.



import logging
from optparse import OptionParser
import pycurl
import urllib
import urlparse
import ConfigParser
import re
import os
# TODO: use subprocess
import commands


SITE = 'http://www.23hq.com'
CFGFILE = '~/.upload23'



class Account23:
    """Operates with a 23hq.com account.
    """
    #TODO: auth with frob.
    
    def __init__ (self, auth_tuples, site=SITE):
        """Initials settings for the account. Receives list of tuples
        with params for authentication.
        """
        
        self.auth = auth_tuples
        self.site = site
        self.url_upload = urlparse.urljoin(self.site, '/services/upload/')
        # XML strings returned on each POSTed file.
        self.contents = ''
        logging.debug("Account manager instantiated.")
        

    def __get_uploaded_ids (self):
        """List of uploaded photoIDs.
        """
        
        pattern = r'''<photoid>(.\d*)</photoid>'''
        regex = re.compile (pattern)
        return regex.findall(self.contents)


    def edit_uploaded (self):
        """Redirect to Firefox for editing uploaded files.
        """
        # ToDo: not working when called from Digikam (works on command-line).
        logging.debug('calling Firefox to edit uploaded files')
        
        ids_csv = ','.join(self.__get_uploaded_ids())
        url = urlparse.urljoin(self.site, '/tools/uploader_edit.gne?ids=%s' \
            % ids_csv)
        cmd = '''firefox -remote "openurl(%s)"''' % url 
        (_, _) = commands.getstatusoutput (cmd)

    
    def upload (self, fname):
        """Sends an image to 23hq.com POSTing to /services/upload/.
        """
        fname = os.path.abspath(os.path.expanduser(fname))
        
        # ToDo: proxy detection fails; Digikam calls it with a clean environment?
        #if os.environ.has_key('http_proxy'):
            #proxy = os.environ['http_proxy']
        proxy = 'http://proxy.upf.es:8080'
        #proxy = ''
        
        logging.debug("Account23.upload() has been called")
        if os.path.exists(fname):
            logging.debug("configuring curl to upload '%s'" % fname)
            postfields = self.auth + \
                [ ('photo', (pycurl.FORM_FILE, fname)) ] 
        
            curl = pycurl.Curl()
            #curl.setopt (curl.VERBOSE, 1)    # just for debugging
            if proxy:
                curl.setopt(pycurl.PROXY, proxy)
                curl.setopt(pycurl.NOSIGNAL, 1)
                logging.debug("Proxy set to %s" % proxy)
            curl.setopt (curl.URL, self.url_upload)
            curl.setopt (curl.HTTPPOST, postfields)
            # Don't print on stdout.
            curl.setopt (curl.WRITEFUNCTION, self.__curl_body_callback)
            logging.debug("starting upload with curl...")
            curl.perform()
            curl.close()
            logging.debug("...upload with curl finished")
        else:
            logging.error('File not found: %s' % fname)


    def __curl_body_callback (self, buff):
        """Store in self.contents XML returned by each POST.
        """
        self.contents = self.contents + buff
                

##########################################################

#def encode_multipart_formdata(fields, files):
    #"""Return (content_type, body) ready for httplib.HTTP instance

    #@fields:    sequence of (name, value) elements for regular form fields.
    #@files:     sequence of (name, filename, value) elements for data 
    #                    to be uploaded as files
    #"""

    #import mimetools
    #import mimetypes

    #boundary =  mimetools.choose_boundary()

    #body = []

    #for (key, value) in fields:
        #body += '--%s' % boundary
        #body += 'Content-Disposition: form-data; name="%s"' % key
        #body += value

    #for (key, filename, value) in files:
        ##base64.encode(open(FILE, "rb"), file)
        #body += '--%s' % boundary
        #body += 'Content-Disposition: form-data; name="%s"; filename="%s"' \
            #% (key, filename)
        #body += 'Content-Type: %s' % get_content_type(filename)
        #body += value

    #body += '''--%s--''' % boundary

    #content_type = 'multipart/form-data; boundary=%s' % boundary
    #return content_type, body

#def get_content_type(filename):
    #return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

##########################################################


def load_conf (cfg_fname=CFGFILE):
    """Returns dict of sections. Has a list of tuples (key, value).

    Usage:
        cfg['auth']['password']
    """
    fileconf = os.path.abspath(os.path.expanduser(cfg_fname))
    parser = ConfigParser.ConfigParser()
    parser.read(fileconf)

    cfg = [(section, parser.items(section)) for section in parser.sections()]
    return dict(cfg)


def is_nautilus_invoked():
    """True if the script has been invoked from Nautilus.
    """
    return os.environ.has_key ('NAUTILUS_SCRIPT_SELECTED_URIS')


def get_nautilus_files():
    """Returns files passed from Nautilus.
    """
    # Nautilus passes files as one-per-line url-encoded.
    uris = os.environ['NAUTILUS_SCRIPT_SELECTED_URIS'].split('\n')
    # Remove 'file://' and unquote '%xx' chars.
    return [urllib.unquote(uri)[7:] for uri in uris]



def main():
    """Read command-line, parse config. file, 
    """
    
    # Parse command-line.
    usage = """usage: %prog [options]"""
    parser = OptionParser(usage=usage)
    
    parser.add_option("-d", "--debug", action="store_true",
                      help="set DEBUG loglevel")
    parser.add_option("-n", "--noact", action="store_true",
                      help="do nothing, just show")
    
    options, args = parser.parse_args()

    # Set debug level.
    if options.debug:
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG, filename='/tmp/upload23.out')
    else:
        logging.basicConfig(level=logging.INFO)

    cfg = load_conf()
    logging.debug('Config read.\n\t%s' % cfg['auth'])

    if is_nautilus_invoked():
        filenames = get_nautilus_files()
    else:
        filenames = args
    logging.debug('Filenames to upload: %s' % filenames)
    #filenames = nautilus_or_cmdline()
    
    account23 = Account23 (cfg['auth'])
    
    for fname in filenames:
        logging.debug('uploading %s' % fname)
        if not options.noact:
            account23.upload (fname)
    # Show the uploaded_files page in Firefox.
    if filenames:
        if not options.noact:
            account23.edit_uploaded()


if __name__ == '__main__':
    print """Warning: this script is abandoned. You can have similiar
    functionality with the Fotofox Firefox extension.
    
    Fotofox: http://briks.si/projekti/fotofox/
    """
    main()

