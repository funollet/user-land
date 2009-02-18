#!/usr/bin/env python
# sms_vodafone

import pycurl
import tempfile
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


class CurlShareCookies:
    """Instance of pycurl.Curl() that does several POSTs sharing cookies.
    """
    
    def __init__(self, cookiejar):
        
        # Filename of the cookiejar.
        self.cookiejar = cookiejar

        # String-like object to "hide" curl's output. Used as /dev/null.
        self.body = StringIO.StringIO()
        
        self.curl = pycurl.Curl()
        # Option -b/--cookie <name=string/file>
        # Note: must be a string, not a file object.
        self.curl.setopt(pycurl.COOKIEFILE, self.cookiejar)
        # Option -c/--cookie-jar <file>
        # Note: must be a string, not a file object.
        self.curl.setopt(pycurl.COOKIEJAR, self.cookiejar)


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
        self.curl.close()



class Vodafone:
    
    def __init__(self, cookie_fname):
        self.cookiejar = cookie_fname


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

        self.curl = CurlShareCookies(self.cookiejar)
        self.curl.post(url, postfields)


    def login_albumsms(self):
        """Login to the "AlbumSMS" application.
        """

        logging.debug('entering Vodafone.login_albumsms()')
        #-d action="accessSMS"
        #"https://online.vodafone.es/albumsms/ContEntrada?mensaje=${MSISDN}&id_session=${ID_SESSION}&firma="
        #url = "https://online.vodafone.es/albumsms/ContEntrada?mensaje=%s&id_session=%s&firma=" % (MSISDN, ID_SESSION)
        url = 'https://online.vodafone.es/albumsms/ContEntrada?mensaje=600859815&id_session=NCO1D1621DB61FAF9E7608D8DBD8CEF7181&firma='
        postfields = [
            ("action", "accessSMS"),
            ]

        self.curl = CurlShareCookies(self.cookiejar)
        self.curl.post(url, postfields)


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

        self.curl = CurlShareCookies(self.cookiejar)
        self.curl.post(url, postfields)


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

    # Temporal file for storing cookies.
    cookies = tempfile.mktemp()
    
    vodaf = Vodafone(cookies)
    vodaf.login_mivodafone(msisdn, password)
    vodaf.login_albumsms()
    vodaf.send_sms()
    
    # Remove stored cookies.
    os.remove(cookies)
    
    
if __name__ == '__main__':
    #TODO: screen-scrap for this value.
    ID_SESSION = "NCO1D1621DB61FAF9E7608D8DBD8CEF7181"
    #TODO: convert to command-line option.
    DEBUG = True

    main()
    