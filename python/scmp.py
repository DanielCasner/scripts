#!/usr/bin/env python
"""
SCMP -- Ssh Caching Music Player
A program for playing music stored on a remote unix server by downloading it
through ssh, caching it and playing it through mplayer.
"""
__author__ = 'Daniel Casner <www.danielcasner.org>'
__version__ = 0.3

## Features to add:
# Start python process on server to allow get more information about file system and use a single ssh connection
# Cached only option
# Cache database with information on file dates etc. to allow resyncronization and deletion
# UI client architecture

import sys, getopt, subprocess, re, random, os, time

verbosity = 0
lookahead = 2
storeDir = os.path.join(os.environ['HOME'], '.scmp')
cacheDir = os.path.join(storeDir, 'cache')
playlistTypes = ['.pls', '.m3u']
player = 'mplayer'
sys.null = file(os.devnull, 'r+') # Sys should include dev null but doesn't

USAGE = """
SCMP -- Ssh Cachine Music Player

Usage:
    %s [options] HOST {DIRECTORY|PLAYLIST [REMOTE_ROOT]}
    %s {-c|--clear}

Copies files from HOST or uses a locally cached copy in %s if it
exists. The music files to play are selected from either DIRECTORY on the
remote host or a local playlist if the argument's extension is a recognized
playlist format %s.

Options:
    -s      --shuffle   Shuffles the contents of DIRECTORY or PLAYLIST rahter
                        than playing in order.
    -e      --player    Specify an alternate player, default: "%s"
    -l      --lookahead The number of tracks to download in advance, default %d
    -d      --cache     Specify where to cache downloaded files.
    -c      --clear     Clears the cache directory removing all files stored
                        there.
    -v      --verbose   Increment verbosity

""" % (sys.argv[0], sys.argv[0], storeDir, str(playlistTypes), player, lookahead)
# Add cached only option

def main(args):
    global verbosity
    global lookahead
    global storeDir
    global cacheDir
    global playlistTypes
    global player
    shuffle = False
    try:
        opts, args = getopt.getopt(args[1:], 'hse:l:d:vc', ('help', 'shuffle', 'player=', 'lookahead=', 'cache=', 'verbose', 'clear'))
    except getopt.GetoptError:
        sys.stderr.write("""Error parsing arguments, try "%s --help"\n""" % sys.argv[0])
        return 1
    for opt, val in opts:
        if opt in ('-h', '--help'):
            sys.stdout.write(USAGE)
            return 0
        elif opt in ('-c', '--clear'):
            return clearCache()
        elif opt in ('-v', '--verbose'):
            verbosity += 1
        elif opt in ('-s', '--shuffle'):
            shuffle = True
        elif opt in ('-e', '--player'):
            player = val
        elif opt in ('-l', '--lookahead'):
            try:
                lookahead = int(val)
            except ValueError:
                sys.stderr.write('Invalid lookahead value: "%s"\n' % val)
                return 1
        elif opt in ('-d', '--cache'):
            if os.path.isdir(val):
                cacheDir = val
            else:
                sys.stderr.write('"%s" is not a valid directory, cannot use for caching' % val)
                return 1
    if len(args) < 2:
        sys.stderr.write("Invalid arguments:\n\t%s\n\n" % ' '.join(args))
        sys.stderr.write(USAGE)
        return 1
    host, what = args[:2]
    listGen = None
    for ext in playlistTypes:
        if what.endswith(ext):
            dbg(2, """Seems we've been given a "%s" playlist file""" % ext)
            listGen = playlistGenerator(what, ext, shuffle, args[2] if len(args) >= 3 else '')
            break
    if listGen is None:
        dbg(2, "Seems we've been given a remote directory to play from")
        if what.startswith('..'):
            sys.stderr.write('Remote directory must not be specified with ".."\n')
            return 2
        else:
            listGen = directoryGenerator(what, host, shuffle)
    dbg(1, 'Argment parsing successful, starting...')
    dbg(2, 'Using "%s" as play command' % player)
    player = player.split()
    
    if not os.path.isdir(storeDir):
        dbg(1, 'Program store directory does not exist, creating "%s"' % storeDir)
        os.mkdir(storeDir)
    if not os.path.isdir(cacheDir):
        dbg(1, 'Cache directory does not exist, creating "%s"' % cacheDir)
        os.mkdir(cacheDir)

    dbg(0, "Downloading first file...")
    downloadProc = Download(host, listGen.next(), stdout=sys.stdout)
    if downloadProc.finish() != 0: die('Error downloading first file "%s"' % downloadProc.file, downloadProc.result)
    playList = []
    downloadProc.addToPlaylist(playList)
    playProc = subprocess.Popen(player + [playList.pop(0)])
    noMore = False
    dbg(2, "Entering main loop")
    while True:
        try:
            if downloadProc.done:
                downloadProc.addToPlaylist(playList)
                if len(playList) < lookahead:
                    try: downloadProc = Download(host, listGen.next())
                    except StopIteration: noMore = True
            
            if playProc.poll() is not None:
                if playList:
                    playProc = subprocess.Popen(player + [playList.pop(0)])
                elif downloadProc:
                    sys.stdout.write("Please wait for the next file to download\n")
                    downloadProc.finish()
                if noMore:
                    break

            time.sleep(0.01)

        except KeyboardInterrupt:
            break


def dbg(level, string):
    "Prints the string to stdout if verbosity is greater than or equal to level"
    global verbosity
    if verbosity >= level:
        sys.stdout.write(string + '\n')

def die(txt, status=1):
    "Prints an error message and exits with error status"
    sys.stderr.write(txt + '\n')
    exit(status)

def playlistGenerator(filename, typ, shuffle, remoteDir=''):
    if typ == '.pls':
        dbg(2, "Interpreting the playlist file as PLS format")
        parser = re.compile(r'^File\d+=(.+)')
    elif typ == '.m3u':
        dbg(2, "Interpreting the playlist file as M3U (simple) format")
        parser = re.compile(r'^(.+)$')
    else:
        die("Unknown playlist type")
    dbg(2, 'Attempting to open playlist file "%s"' % filename)
    try:
        fh = file(filename, 'r')
        playlist = fh.read().split('\n')
    except IOError:
        die("Could not open playlist file!")
    fh.close()
    if shuffle:
        dbg(3, 'Shuffling the playlist')
        random.shuffle(playlist)
    for f in playlist:
        yield os.path.join(remoteDir, parser.findall(f)[0])
    
def directoryGenerator(dir, hostname, shuffle):
    dbg(1, 'Attempting to connect to host %s to list directory "%s"' % (hostname, dir))
    try:
        findProc = subprocess.Popen(['ssh', hostname, 'find "%s"' % os.path.join(dir, '')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #retcode = findProc.wait() # This causes strange behavior on FreeBSD 6.3
        files, error = findProc.communicate()
    except Exception, inst:
        die('Exception while trying to list files in directory "%s" on host "%s":\n%s' (dir, host, str(inst)))
    if findProc.poll() != 0:
        die("Error listing files in directory on server: " + error, findProc.poll())
    elif files:
        dbg(4, 'File list: ' + files)
        playlist = files.split('\n')
        if shuffle:
            dbg(3, 'Shuffling the playlist')
            random.shuffle(playlist)
        for f in playlist:
            if f.endswith(os.path.sep): continue # Is a directory
            elif not os.path.splitext(f)[1]: continue # Has no file extesion so probably a directory
            elif not f: continue # No file at all
            else: yield f

def clearCache():
    "Removes all files from the cache directory"
    return subprocess.call(['rm', '-rf', cacheDir])

class Download(object):
    "A class to represent a downloading, cached or downloaded file"
    __slots__ = ['host', 'file', 'complete', 'added', 'proc', 'result']

    executible = 'scp'

    def __init__(self, hostname, file, stdout=sys.null):
        "Initalizes the download"
        self.host = hostname
        self.file = os.path.join(cacheDir, hostname, file)
        self.added = False
        # Check to see if we have a cached copy
        if self.isCached:
            dbg(2, 'Found cached file "%s"' % self.file)
            self.complete = True
        else:
            self.complete = False
            # If not start download
            try:
                # Make the directory to cache the file in
                dir, fn = os.path.split(self.file)
                dbg(3, 'Download.mkdir(%s)' % dir)
                self.mkdir(dir.split(os.path.sep))
                # Formulate the arguments to download it
                args = [self.executible, '%s:"%s"' % (hostname, file), self.file]
                # And start the download
                dbg(3, 'Starting download command: "%s"' % ' '.join(args))
                self.proc = subprocess.Popen(args, stdin=sys.null, stdout=stdout, stderr=stdout)
            except Exception, inst:
                self.die(inst)

    def __del__(self):
        "Called when the object is destructed"
        self.proc = None # Kill the process if it is still running
        if not self.complete: self.rm()
        
    def die(self, inst):
        "Object specific die command"
        die('Error creating download subprocess to download file "%s" from "%s":\n%s' % (self.file, self.host, str(inst)))

    @classmethod
    def mkdir(cls, tree):
        "Recursively makes the required directory to cache the file"
        if tree:
            if tree[0] == '': tree[0] = os.path.sep
            dir = os.path.join(*tree)
            if not os.path.isdir(dir):
                cls.mkdir(tree[:-1])
                os.mkdir(dir)

    def finish(self):
        "Blocks till the download finishes"
        if not self.complete:
            try:
                self.result = self.proc.wait()
            except Exception, inst:
                self.die(inst)
            else:
                self.complete = True
                return self.result
        else:
            return 0

    @property
    def isCached(self):
        "Figures out if the file is cached or not"
        return os.path.isfile(self.file)


    @property
    def done(self):
        "Returns whether the download has completed yet or not"
        if self.complete:
            return True
        elif self.proc.poll() is None:
            return False
        else:
            self.complete = (self.proc.poll() == 0)
            return True

    def addToPlaylist(self, playlist):
        "Adds the file to the end of playlist if it isn't present already"
        if self.complete and not self.added:
            dbg(3, 'Appending file "%s" to the playlist %s' % (self.file, str(playlist)))
            playlist.append(self.file)
            self.added = True

    def rm(self):
        "Deletes the file from cache, useful for killing incomplete downloads"
        if not os.path.isdir(self.file): os.remove(self.file)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
