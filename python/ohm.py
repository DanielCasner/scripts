#!/usr/bin/env python
"""Simple implementation of ohm's law"""

def V(i, r):
    "V = I*R Volts"
    return i*r

def I(v, r):
    "I = V/R Amps"
    return v/r

def R(i, v):
    "R = V/I Ohms"
    return v/i

def W(v,i):
    "W = V*I Whatts"
    return v*i

def P(v=None, i=None, r=None):
    "Calculate power (in Whatts) from any two of V, I and R"
    if v is not None and i is not None:
        return W(v,i)
    elif v is not None and r is not None:
        return W(v, I(v,r))
    elif i is not None and r is not None:
        return W(V(i,r), i)
    else:
        raise ValueError, "Not enough arguments to calculate power"

def cap_ser(caps):
    "Calculate the capacitance of a list of capacitors in seriese"
    return 1.0/sum([1.0/c for c in caps])

def cap_par(caps):
    "Calculate the capacitance of a list of capacitors in parallel"
    return sum(caps)

def res_ser(resistors):
    "Calculate the resistance of a list of resistors in seriese"
    return sum(resistors)

def res_par(resistors):
    "Capculate the resistance of a list of resistors in parallel"
    return 1.0/sum([1.0/r for r in resistors])

def E(c, v):
    "Return the energy stored in a given capacitance and voltage."
    return 0.5 * (v**2) * c

def vdiv(top, bottom, voltage=1.0):
    i = I(voltage, top+bottom)
    return V(i, bottom)

if __name__ == '__main__':
    import sys
    print sys.argv
    v=None
    i=None
    r=None
    for a in sys.argv[1:]:
        try:
            arg, val = a.split('=')
        except ValueError:
            continue
        arg = arg.lower()
        if arg == 'v':
            try:
                v = float(val)
            except ValueError:
                sys.stderr.write('Can\'t parse "%s" as a value for voltage.' % val)
                sys.exit(1)
        elif arg == 'i':
            try:
                i = float(val)
            except ValueError:
                sys.stderr.write('Can\'t parse "%s" as a value for current.' % val)
                sys.exit(1)
        elif arg == 'r':
            try:
                r = float(val)
            except ValueError:
                sys.stderr.write('Can\'t parse "%s" as a value for resistance.' % val)
                sys.exit(1)
        else:
            sys.stderr.write('Unexpected argument: "%s=%s"' % (arg, val))
    if v is not None and i is not None:
        sys.stdout.write('R=%f\n' % R(i, v))
        sys.stdout.write('W=%f\n' % W(v, i))
        sys.stdout.write('P=%f\n' % P(i=i, v=v))
    if v is not None and r is not None:
        sys.stdout.write('I=%f\n' % I(v, r))
        sys.stdout.write('P=%f\n' % P(v=v, r=r))
    if i is not None and r is not None:
        sys.stdout.write('V=%f\n' % V(i, r))
        sys.stdout.write('P=%f\n' % P(i=i, r=r))
