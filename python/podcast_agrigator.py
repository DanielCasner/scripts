#!/usr/bin/env python
#----------------------------------------------------------------------------
#  Copyright 2009 Daniel Casner <www.danielcasner.org>
#
#  This file is constitutes podcast_agrigator
#
#  podcast_agrigator is free software: you can redistribute it
#  and/or modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3 of
#  the License, or (at your option) any later version.
#
#  podcast_agrigator is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty
#  of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with podcast_agrigator.  If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------------
"""
An RSS feed agrigator specifically for collecting podcasts onto a removeable
device.
"""
__author__ = "Daniel Casner <www.danielcasner.org>"
__version__ = 1.0

import sys, os, getopt, string, urllib, pickle
myName = os.path.splitext(os.path.split(sys.argv[0])[1])[0]
try:
    import feedparser
except ImportError:
    sys.stderr.write("""Error:
%s requires the Universal feedparser library to run.
On ubuntu run:
    sudo apt-get install python-feedparser
to install it. Otherwise it is available from http://feedparser.org
""" % myName)
    if __name__ == '__main__': sys.exit(1)


#### Constants #################################################################

DEFAULT_LIST_FILE = '.' + myName
DEFAULT_DIRECTORY = os.path.curdir
DEFAULT_NUMBER    = 2

USAGE = """ %s
Keeps the most recent N issues of a set of podcasts in a specified directory
such as on a mounted mp3 player.

Usage:
    %s [Special Options] [Options]

Options:
    -f    --file=        Specifies the file containing the list of podcasts
                         subscribed to. If omitted '%s'
                         will be assumed.
    -d    --directory=   Specifies the base directory to download podcasts into.
                         If omitted '%s' will be used.
    -s    --subscribe=   Subscribes to the specified URL.
    -n    --number=      Used with subscribe, specifies the number of issues of
                         the podcast to keep in the directory. Must be specified
                         before '-s' or the default will be used. Default %d. 
    -u    --unsubscribe= Unsubscribe from the specified URL or podcast title.
    -l    --list         Lists the urls for the feeds currently subscribed to
    -o    --override     When subscribing to a feed, override normal checks for
                         RSS validity. Use if absolutely nessisary.
    -h    --help         Prints this help message.
    -v    --verbose      Increases debugging verbosity
    -w    --log          Increase log verbosity when operating in daemon mode.

Special Options:
    --directory-daemon=  Sets up %s to be a daemon which checks
                         periodically to see if the specified directory is
                         mounted and if so updates the feeds. Monitor's argument
                         should be of the form "WAIT1:WAIT2" where WAIT1 is the
                         interval to wait if the directory wasn't availiable
                         when last checked and WAIT2 is the interval to wait if
                         it was availible when last checked.

""" % (myName, sys.argv[0], DEFAULT_LIST_FILE, DEFAULT_DIRECTORY, DEFAULT_NUMBER, myName)


#### Globals ###################################################################
am_daemon = False
verbosity = 1
log_level = 0

#### Program Operation Functions ###############################################

def process_feed(feed):
    "Main program operational method. Processes a single feed."
    # Parse the RSS
    data = feedparser.parse(feed.url)
    if data.bozo and not feed.force:
        sys.stderr.write('Error processing feed "%s", skipping\n' % feed)
        return False
    vwrite('Processing feed "%s"\n' % data.feed.title, 1)

    # Make the appropriate subdirectory if it doesn't exist
    subdir = sanitize_title(feed.title)
    if not os.path.isdir(subdir):
        try:
            os.mkdir(subdir)
        except OSError, inst:
            sys.stderr.write('Error creating subdirectory "%s" for feed "%s" (%s):\n\t%s\n' % (subdir, data.feed.title, feed))
            return False

    # Download the specified number of files
    files = []
    for entry in data.entries[:feed.number]:
        vwrite('  Entry from %s\n' % entry.date, 1)
        for enclosure in entry.enclosures:
            filename = enclosure.href.split('/')[-1]
            pathname = os.path.join(subdir, filename)
            files.append(filename)
            if os.path.isfile(pathname):
                vwrite('    Already on device.\n', 2)
            else:
                vwrite('    Downloading %s\n' % filename, 1)
                dh = urllib.urlopen(enclosure.href)
                wh = file(pathname, 'wb')
                wh.write(dh.read())
                dh.close()
                wh.close()

    # Clean up old files
    vwrite('Cleaning up old files\n', 1)
    for f in os.listdir(subdir):
        if f not in files:
            vwrite('  Removing "%s"\n' % f, 2)
            os.remove(os.path.join(subdir, f))

def run_directory_daemon(directory, list_file, poll_interval, refresh_interval):
    """Checks to see if 'directory' exists every 'poll_interval' seconds and if
    it does, runs process_feed on all subscribed feeds, then sleeps
    'refresh_interval before checking again."""
    startDir  = os.path.abspath(os.path.curdir)
    directory = os.path.abspath(directory)
    while True:
        if os.path.isdir(directory):
            vwrite('%s: Directory present, checking feeds\n' % myName, 2)
            os.chdir(directory)
            for feed in get_feeds(list_file):
                process_feed(feed)
            os.chdir(startDir)
            vwrite('Sleeping for refresh_interval = %d seconds\n' % refresh_interval, 3)
            time.sleep(refresh_interval)
        else:
            vwrite('%s: Directory not present to sleeping for %d seconds\n' % (myName, poll_interval), 2)
            time.sleep(poll_interval)

def subscribe(list_file, subscribeSet):
    "Adds the specified list of feeds to the subscription list in the file"
    feeds = get_feeds(list_file)
    newFeeds = subscribeSet.union(feeds) # Use this order to make sure updates to existing feeds work
    return save_feeds(list_file, newFeeds)

def unsubscribe(list_file, unsubscribeSet):
    "Removes the specified list of feeds from the subscription list in the file"
    feeds = get_feeds(list_file)
    for f in tuple(feeds):
        for u in unsubscribeSet:
            if f.match(u):
                feeds.remove(f)
    return save_feeds(list_file, feeds)

def show_feeds(list_file):
    "Just prints the contents of the specified file"
    feeds = get_feeds(list_file)
    for f in feeds:
        sys.stdout.write('%s\t\t%d\t%s\n' % (f.title, f.number, f.url))

#### Utility Functions and Data Structures #####################################

class Feed(object):
    "A simple structure to store information about a feed"
    def __init__(self, url, number, force=False):
        "Sets up a new feed"
        self.url = url
        self.number = number
        self.force = force
        d = feedparser.parse(url)
        if d.bozo and not force:
            self.bozo = True
            self.title = None
        else:
            self.bozo = False
            self.title = d.feed.title

    def __eq__(self, other):
        "Two feeds are the same if their urls match"
        return other.url == self.url

    def __cmp__(self, other):
        "Follows __eq__"
        return cmp(self.url, other.url)

    def __hash__(self):
        "Follows __eq__"
        return self.url.__hash__()

    def match(self, string):
        "Returns true if string matches either the title or url"
        return string in (self.title, self.url, sanitize_title(self.title))

def get_feeds(file_name):
    "Reads the specified file and returns the set of subscribed feeds"
    try:
        lfh = file(file_name, 'rb')
    except IOError, inst:
        sys.stderr.write('Error opening specified list file "%s":\n\t%s\n' % (file_name, str(inst)))
        return set()
    else:
        try:
            feeds = pickle.load(lfh)
        except Exception, inst:
            sys.stderr.write('Invalid list file "%d"\n' % file_name)
            feeds = set()
        lfh.close()
        return feeds

def save_feeds(file_name, feeds):
    "Saves the set of feeds to the specified file"
    try:
        lfh = file(file_name, 'wb')
        pickle.dump(feeds, lfh, 0)
        lfh.close()
    except Exception, inst:
        sys.stderr.write('Error saving feeds list to file "%s":\n\t%s\n' % (file_name, str(inst)))
        return False
    else:
        return True
    
def sanitize_title(title):
    "Accepts a title and modifies it to be a safe file name."
    acceptable = string.letters+string.digits+' _-'
    return ''.join([c for c in title if c in acceptable])

def vwrite(text, level):
    "Writes text to stdout if verbosity is greater than or equal to level"
    global am_daemon, verbosity, log_level
    test = log_level if am_daemon else verbosity
    if test >= level:
        sys.stdout.write(text)
        sys.stdout.flush()
        return len(text)
    else:
        return 0

#### Program Entry Point #######################################################
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:d:n:s:u:lohvw',
                                   ('directory-daemon=',
                                    'file=',
                                    'directory=',
                                    'number=',
                                    'monitor=',
                                    'subscribe=',
                                    'unsubscribe=',
                                    'list',
                                    'override',
                                    'help',
                                    'verbose',
                                    'log'))
    except getopt.GetoptError:
        sys.stdout.write('Error parsing arguments, try "%s --help"\n' % myName)
    else:
        listFile  = DEFAULT_LIST_FILE
        directory = DEFAULT_DIRECTORY
        number    = DEFAULT_NUMBER
        dirDaemon = False
        subscribeSet = set()
        unsubscribeSet = set()
        showFeeds  = False
        override   = False

        for opt, val in opts:
            if opt in ('-f', '--file'):
                listFile = val
            elif opt in ('-d' , '--directory'):
                if not os.path.isdir(val) and dirDaemon is False:
                    sys.stderr.write('Specified directory ("%s") does not exist!\n' % val)
                    sys.exit(1)
                else:
                    directory = val
            elif opt in ('-n', '--number'):
                try:
                    number = int(val)
                except ValueError:
                    sys.stderr.write('Invalid number argument "%s"\n' % val)
                    sys.exit(1)
            elif opt in ('-o', '--override'):
                override = True;
            elif opt == '--directory-daemon':
                try:
                    waits = [int(w) for w in val.split(':')]
                    assert len(waits) == 2
                    assert all([w > 0 for w in waits])
                except:
                    sys.stderr.write('Invalid directory daemon argument "%s".\nNeeds to be of the form "INT1:INT2" where both INTs are intagers greater than 0\n' % val)
                    sys.exit(1)
                else:
                    dirDaemon = waits
                    import time
            elif opt in ('-s', '--subscribe'):
                f = Feed(val, number, override)
                if f.bozo:
                    sys.stderr.write('"%s" does not seem to be a valid RSS feed and will not be added to the subscription list.\nPlease check it in a web browser.\n' % val)
                else:
                    subscribeSet.add(f)
            elif opt in ('-u', '--unsubscribe'):
                unsubscribeSet.add(val)
            elif opt in ('-l' '--list'):
                showFeeds = True
            elif opt in ('-h', '--help'):
                sys.stdout.write(USAGE)
                sys.exit(0)
            elif opt in ('-v', '--verbose'):
                verbosity += 1
            elif opt in ('-w', '--log'):
                log_level += 1


        if dirDaemon:
            sys.stderr.write('Starting %s in daemon mode\n' % myName)
            am_daemon = True
            run_directory_daemon(directory, listFile, dirDaemon[0], dirDaemon[1])
        else:
            os.chdir(directory)
            if verbosity > 4: sys.stdout.write('Now in directory: %s\n' % os.path.abspath(os.path.curdir))
            if len(subscribeSet):
                if not subscribe(listFile, subscribeSet): sys.exit(1)
            elif len(unsubscribeSet):
                if not unsubscribe(listFile, unsubscribeSet): sys.exit(1)
            elif showFeeds:
                show_feeds(listFile)
            else:
                for feed in get_feeds(listFile):
                    process_feed(feed)
