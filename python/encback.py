#!/usr/bin/env python
"""
Encrypted backup
Run this program to create an encrypted backup copy of a directory on a remote
machine via ssh. A locally stored pickle keeps track of the last version of each
file in the tree which has been sent to the server so on future executions only
updates are sent.

Usage:
    encback.py [options] SSH_HOST:BACKUP_STORE_PATH [DIRECTORY]

The first argument specifies the ssh host (and username with "@" syntax if
nessisary) followed by a colon and the path to be the root of the backup.

If DIRECTORY is omitted, the current directory is assumed.

Options:
    -x --exclude    Ignore subdirectories with the specified name. May be
                    specified more than once.
    -d --die        Die on error rather than continuing
    -v --verbose    Increase verbosity, may be specified more than once.
"""
__author__ = 'Daniel Casner <www.danielcasner.org>'
__version__ = '0.01'

import sys, os, subprocess, cPickle as pickle, threading

verbosity = 0

class Server(object):
    """Represents a connection to the ssh server where the backup will be stored
    and has methods for storing data, creating dirs etc."""

    def __init__(self, host):
        try:
            hostname, hostdir = host.split(':')
        except:
            raise ValueError, 'Invalid host, directory argument "%s"' % host
        else:
            self.top = hostdir
            pass

    def __del__(self):
        pass

    def pruneDirs(self, dirpath, subdirs):
        "Prunes subdirectories in dirpath to match subdirs"
        pass

    def mkdir(self, dirpath, directory, errorIfExists=False):
        "Creates a subdirectory in dirpath if it doesn't exist"
        # Test if dir exists
        # Create if it does not
        # ? error if it does

    def pruneFiles(self, dirpath, files):
        "Prunes files in dirpath to match files list"
        pass

    def encryptAndUploadFile(self, remotePath, filename, localPathname, callback, param):
        """Encrypts and uploads he file and calls callback with the success
        state and param when done"""
        pass


def runBackup(host, excludeDirs=[] dieOnError=False):
    """Runs the backup logic in the current directory and sends data to the
    server."""
    state = initState(root)
    server = Server(host)

    def errorCB(exception):
        "Called when os.listdir has an error"
        if dieOnError: raise exception
        else sys.stderr.write(str(exception))

    def uploadCompleteCB(success, param):
        "Called by server object thread when a file upload completes"
        if success: state[param[0]] = param[1]
        else:
            sys.stderr.write('Uploading file "%s" failed!' % param[0])
            if dieOnError: return

    for dirpath, subdirs, files in os.walk(os.path.curdir, True, errorCB):
        # Filter out excluded directories.
        for d in excludeDirs:
            if d in subdirs: subdirs.remove(d)
        # Removes directory trees from the server which aren't on the local side
        server.pruneDirs(dirpath, subdirs)
        # Make remote dirs if they don't exist
        for d in subdirs: server.mkdir(dirpath, d, False)
        # Delete files from server if they don't exist locally
        server.pruneFiles(dirpath, files)
        # Backup all the files
        for f in files:
            fullname = os.path.join(dirpath, f)
            try:
                fh = file(fullname, 'rb')
                check = md5.new(fh.read()).digest()
            except Exception, inst:
                errorCB(inst)
                fh.close()
                continue
            else:
                fh.close()
                if state.has_key(fullname) and state[fullname] == check:
                    continue
                else:
                    server.uploadFile(dirpath, f, fullname,
                                      encryptAndUploadCompleteCB, (fullname, check))

    server.waitForFinish()
        

def initState(directory):
    """Attempts to load the state pickle from a previous backup. Failing that it
    initalizes a new state."""
    fileName = '.encback.state'
    try:
        fh = file(os.path.join(directory, fileName), 'rb')
        loader = pickle.Unpickler(fh)
        state = loader.load()
        fh.close()
    except:
        state = {} # Initalize new state
    return state


if __name__ == '__main__':
    # Add option parsing
    args = sys.argv[1:]
    if len(args) == 0 || len(args) > 2:
        system.out.write(__doc__)
    else:
        host = args[0]
        if len(args) > 1: os.chdir(args[1])
        runBackup(host)

