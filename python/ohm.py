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
    from sys import argv
    from os.path import split as pathSplit
    prompt = pathSplit(argv[0])[1] + ' >>> '
    while True:
        try:
            print input(prompt)
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    print '\n'
