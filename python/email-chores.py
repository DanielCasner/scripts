#!/usr/bin/python

__doc__ = """A script to be run from cron to send out weekly chore lists.
Usage:
    python email-chores.py CHORE_FILE.xml
    
All the options are specified in the xml file, use the example as a template.
The number of chores and people can be completely independent and multiple
people can be assigned to a chore. Each person will be rotated over the list
of possible chores.

<?xml version="1.0" ?>
<chores>
    <smtp host="mail.server.net" />
    <sender email="john@server.net" />

    <person name="John" email="john@server.net" lastChore="0" />
    <person name="Mary" email="mary@server.net" lastChore="2" />

    <chore text="Week off" number="0" />
    <chore text="Bathroom cleaning" number="1" />
    <chore text="Kitchen and dinning room cleaning" number="2" />
    <chore text="Livingroom and hallway cleaning" number="3" />
</chores>

"""
__author__ = "Daniel Casner www.danielcasner.org"
__version__ = 1.1

import smtplib
from xml.dom import minidom
from sys import stderr, exit, argv
from time import ctime

# Print help if not specified a file
if len(argv) == 1 or '-h' in argv or '--help' in argv:
    print __doc__
    exit(0)

file = argv[1]

# Try to open the file
try:
    input = minidom.parse(file)
except:
    stderr.writelines("Couldn't parse " + file + "\n")
    exit(1)
    
# Get the info we need
sender = str(input.getElementsByTagName('sender')[0].attributes['email'].value)
smtp_host = str(input.getElementsByTagName('smtp')[0].attributes['host'].value)
chores = input.getElementsByTagName('chore')
people = input.getElementsByTagName('person')


def advanceChore(choreNumber):
    return (choreNumber + 1) % len(chores)

def choreByNumber(choresDomList, n):
    for c in choresDomList:
        if int(c.attributes['number'].value) == n:
            return c.attributes['text'].value
    raise IndexError()


# Get the to addresses
toList = []
toString = ''
for person in people:
    toList.append(str(person.attributes['email'].value))
    toString += str(person.attributes['email'].value) + ', '

missive = "From: %s\r\nTo: %s\r\nSubject: Weekly chore assignments (%s)\r\n\r\n" % (sender, toString, ctime())

# Advance chores and create the messages
for person in people:
    newChoreNum = advanceChore(int(person.attributes['lastChore'].value))
    person.attributes['lastChore'].value = str(newChoreNum)
    missive += "%s: %s\r\n" % (person.attributes['name'].value, choreByNumber(chores, newChoreNum))
fh = open(file, 'w')
fh.write(input.toxml())
fh.close()

# The actual mail send
server = smtplib.SMTP(smtp_host)
smtpresult = server.sendmail(sender, toList, missive)
server.quit()
# Check for errors
if smtpresult:
    errstr = ""
    for recip in smtpresult.keys():
        errstr += ("Could not delivery mail to: " + recip +
                   "\nServer said: " + str(smtpresult[recip][0]) + "\n" +
		    str(smtpresult[recip][1]) + "\n\n")
    stderr.writelines(errstr)
