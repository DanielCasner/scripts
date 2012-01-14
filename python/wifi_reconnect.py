#!/usr/bin/python
"""
This script is meant to be run by root as a service to attempt to reestablish
wifi connection which go down by automatically calling ifconfig.

Usage:
    python wifi_reconnect.py INTERFACE_NAME CHECK_INTERVAL
    
Parameters:
    INTERFACE_NAME specifies the name of the interface to check the connection
    status of. For example ath0 or wi0.
    
    CHECK_INTERVAL specifies the interval (in seconds, may be decimal) at which
    to check the status of the interface and attempt to reconnect if nessisary.
"""
from os import popen2
from sys import argv, stderr
from time import sleep
from getpass import getuser

if getuser() != 'root':
    sys.stderr.write('This script needs root privledge to run.')

def reconnect(ifname):
    """Attempts to reconnect the specified interface. Return true on success or
    false on faulure."""
    if system('ifdown ' + ifname) == 0:
        return system('ifup ' + ifname) == 0
    else:
        return False
    
def isConnected(ifname):
    "Returns true if the specified interface has an IP address, false otherwise."
    pin, pout = popen2('ifconfig ' + ifname)