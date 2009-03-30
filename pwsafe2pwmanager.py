#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pwsafe2pwmanager.py
"""
Parses an XML file exported from MyPasswordSafe. Creates a CSV 
file that can be imported into Pwsafe.

Assumes there's just one level of 'groups' at the original file (no
nested groups).

NOTE: this script is unmaintained and it's status is "works for me". Use at
your own risk.
"""
# Copyright 2009 Jordi Funollet <jordi.f@ati.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import BeautifulSoup, codecs
from optparse import OptionParser




class PwItem(dict):
    """Dictionary describing a password item.

    keys = ('categ', 'descr', 'user', 'password', 'url', 'comment')
    """
    
    def __init__(self, item):
        """Gets an item resulting of parsing with BeautifulSoup an XML 
        export file from MyPasswordSafe."""

        dict.__init__(self)

        self['categ'] = item.parent['name']
        self['descr'] = getattr(item.findNext('name'), 'string', '')
        self['user'] = getattr(item.user, 'string', '')
        self['password'] = getattr(item.password, 'string', '')
        notes = getattr(item.notes.line, 'string', '')
        # Rough try to detect an URL in the "notes" field.
        if 'http://' in notes or 'https://' in notes:
            self['url'] , self['comment'] = notes , ''
        else:
            self['url'] , self['comment'] = '' , notes


    def csv (self):
        """Format as Pwmanager CSV export."""

        # Output format.
        item_csv_tmpl = '''"%(categ)s",,"%(descr)s","%(user)s","%(password)s","%(url)s",,"%(comment)s"'''

        return item_csv_tmpl % self




def soup2csv (soup):
    """Parse every item in the BeautifulSoup object received. Return a
    single string full of CSV lines."""

    groups = soup.findAll('group')
    items_array = [ some_group.findAll('item') for some_group in groups ]
    # Convert every item. The structure is two levels depth.
    csv_list = [ PwItem(some_item).csv() 
                for items_list in items_array for some_item in items_list ]

    return '\n'.join(csv_list)



def main():

    usage = u"""usage: %prog [options]

Parses an XML file exported from MyPasswordSafe. Creates a CSV 
file to import from Pwsafe.

Assumes there's just one level of 'groups' at the original file (no
nested groups)."""
    parser = OptionParser( usage=usage )
    parser.add_option("-i", "--input-file", action="store",
                      default="pwsafe.xml", type="string", metavar="FILE",
                      help="(default: %default)")
    parser.add_option("-o", "--output-file", action="store", 
                      default="import.csv", type="string", metavar="FILE",
                      help="(default: %default)")

    (options, args) = parser.parse_args()


    # Read data.
    xml = open(options.input_file).read()

    # Parse the data.
    soup = BeautifulSoup.BeautifulStoneSoup(xml)
    csv_lines = soup2csv(soup)

    # Write output file. Force writing to UTF-8.
    f_out = codecs.open( options.output_file, 'w', 'utf-8' )
    f_out.write(csv_lines + '\n')


if __name__ == '__main__':
    main()
