#!/usr/bin/python

__author__ = "Daniel T. Casner daniel.t.casner@ieee.org"

import urllib
import time
import sys
import getopt

def main(argv):
    "Main function for httping program, parses command line arguments."
    #Default values    
    averaging = False # Default
    averageTimes = 10
    URL = 'http://www.google.com'
    timeout = 5
    verbose = False
    wait = 1
    # Try to parse our arguments
    try:                                
        opts, args = getopt.getopt(argv, "a:hs:t:v")
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)
    # Parse url argument
    if len(args) > 0:
        URL = args[0]
        if URL[:7] != 'http://':
           URL = 'http://' + URL
    # Parse options
    for opt, arg in opts:
        if opt == '-h':
            printHelp()
            sys.exit(0)
        elif opt == '-t':
            try:
                timeout = float(arg)
            except ValueError:
                printHelp()
                sys.exit(2)
        elif opt == '-a':
            try:
                averaging = True
                averageTimes = int(arg)
            except ValueError:
                printHelp()
                sys.exit(2)
        elif opt == '-s':
            try:            
                wait = float(arg)
            except ValueError:
                print "Invalid number of times to average"
                printHelp()
                sys.exit(2)
        elif opt == '-v':
            verbose = True
    # Run
    if verbose:
        print "Starting HTTP ping to " + URL
    if averaging:
        times = []
        av = 0
        while len(times) < averageTimes:
            t = ping(URL)
            av += t
            times.append(t)
            if verbose:
                print "Responce time: " + str(t)
            time.sleep(wait)
        #print "Times were: " + str(times)
        print "Average responce time is: " + str(av/averageTimes) + "\n"
    else:
        while True:
            t = ping(URL)
            print "Responce time: " + str(t)
            if t < timeout:
                print "Got fast responce\nDone.\n"
                break
            time.sleep(wait)

    
def printHelp():
    "Prints out useage instructions for ping+ script"
    print """HTTPing
Pings a URL with HTTP requests.

Usage: httping [options] URL
-a n	try request n times and returns the average responce time. 
-h	print this usage information
-s sec	amount of time to wait between requests in decimal seconds. Default 1 second.
-t sec	specify timeout parameter in decimal seconds. Default 5 seconds.
-v	Verbose output
URL	specify the url to ping. Default www.google.com
"""

def ping(url):
    "Makes an HTTP request and returns the time taken to respond or 10000 if no responce was received"
    try:
        initTime = time.time()
        h = urllib.urlopen(url)
        h.close()
        respT = time.time() - initTime
        return respT
    except EnvironmentError:
        print "No responce"
        return 10000


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print "Aborted by user\n"
	sys.exit(0)
