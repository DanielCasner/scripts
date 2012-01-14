__doc__ = "Lists the contents of a directory and the methods of any python modules contained."
__author__ = "Daniel Casner <www.danielcasner.org>"
__version__ = 0.1

import os
import pyxhtml
import sys

mydir = '/var/wwwssl'

sys.path.insert(0, mydir)

def index():
    page = pyxhtml.webdoc()
    page.title = os.path.abspath(mydir)
    page.body_add('begin')
    page.h1_add('add', {}, page.title)
    page.ul_add('begin')

    for f in os.listdir(mydir):
        if f == 'index.py': pass # Exclude self
        elif f.endswith('.py'):
            page.li_add('add', {}, f)
            try:
                members = [m for m in dir(__import__(f[:-3])) if not m.startswith('__')]
            except ImportError:
                pass
            else:
                page.ul_add('begin')
                for m in members:
                    page.li_add('begin')
                    page.a_add('add', {'href': f + '/' + m}, m)
                    page.li_add('end')
                page.ul_add('end')
	elif f.endswith('.pyc'): pass # Hide python cache files
        else:
            page.li_add('begin')
            page.a_add('add', {'href': f}, f)
            page.li_add('end')
        

    page.ul_add('end')

    page.body_add('end')

    page.make()

    return page.document
