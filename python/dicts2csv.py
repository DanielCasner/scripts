#!/usr/bin/env python

import sys, os

def dicts2csv(dicts):
    csv = []
    keys = dicts[0].keys()
    csv.append(', '.join(keys))
    for d in dicts:
        if d.keys() != keys:
            sys.stderr.write('WARNING Inconsistent fields: %s vs %s\n' % (keys, d.keys()))
        else:
            csv.append(', '.join(d.values()))
    return csv

if __name__ == '__main__':
    try:
        infn, ofn = sys.argv[1:]
    except:
        sys.stdout.write('Usage: %s INFILE OUTFILE\n' % (sys.argv[0],))
    else:
        dicts = [eval(d) for d in file(infn, 'r').read().split(os.linesep) if len(d)]
        csv = dicts2csv(dicts)
        file(ofn, 'w').write(os.linesep.join(csv))
    

