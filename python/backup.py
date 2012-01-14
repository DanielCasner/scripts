#!/usr/bin/env python
"""
A python module for creating differential archives with the 'dar' command.
"""
__author__ = 'Daniel Casner <www.danielcasner.org>'
__version__ = 0.01

import sys, os, time, datetime, getopt, re, subprocess

USAGE = """
Usage:
   backup.py [options] SOURCE DEST
   backup.py [options] --merge SOURCE1 SOURCE2 DEST
   
Where SOURCE is the root of the directory tree to be backed up and DEST
is the directory to store the archive in. The backup will be saved in DEST
with name 'YYYY-MM-DD.dar'

In --merge mode archives SOURCE1 and SOURCE2 will be merged into dest.

Options:
    -w  --weekly=   This option with a 0 through 6 will specify a day of the
                    week that a complete backup should be made, archive made on
                    any other day will reference the most recent complete
                    backup.
    -m  --monthly=  As with -w except the number should be 1-31 and specifies
                    that complete backups should occur only monthly.
    -r  --remove=   Specify an age in number of days for backs to be removed
                    after. If combined with -w or -m, complete backups will
                    only be removed after all referencing backups have been
                    removed first.
    -p  --password  Specify an encryption key to apply to the archive with the
                    blowfish algorithm. Will use getpass to ask for the password
                    interactively. 
    -k  --key=      As with -p except a file name is specified, the first line
                    of which will be read and used as the password.
    -v  --verbosity Increment the debugging verbosity.
"""

#### Globals and Constants #####################################################
verbosity = 0

UNCOMPRESSED_MASKS = ['*.mp3', '*.ogg', '*.wma', '*.aac', '*.m4a', # Compressed music
                      '*.avi', '*.mov', '*.mpg', '*.mpeg', '*.wmv', # Compressed video
                      '*.jpg', '*.png', '*.gif', # Compressed images
                      '*.zip', '*.bz2', '*.gz', '*.tgz', '*.tbz', '*.rar', '*.jar', '*.egg'] # Archives
UNCOMPRESSED_MASKS += [m.upper() for m in UNCOMPRESSED_MASKS]

EXCLUDE_MASKS = ['.Trash*', '.thumbnails', 'tmp', 'download', '*~', '.*~', '#*', '%*']

DATENAME_RE = re.compile(r'^(\d\d\d\d)-(\d\d)-(\d\d).*\.dar$')

#### General Utility Functions #################################################
def vwrite(text, level):
    "Writes text to stdout if verbosity is greater than or equal to level"
    global verbosity
    if verbosity >= level:
        sys.stdout.write(text)
        sys.stdout.flush()
        return len(text)
    else:
        return 0

def archiveBase(date, directory=''):
    """Constructs the appropriate base path/name for an archive on a given
    date in the given directory."""
    return os.path.join(directory, '%04d-%02d-%02d' % date.timetuple()[:3])

#### Dar command wrapper #######################################################

def dar(name, root, compression=9, reference=None, key=None,
        exclude_masks=EXCLUDE_MASKS, uncompressed_masks=UNCOMPRESSED_MASKS):
    "Wrapper function for the dar command"
    vwrite('Creating dar archive of "%s" with base name "%s"\n' % (root, name), 2)
    command = ['dar']
    command += ['-c' + name]
    command += ['-y%d' % compression]
    command += ['-Z' + mask for mask in uncompressed_masks]
    command += ['-R' + root]
    command += ['-X' + mask for mask in exclude_masks]
    if key is not None:
        command.append('-Kbf:' + key)
    if reference is not None:
        command.append('-A' + reference)
        if key is not None: command.append('-Jbf:' + key)
    vwrite('\t%s\n' % ' '.join(command), 3)
    return subprocess.call(command) == 0

def merge(a1, a2, r, key=None):
    "Merges archives a1 and a2 into r"
    vwrite('Merging archives %s and %s into %s...\n' % (a1, a2, r), 2)
    command = ['dar', '-ak']
    command += ['-A ' + a1,]
    if key is not None: command.append('-Jbf:' + key)
    command += ['-@ ' + a2]
    if key is not None: command.append('-Jbf:' + key)
    if key is not None: command.append('-Kbf:' + key)
    command += ['-+ ' + r]
    vwrite('\t%s\n' % ' '.join(command), 3)
    return subprocess.call(command) == 0
    

#### Program Entry Point #######################################################
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'w:m:r:pk:hv', (
            'merge'
            'weekly=',
            'monthly=',
            'remove=',
            'password',
            'key=',
            'help',
            'verbosity'
            ))
    except getopt.GetoptError:
        sys.stderr.write('Error parsing arguments. Try "%s --help"\n' % sys.argv[0])
        sys.exit(1)
    else:
        diffMode = (None, -1)
        remove   = None
        password = None
        merge = False

        # Parse through the options
        for opt, val in opts:
            if opt in ('-h', '--help'):
                sys.stdout.write(USAGE)
                sys.exit(0)
            elif opt == '--merge':
                merge = True
            elif opt in ('-w', '--weekly'):
                try:
                    dow = int(val)
                    assert 0 <= dow <= 6
                except:
                    sys.stderr.write('Incorrect value specified for --weekly option.\nMust be an intager between 0 and 6.\n')
                    sys.exit(1)
                else:
                    diffMode = ('w', dow)
            elif opt in ('-m', '--monthly'):
                try:
                    dom = int(val)
                    assert 1 <= dom <= 31
                except:
                    sys.stderr.write('Inccorect value specified for --monthly option.\nMust be an intager between 1 and 31.\n')
                    sys.exit(1)
                else:
                    diffMode = ('m', dom)
            elif opt in ('-r', '--remove'):
                try:
                    remove = int(val)
                    assert remove > 0
                except:
                    sys.stderr.write('Incorrect value specified for --remove option.\nMust be a positive intager.\n')
                    sys.exit(1)
            elif opt in ('-p', '--password'):
                from getpass import getpass
                password = getpass('Encryption key: ')
                if not password:
                    sys.stderr.write('No password seems to have been specified, bailing out.\n')
            elif opt in ('-k', '--key'):
                try:
                    kfh = file(val, 'r')
                    password = kfh.readline().strip()
                except IOError, inst:
                    sys.stderr.write('Error reading specified key file "%s":\n\t%s\n' % (val, str(inst)))
                    sys.exit(1)
                kfh.close()
            elif opt in ('-v', '--verbosity'):
                verbosity += 1

        if merge:
            if len(args) != 3:
                sys.stdwrr.write('Wrong number of arguments for a merge. Try "%s --help"\n' % sys.argv[0])
                sys.exit(2)
            else:
                merge(*args)
        elif len(args) != 2:
            sys.stderr.write('Wrong number of arguments. Try "%s --help"\n' % sys.argv[0])
            sys.exit(2)
        else:
            root, dest = args

            assert False # Make sure there is a static copy of Dar of the same version as being used to compress

            # Run the backup
            today = datetime.date.today()
            darName   = archiveBase(today, dest)
            reference = archiveBase(today - datetime.timedelta(1), dest)

            # Make a complete backup if today is a day to do so
            if (diffMode[0] is None) or \
               (diffMode[0] == 'w' and today.weekday() == diffMode[1]) or \
               (diffMode[0] == 'm' and today.day == diffMode[1]) or \
               (not any((f.startswith(os.path.split(reference)[1]) for f in os.listdir(dest)))):
                vwrite("Creating full backup\n", 1)
                dar(darName, root, key=password)
            else:
                vwrite("Creating differential backup\n", 1)
                dar(darName, root, reference=reference, key=password)
            if remove:
                archives = [DATENAME_RE.match(f) for f in os.listdir(dest)]
                for a in [datetime.date(*[int(d) for d in a.groups()]) for a in archives if a is not None]:
                    if a < today - datetime.timedelta(remove):
                        os.remove(a)
                

