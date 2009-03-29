#!/usr/bin/env python
# sms.py
"""
Send SMS messages from commmand-line. Right now there's just one backend
implemented which sends the messages using the SOAP API of ipipi.com_.

You must get an authentication token (generated with the
`API authentication form`_). Just save it on the default location or specify
the file on command-line.


Usage with kaddressbook
-----------------------

Go to 'Settings -> Configure kaddressbook -> General'.
In 'Script-hooks -> SMS text':

    sms.py --phone "%N" --message-file "%F"
    
Looks like kaddressbook needs the script to be on the PATH. Otherwise it shows a
"program not found" warning.

.. _ipipi.com: http://www.ipipi.com
.. _`API authentication form`: https://api.upsidewireless.com/soap/Authentication.asmx?op=GetParameters
"""

#TODO:
# - License.
# - Test with an HTML proxy.
# - Test unicode messages.

import sys, os, logging
from optparse import OptionParser
import pycurl
import urllib
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from BeautifulSoup import BeautifulStoneSoup


# Default values.
IPIPI_AUTH_FILE = '~/.sms/ipipi_auth.xml'
IPIPI_API_URL = 'http://api.upsidewireless.com/soap/SMS.asmx/Send_Plain'
INTERNATIONAL_PREFIX = '+34'


def parse_command_line ():
    """Optparse wrapper.
    """

    usage = "usage: %prog <options>"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--phone", action="store",
                      help="phone number")
    parser.add_option("-m", "--message", action="store",
                      help="Message to be sent (quoted)")
    parser.add_option("--message-file", action="store", dest='message_file',
                      help="file with message to be sent")
    parser.add_option("-f", "--auth-file", action="store", dest='auth_file',
                      default=IPIPI_AUTH_FILE,
                      help="file with authentication parameters")
    
    parser.add_option("-d", "--debug", action="store_true", default=False,
                      help="show debugging info")
    parser.add_option("-q", "--quiet", action="store_true",
                      help="be silent",)

    options, args = parser.parse_args()

    # Check required options.
    if not options.phone:
        parser.error("A phone number is required.")
    if not options.message and not options.message_file:
        parser.error("This program is more useful if you provide a message to send.")

    return (options, args)


def load_text_file(fname):
    """Expands a filename and returns its contents as a single string.
    """

    fname_normalized = os.path.abspath(os.path.expanduser(fname))

    txt_file = open(fname_normalized, 'r')
    txt = txt_file.read()
    txt_file.close()
    return txt


def sanitize_phone(phone):
    """Gives suitable format to a phone number: remove unwanted chars, add
    an international prefix (if needed).
    
    @phone:    phone number (str)
    """
    
    phone = phone.replace('.', '')
    phone = phone.replace(' ', '')
    phone = phone.replace('-', '')
    phone = phone.replace('_', '')
    
    # Add default international prefix, if needed
    if phone.startswith('+'):
        return phone
    else:
        return '%s%s' % (INTERNATIONAL_PREFIX, phone)



class IpipiSms:
    """Class for connections to the ipipi.com SMS provider. Retrieves the
    authentication parameters from an XML
    """
    
    def __init__(self, fname_auth):
        """Initialize a curl object and gets parameters for authenticating
        with ipipi.com.
        
        @fname_auth:  filename containing the XML authentication parameters
        """
        
        self.curl = pycurl.Curl()
        self.postfields = {}
                    
        # Capture curl output.
        self.post_header= StringIO()
        self.post_response = StringIO()
        self.curl.setopt(pycurl.WRITEFUNCTION, self.post_response.write)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.post_header.write)

        # URL for the ipipi.com API.
        self.curl.setopt(pycurl.URL, IPIPI_API_URL)
        # Use POST method.
        self.curl.setopt(pycurl.POST, 1)

        # Load authentication parameters from XML file.
        self.fname_auth = fname_auth
        self.postfields.update(self.get_auth_ipipi())


    def get_auth_ipipi(self):
        """Extracts authentications parameters from an XML file.
        
        Returns a dict.
        """
    
        try:    
            xml = load_text_file(self.fname_auth)    
        except IOError, msg:
            print "Authentication file not found."
            raise IOError, msg
    
        soup = BeautifulStoneSoup(xml)
        d_auth = {}
        for name in ['token', 'signature']:
            d_auth[name] = soup.find(name).string
            
        return d_auth
    

    def send(self, recipient, message, verbose=False):
        """Sends an SMS using the POST method of ipipi.com's API.
        
        @recipient:  destination phone number
        @message:    text of the message
        @verbose:    show POST result on stdout (default: False)
        """
        
        if verbose:
            self.curl.setopt (pycurl.VERBOSE, 1)    # just for debugging
        else:
            self.curl.setopt (pycurl.VERBOSE, 0)    # be quiet
            
        self.postfields['recipient'] = sanitize_phone(recipient)
        self.postfields['message'] = message
        # Encoding for the message text.
        self.postfields['encoding'] = 'Seven'

        self.curl.setopt(pycurl.POSTFIELDS, urllib.urlencode(self.postfields))
        self.curl.perform()
        self.curl.close()
        
        logging.debug(self.post_response.getvalue())
        
        # Returns True if the API response is OK.
        soup = BeautifulStoneSoup(self.post_response)
        return soup.find('isok').string == u'true'
    




def main():
    """Run when executed as a script.
    """
    
    # Parse command-line.
    opts, ___ = parse_command_line()
    # Set debug level.
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif opts.quiet:
        logging.basicConfig(level=logging.CRITICAL)
    else:
        logging.basicConfig(level=logging.INFO)
    
    sms = IpipiSms(opts.auth_file)
    
    if opts.message:
        message = opts.message
    else:
        # The message is on a file.
        try:
            message = load_text_file(opts.message_file)
        except IOError, msg:
            logging.error("The file containing the message doesn't exists.")
            raise (IOError, msg)

    status = sms.send(opts.phone, message)
        
    if status:
        sys.exit(0)
    else:
        logging.error("SMS not sent. Run with --debug to see details.")
        sys.exit(1)

    
if __name__ == '__main__':
    main()