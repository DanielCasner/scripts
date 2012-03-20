'''
Created on Mar 7, 2012

@author: dtcasne
'''

PREFIXES = {
    'H': 1e27, # Hella-
    'Y': 1e24,
    'Z': 1e21,
    'E': 1e18,
    'P': 1e15,
    'T': 1e12,
    'G': 1e9,
    'M': 1e6,
    'k': 1e3,
    'K': 1e3, # kilo is sometimes capitalized
    'h': 1e2,
    'da': 1e1,
    'd': 1e-1,
    'c': 1e-2,
    'm': 1e-3,
    'u': 1e-6, # micro is sometimes 'u'
    u'\xb5': 1e-6, # and sometimes mu
    'n': 1e-9,
    'p': 1e-12,
    'f': 1e-15,
    'a': 1e-18,
    'z': 1e-21,
    'y': 1e-24,
}

PREFIX_RE_SET = u'[HYZEPTGMkKhdcmu\xb5npfazy]' # Does not recognize da because it's two letters and no one uses it anyway