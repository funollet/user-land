#!/usr/bin/env python
# sms_vodafone

"""This script is unmaintained.
"""

import pycurl
import StringIO
import logging
import os
import ConfigParser

CFGFILE = '~/.sms_vodafone'

def load_conf (cfg_fname=CFGFILE):
    """Returns dict of sections. Has a list of tuples (key, value).

    Usage:
        cfg['auth']['password']
    """
    fileconf = os.path.abspath(os.path.expanduser(cfg_fname))
    parser = ConfigParser.ConfigParser()
    parser.read(fileconf)

    cfg = [(section, dict(parser.items(section))) for section in parser.sections()]
    return dict(cfg)


#class CurlShareCookies:
#    """Instance of pycurl.Curl() that does several POSTs sharing cookies.
#    """
#    
#    def __init__(self, cookiejar):
#        
#        # Filename of the cookiejar.
#        self.cookiejar = cookiejar
#
#        # String-like object to "hide" curl's output. Used as /dev/null.
#        self.body = StringIO.StringIO()
#        
#        self.curl = pycurl.Curl()
#        # Option -b/--cookie <name=string/file>
#        # Note: must be a string, not a file object.
#        self.curl.setopt(pycurl.COOKIEFILE, self.cookiejar)
#        # Option -c/--cookie-jar <file>
#        # Note: must be a string, not a file object.
#        self.curl.setopt(pycurl.COOKIEJAR, self.cookiejar)
#
#
#    def post(self, url, postfields, verbose=True):
#        """Sends a POST using pycurl.
#        
#        @url:        url for pycurl.Curl
#        @postfields: postfields for pycurl.Curl    
#        @verbose:    if True, shows HTML on stdout (default: True)
#        """
#        
#        self.curl.setopt(pycurl.URL, url)
#        self.curl.setopt(pycurl.HTTPPOST, postfields)
#
#        if verbose:
#            self.curl.setopt (pycurl.VERBOSE, 1)    # just for debugging
#        else:
#            self.curl.setopt (pycurl.VERBOSE, 0)    # be quiet
#            self.curl.setopt(pycurl.WRITEFUNCTION, self.body.write)
#            self.curl.setopt(pycurl.HEADERFUNCTION, self.body.write)
#
#        self.curl.perform()
#        self.curl.close()



class Vodafone:
    
    def __init__(self):

        # String-like object to "hide" curl's output. Used as /dev/null.
        self.body = StringIO.StringIO()
        
        # Create the curl object.
        self.curl = pycurl.Curl()

        # Store the cookies trasparently.
        self.share = pycurl.CurlShare()
        self.share.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_COOKIE)
        self.share.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_DNS)

        self.curl.setopt(pycurl.SHARE, self.share)


    def post(self, url, postfields, verbose=True):
        """Sends a POST using pycurl.
        
        @url:        url for pycurl.Curl
        @postfields: postfields for pycurl.Curl    
        @verbose:    if True, shows HTML on stdout (default: True)
        """
        
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.HTTPPOST, postfields)

        if verbose:
            self.curl.setopt (pycurl.VERBOSE, 1)    # just for debugging
        else:
            self.curl.setopt (pycurl.VERBOSE, 0)    # be quiet
            self.curl.setopt(pycurl.WRITEFUNCTION, self.body.write)
            self.curl.setopt(pycurl.HEADERFUNCTION, self.body.write)

        self.curl.perform()


    def get(self, url, verbose=True):
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.HTTPGET, 1)
        
        
        if verbose:
            self.curl.setopt (pycurl.VERBOSE, 1)    # just for debugging
        else:
            self.curl.setopt (pycurl.VERBOSE, 0)    # be quiet
            self.curl.setopt(pycurl.WRITEFUNCTION, self.body.write)
            self.curl.setopt(pycurl.HEADERFUNCTION, self.body.write)

        self.curl.perform()


    def close(self):
        self.curl.close()


    def login_mivodafone(self, msisdn, password):
        """Login to the 'MiVodafone' website.
        
        @msisdn: login at Vodafone website (phone number)
        @password: password at Vodafone website
        """
        
        logging.debug('entering Vodafone.login_mivodafone()')

        url = "https://canalonline.vodafone.es/cpar/do/login/query"
        #url = "https://grandescuentas.vodafone.es/cwgc/directLogin.jsp"
        postfields = [ 
            ("action", 
             "https://grandescuentas.vodafone.es/cwgc/directLogin.jsp"),
            ("msisdn", msisdn),
            ("pwd", password),
            ]

        self.post(url, postfields, verbose=False)

        logging.debug('running GET at mivodafone home')
        
        url = "https://canalonline.vodafone.es/cpar/do/home/load"
        self.get(url)


    def login_albumsms(self):
        """Login to the "AlbumSMS" application.
        """

        logging.debug('entering Vodafone.login_albumsms()')

        #-d action="accessSMS"
        #"https://online.vodafone.es/albumsms/ContEntrada?mensaje=${MSISDN}&id_session=${ID_SESSION}&firma="
        #url = "https://online.vodafone.es/albumsms/ContEntrada?mensaje=%s&id_session=%s&firma=" % (MSISDN, ID_SESSION)
        url = 'https://canalonline.vodafone.es/cpar/do/sms/info'
        postfields = [
            ("action", "accessSMS"),
            ("url", "https://online.vodafone.es/albumsms/ContEntrada?mensaje=600859815&id_session=NCO8618367667AAAEA6248795B22A1FAE3C&firma=")
            ]

        self.post(url, postfields, verbose=False)


    def send_sms (self):
        """Send an SMS.
        """
        
        logging.debug('entering Vodafone.send_sms()')
        #-d action="/albumsms/ContEnvioSMS" \
        #-d operacion="iniciar_envioSMS" \
        #-d destinos="t1.600859815" \
        #-d smsTxt="hola caracola" \
        #      https://online.vodafone.es/albumsms/ContEnvioSMS
        url = 'https://online.vodafone.es/albumsms/ContEnvioSMS'
        postfields = [
            ("action", "/albumsms/ContEnvioSMS"),
            ("operacion", "iniciar_envioSMS"),
            ("destinos", "t1.600859815"),
            ("smsTxt", "hola caracola"),
        ]

        self.post(url, postfields, verbose=False)


def main():
    """Run the program.
    """

    # Set debug level.
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Read user/password from configuration file.
    cfg = load_conf()
    msisdn = cfg['auth']['msisdn']
    password = cfg['auth']['password']

    vodaf = Vodafone()
    vodaf.login_mivodafone(msisdn, password)
    #vodaf.login_albumsms()
    #vodaf.send_sms()
    vodaf.close()
    
    
if __name__ == '__main__':
    #TODO: screen-scrap for this value.
    ID_SESSION = "NCO1D1621DB61FAF9E7608D8DBD8CEF7181"
    #TODO: convert to command-line option.
    DEBUG = True

    main()
    