#! /usr/bin/env python
"""
A script for paging through pickles.
"""
__author__ = "Daniel Casner <www.danielcasner.org/code>"
__version__ = 0.1
from cPickle import Unpickler

def pageThrough(unpickler):
    while True:
        try:
            print unpickler.load()
            cmd = raw_input() # Pause
        except EOFError: break
        if cmd == 'q': break

if __name__ == '__main__':
    from sys import argv
    usage = """
Usage:
    %s PICKLE

Prints out the objects in the pickle one at a time.
""" % argv[0]
    try:
        fh = open(argv[1], 'rb')
    except:
        print usage
        exit(1)
    else:
        try:
            pageThrough(Unpickler(fh))
        finally:
            fh.close()
    
