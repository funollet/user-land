#!/usr/bin/env python
# upload23.py
#   Uploads files to www.23hq.com.
#   (Nautilus script. Place it under ~/gnome2/nautilus-scripts/
#   and make executable).
#
# Jordi Funollet <jordi.f@ati.es>  Mon, 09 Jan 2006 16:35:01 +0100

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



import pycurl, urllib, ConfigParser, os, commands, re

SITE='http://www.23hq.com'
CFGFILE='~/.upload23'

#TODO: pending unittesting!!! 

def load_conf ():
    fileconf = os.path.normpath (os.path.expanduser(CFGFILE))
    c = ConfigParser.ConfigParser()
    c.read (fileconf)
    cfg = {}
    for section in c.sections() :
        cfg[section] = c.items(section)
    return cfg


def file_existant (*path_chunks):
    """Builds a full path from chunks. Verify file existence.

    Path is user-expanded.
    
    *path_chunks: strings with parts of path to be build.
    """
    joined = os.path.join (*path_chunks)
    xpanded = os.path.expanduser(joined)
    #TODO: handle exception; show informative message
    #TODO: OSError? is this the most convenient exception?
    # Raise OSError if file not found.
    st = os.stat (xpanded)
    return xpanded
         

            
class Account23:
    """Operates with a 23hq.com account.
    """
    
    def __init__ (self, auth_tuples):
        """Initials settings for the account. Receives list of tuples
        with params for authentication.
        """
        self.auth = auth_tuples
        # XML strings returned on each POSTed file.
        self.contents = ''
        #TODO: Generate post_fields (more) dinamicaly.

    def __curl_body_callback (self, buff):
        """Puts XML returned by each POST to self.contents."""
        self.contents = self.contents + buff
                
                
    def uploaded_ids (self):
        """List of photoIDs uploaded."""
        
        pattern = r'''<photoid>(.\d*)</photoid>'''
        regex = re.compile (pattern)
        return regex.findall(self.contents)


    def edit_uploaded (self):
        """Redirect to Firefox for editing uploaded files."""

        ids_csv = ','.join (self.uploaded_ids())
        url = SITE + '/tools/uploader_edit.gne?ids=' + ids_csv
        cmd = '''firefox -remote "openurl(%s)"''' % url 
        (n,s) = commands.getstatusoutput (cmd)

        
    def upload (self, *args):
        """Upload an image to 23hq.com. Default method."""
        self.services_upload (*args)
        

    def services_upload (self, fname):
        """Sends an image to 23hq.com POSTing to /services/upload/."""

        url = SITE + '/services/upload/'
        
        try:
            photo = file_existant (fname)
        except OSError:
            raise Exception('%s: file not found' % fname)

        postfields = self.auth + \
            [ ('photo', (pycurl.FORM_FILE, photo)) ] 
        
        c = pycurl.Curl()
        #c.setopt (c.VERBOSE, 1)    # just for debugging
        c.setopt (c.URL, url)
        c.setopt (c.HTTPPOST, postfields)
        # Don't print on stdout.
        c.setopt (c.WRITEFUNCTION, self.__curl_body_callback)
        c.perform()
        c.close()

     
def nautilus_or_cmdline ():
    """Returns files passed from Nautilus. If not invoked from Nautilus or
    no files passed, returns command-line arguments.
    """
    
    # Invoked from Nautilus?
    if os.environ.has_key ('NAUTILUS_SCRIPT_SELECTED_URIS'):
        def uri2path (uri):
            """Converts URI to local file-path."""
            # Remove 'file://' and unquote '%xx' chars.
            return urllib.unquote(uri)[7:]       

        # Nautilus passes files as one-per-line url-encoded.
        uris = os.environ['NAUTILUS_SCRIPT_SELECTED_URIS'].split('\n')
        paths = [uri2path(u) for u in uris]
    else:
        # Filenames from command-line.
        paths = os.sys.argv[1:]
        
    return paths


def main():
    cfg = load_conf()
    #TODO: auth with frob.
    my23 = Account23 (cfg['auth'])

    for fname in nautilus_or_cmdline():
        my23.upload (fname)

    my23.edit_uploaded()

if __name__ == '__main__':
    print """Warning: this script is abandoned. You can have similiar
    functionality with the Fotofox Firefox extension.
    
    Fotofox: http://briks.si/projekti/fotofox/
    """
    main()

