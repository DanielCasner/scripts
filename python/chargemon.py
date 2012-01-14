#!/usr/bin/python
"""
chargemon is a simple python program to alert the user when the battery on a Sony Vaio has
finished charging. It can alert the user via printed message and system beep. spicctrl is used
to determine the current battery status.

Usage:
    chargemon.py [interval [level]]
    
Parameters:
    interval sets how many seconds between battery level checks. Default 61 (it's prime).
    level sets the percent charged which should be considered full. Default 100%.
"""
__author__ = 'Daniel Casner <www.danielcasner.org/code>'
__version__ = 0.1

from os import popen
from time import sleep
import re
from sys import argv

## Just make it easy to run stuff through python and get the result
bashrun = lambda cmd: popen(cmd).read()

battcmd = 'spicctrl -p'
spicctrlre = re.compile(r'\s([\d\.]+)%\sAC$')
interval = 61
level = 100.0
notification = """\a
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%% Battery is fully charged. %%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\a"""
# The \a characters are to produce a system beep on systems which support it.

def main(interval, level):
    """Checks the battery status periodically and notifies the user if fully charged and exists.
    interval sets how many seconds between times the program checks the charge level.
    level sets the percentage which should be considered fully charged."""
    chg = float(spicctrlre.findall(bashrun(battcmd))[0])
    print "Present charge level: %0.2f%s" % (chg, r'%')
    while chg < level:
        chg = float(spicctrlre.findall(bashrun(battcmd))[0])
        sleep(interval)
    print notification


if __name__ == '__main__':
    if '-h' in argv or '--help' in argv:
        print __doc__
    else:
        if len(argv) > 1: interval = float(argv[1])
        if len(argv) > 2: level = float(argv[2])
        main(interval, level)
        exit(0)
