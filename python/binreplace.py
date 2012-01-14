#! /usr/bin/env python
"""
This module is useful for replacing strings in mixed binary / text files
particularly python pickles.

Usage:
    binreplace SEARCH REPLACE FILE

Parameters:
    SEARCH    The string to search for.
    REPLACE   The string to replace all occurances of SEARCH with.
    FILE      A mixed binary/text file to make replacements in.
"""
__author__ = "Daniel Casner <www.danielcasner.org/code>"
__version__ = 0.1

import re

def replace(data, search, repl):
    "Replaces all occurances of search with replace in binary data and returns the result."
    r = re.compile(search, 0)
    return r.sub(repl, data)

if __name__ == '__main__':
    from sys import argv
    me = argv.pop(0)
    try:
        (search, repl, file) = argv
    except:
        print "Invalid arguments to %s" % me
        print __doc__
        exit(1)
    try:
        fh = open(file, 'rb')
        data = fh.read()
    except IOError, inst:
        print "Error opening input file: ", inst
        fh.close()
        exit(1)
    try:
        fh = open(file, 'wb')
        fh.write(replace(data, search, repl))
    finally:
        fh.close()
