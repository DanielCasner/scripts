#!/usr/bin/env python
#----------------------------------------------------------------------------
#  Copyright 2009 Daniel Casner <www.danielcasner.org>
#
#  This file is constitutes download.py
#
#  The download.py is free software: you can redistribute it
#  and/or modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3 of
#  the License, or (at your option) any later version.
#
#  download.py is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty
#  of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with download.py.  If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------------
import urllib
import re
import sys
from os.path import split, join
from os import system

__doc__ = """
download.py    Downloads all files of a specific type from a specified website
recusing to a specified depth looking for files to download.

Usage:
    download.py URL FILE_TYPE [MAX_DEPTH [RECURSE_TYPES]]
    
Example:
    download.py www.danielcasner.org pdf 2 html
"""
__author__ = 'Daniel Casner <www.danielcasner.org>'
__version__ = '0.01'

defaultRecurseTypes = ['htm','html','xhtml','shtml','asp','php','xml']

serverRE = re.compile(r'(http://[^/]+)', re.I)

def compileREs(recurseExts, downloadExt):
    """Accepts a list of extensions to recurse over and an extension
to download and returns lists of compiled regular expressions corresponding
to those extensions."""
    recREs = []
    for ext in recurseExts:
        recREs.append(re.compile(r'href="([^<>"]+?\.' + ext + ')"', re.I))
        recREs.append(re.compile(r'src="([^<>"]+?\.' + ext + ')"', re.I))
    downREs = [re.compile(r'href="([^<>"]+?\.' + downloadExt + ')"', re.I),
               re.compile(r'src="([^<>"]+?\.' + downloadExt + ')"', re.I)]
    return recREs, downREs


def recurse(url, downloadREs, maxDepth, recurseREs):
    # Download the page source
    handle = urllib.urlopen(url)
    print 'Opening page ' + url
    page = handle.read()
    handle.close()
    # Split the file name off the url
    (site,junk) = split(url)
    server = serverRE.findall(site)[0]

    # Make a list of things to download
    downloadList = []
    for exp in downloadREs:
        downloadList.extend(exp.findall(page))
    # Download the files
    for uri in downloadList:
        print 'Downloading file ' + uri
        if uri.startswith('/'):
            uri = server + uri
        elif not (uri.startswith('http://') or uri.startswith('ftp://')):
            uri = join(site, uri)
        system("wget '%s'" % uri)
        
    # Now that we've downloaded everything, recurse
    if maxDepth > 0:
        for exp in recurseREs:
            for uri in exp.findall(page):
                if uri.startswith('/'):
                    newURL = server + uri
                elif uri.startswith('http://'):
                    newURL = uri
                else:
                    newURL = join(site, uri)
                recurse(newURL, downloadREs, (maxDepth - 1), recurseREs)

if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print __doc__
        sys.exit(0)
    else:
        depth = 0
        rExts = defaultRecurseTypes
        if len(sys.argv) == 3:
            (url, ext) = sys.argv[1:]
        elif len(sys.argv) == 4:
            (url, ext, depth) = sys.argv[1:]
        elif len(sys.argv) == 5:
            (url, ext, depth) = sys.argv[1:4]
            rExts = sys.argv[4:]
        else:
            print __doc__
            sys.exit(0)
        if not (url.startswith('http://') or url.startswith('ftp://')):
            url = 'http://' + url
        (dres, rres) = compileREs(rExts,ext)
        recurse(url, rres, int(depth), dres)
