#!/usr/bin/python

# Copyright (C) 2007 Daniel Casner 
# www.danielcasner.org
#
# This work is licensed under a Creative Commons Attribution-Noncommercial-
# Share Alike 3.0 United States License. See:
#     http://creativecommons.org/licenses/by-nc-sa/3.0/us/
# for details. My name and / or a link to www.danielcasner.org must be
# maintained if you use this module or create a derivative work which copies
# code substantially from this module.
#
# Questions regarding comertial use of the software should be directed to the
# author at daniel@danielcasner.org
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. 


import sys, os, re, time, getopt, ftplib, getpass

__author__ = "Daniel Casner <daniel@danielcasner.org>";
__doc__ = """'Author Side Include (ASI)' -- for HTML files
A substitute for SSI for people who's servers don't support SSI.
This script processes the apache "#include file" and "#flasmod file" directives
and uploads the resultant files to an FTP server. Alternately, the processed
files can be placed in a local directory. Like Make, processing starts in the
current directory.
A meta file ".asi.timestamp" is used to keep track of which files have been
updated since the last time the script was run.

Usage:
    asi.py [-h|--help]
        Prints these usage instructions
    asi.py {-f <FTP hostname and path>|-o <output director>} [<other options>]
        Normal operation, either -f or -o must be specified.
        
Example:
    $ asi.py -f ftp.example.com/root -u webmaster -p l0rdofth3pages

Options:
    -a    --all         Upload all files newer than the time stamp, not just
                        html files.
    -f    --host=       FTP hostname and path
    -h    --help        Prints these usage directions instead of processing
    -o    --output=     A local director
    -p    --password=   Remote password, if -f is specified and -p is omitted
                        you will be promted for a password before uploading.
    -u    --user=       Remote username, if -f is specified and -u is omitted
                        the remote user name is assumed to be the same as the
                        local one.
          
Include commands:
The following commands are supported in xhtml files:
    <!--#flastmod file="foo.html" -->
        Inserts the file modified time of foo.html
    <!--#include file="bar.html" -->
        Inlines the contents of bar.html
        Note: Only one level of include is supported at the present time, i.e.
        you can't have a "#include file=..." inside the file you're including.
In both cases the path must be relitive to the xhtml file being processed.
"""
__version__ = 2.3

TIME_STAMP_FILE = '.asi.timestamp'
#timefmtExp  = re.compile(r'<!--\s*#config\s+timefmt="%A %B %d, %Y"\s*-->') Not yet implimented
extExp = re.compile(r'\w+\.[sx]{0,1}htm[l]{0,1}$')
includeExp  = re.compile(r'<!--\s*#include\s+file="(\S+)"\s*-->')
flastmodExp = re.compile(r'<!--\s*#flastmod\s+file="(\S+)"\s*-->')

def main(argv):
    """This is the main method for the ASI script. Accepts the arguments after
    the program name (typically sys.argv[1:]), parses arguments, sets up 
    options and runs the program."""
    try:                                
        opts, args = getopt.getopt(argv, "af:o:p:u:h", ('all', 'host=', 'output=', 'password=', 'user=', 'help'))
    except getopt.GetoptError:
        sys.stderr.write('ASI: Error parsing argument!\nTry\n\tasi.py --help\n')
        sys.exit(2)
    else:
        if len(opts) == 0:
            sys.stdout.write(__doc__)
            sys.exit(0)
        if len(args):
            sys.stderr.write('ASI: Unknown input arguments\n\t')
            sys.stderr.writelines(args)
            sys.stderr.write('Try\n\tasi.py --help\n')
            sys.exit(2)
        else:
            # Initalize some default values
            meta = {
                'all': False,
                'hostname': None,
                'out dir': os.path.normpath('o'),
                'password': None,
                'user': getpass.getuser()
            }
            # Run through the arguments
            for opt, val in opts:
                if opt == '-h' or opt == '--help':
                    sys.stdout.write(__doc__)
                    sys.exit(0)
                elif opt == '-a' or opt == '--all':
                    meta['all'] = True
                elif opt == '-f' or opt == '--host':
                    parts = val.split('/')
                    meta['hostname'] = parts[0]
                    if len(parts) > 1:
                        meta['remote dir'] = '/' + '/'.join(parts[1:])
                    else:
                        meta['remote dir'] = '/'
                elif opt == '-o' or opt == '--output':
                    if os.path.isdir(val) or raw_input('Output directory "%s" does not exist. Should I create it? ' % val).lower().startswith('y'):
                            meta['out dir'] = os.path.normpath(val)
                    else:
                        sys.stderr.write('ASI: Invalid output directory!\n')
                        sys.exit(1)
                elif opt == '-p' or opt == '--password':
                    meta['password'] = val
                elif opt == '-u' or opt == '--user':
                    meta['user'] = val
            # If we've had a remote host specified but no password
            if meta['hostname']:
                if not meta['password']:
                    meta['password'] = getpass.getpass('Remote password: ')
                try:
                    meta['FTP'] = ftplib.FTP(meta['hostname'], meta['user'], meta['password'])
                    meta['FTP'].cwd(meta['remote dir'])
                except:
                    sys.stderr.write('ASI: Error connecting to "%s" remote directory "%s"\n' % 
                                     (meta['hostname'], meta['remote dir']))
                    sys.exit(1)
            if not os.path.isdir(meta['out dir']):
                try:
                    os.mkdir(meta['out dir'])
                except:
                    sys.stderr.write('ASI: output directory does not exist and could not be created!\n')
                    sys.exit(1)
            # Check the time stamp
            if os.path.isfile(TIME_STAMP_FILE):
                try:
                    meta['last time'] = getFileTime(TIME_STAMP_FILE)
                except:
                    sys.stderr.write('ASI: %s invalid!\n' % TIME_STAMP_FILE)
                    meta['last time'] = 0.0
            else:
                meta['last time'] = 0.0
            
            for path, dirs, fnames in os.walk(os.path.curdir):
                for d in dirs:
                    if os.path.normpath(d) == meta['out dir'] or d == '.svn': dirs.remove(d)
                for name in fnames:
                    if path.startswith('./'): path = path[2:]
                    if getFileTime(os.path.join(path,name)) > meta['last time']:                        
                        if extExp.match(name):
                            it = procFile(name, path, meta)
                            # Upload if requested
                            if meta['hostname']:
                                
                                upload(meta['FTP'], os.path.join(meta['remote dir'], path).replace(os.path.sep, '/'), it)
                        elif os.path.isfile(os.path.join(path, name)) and meta['all'] and meta['hostname'] and name != TIME_STAMP_FILE and not name.endswith('~'):
                            upload(meta['FTP'], os.path.join(meta['remote dir'], path).replace(os.path.sep, '/'), os.path.join(path, name))
            
            # Close the FTP connection if itwas open
            if meta['hostname']: meta['FTP'].close()
            # Update the time stamp
            try:
                file(TIME_STAMP_FILE, 'w').close()
            except IOError: sys.stderr.write('ASI: could not create meta file!\n')
            # Print friendly message
            sys.stdout.write('All files processed successfully.\n')

def getFileTime(file):
    "Returns the modified time of a file."
    return os.stat(file).st_mtime

def pathJoin(p1, p2):
    """Does a somewhat smarter join of two path elements than os.path.join
    Specifically it handles '..' correctly."""
    parts1 = p1.split(os.path.sep)
    parts2 = p2.split(os.path.sep)
    while parts2[0] == os.path.pardir:
        parts1 = parts1[:-1]
        parts2.remove(os.path.pardir)
    return os.path.sep.join(parts1 + parts2)


def procFile(name, path, opts):
    """Processes a file from os.path.walk. Accepts the file name, path and
    options hash."""
    file = os.path.join(path, name)
    sys.stdout.write("Processing file: %s\n" % file)
    try:
        # Read in the file
        try:
            FH = open(file, 'r')
            content = FH.read()
            FH.close()
        except IOError, inst:
            sys.stderr.write('Error processing file: %s\n' % str(inst))
        # Process the file
        content = includeExp.sub((lambda m: include(m, path)), content)
        content = flastmodExp.sub((lambda m: flastmod(m, path)), content)
        # Write the file
        outFile = os.path.join(opts['out dir'], file[2:]) # Strip the ./
        outPath, outName = os.path.split(outFile)
        if not os.path.isdir(outPath): os.mkdir(outPath)
        try: 
            FH = open(outFile, 'w')
            FH.write(content)
            FH.close()
        except IOError, inst:
            s.stderr.write('Error processing file: %s\n' % str(inst))
        return outFile
    except IOError, e:
        sys.stderr.write('IO exception while processing "%s": %s\n' % (file, e))
        return None
    
def include(match, path):
    """Accepts a _sre.SRE_Match object and a base path and processes the
    "#include file=..." directive."""
    retval = ''
    incFile = pathJoin(path, os.path.normpath(match.groups()[0]))
    try:    
        fh = open(incFile, 'r')
        try:
            retval = fh.read()
            fh.close()
        except IOError, inst:
            sys.stderr.write('IO Exception while reading file: %s\n' % str(inst))
    except IOError, inst:
        sys.stderr.write("IO exception while trying to include %s: %s\n" % (incFile, str(inst)))
    return retval

def flastmod(match, path):
    """Perform a stat on the specified, convert the modified time
    to a human readible format and return said string."""
    statFile = pathJoin(path, os.path.normpath(match.groups()[0]))
    try:
        return time.ctime(os.stat(statFile).st_mtime)
    except OSError:
        print "Couldn't find last updated time for %s\n" % statFile
        
def upload(FTP, remotePath, filePathname):
    """Uploads the file stored at filePathname to the remote directory
    remotePath on FTP connection FTP."""
    sys.stdout.write('Uploading "%s"...\n' % filePathname)
    def ccd(path):
        try: FTP.cwd(path)
        except ftplib.error_perm, e:
            sys.stdout.write('Couldn\'t CD to "%s," adjusting directory name.\n' % path)
            d = path.split('/')
            if d[0] == '':
                d[0] = '/' + d[1]
            try: FTP.cwd(d[0])
            except:
                sys.stdout.write('Creating remote directory "%s"\n' % d[0])
                FTP.cwd(FTP.mkd(d[0]))
            if len(d) > 1:
                ccd('/'.join(d[1:]))
    ccd(remotePath)
    fh = open(filePathname, 'rb')
    try:
        FTP.storbinary('STOR %s' % os.path.basename(filePathname), fh)
    except Exception, e:
        sys.stderr.write('Error uploading file "%s":\n\t%s\n' % (filePathname, e)) 
    fh.close()
    

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
        sys.stdout.write('Done :-)\n\n')
    except KeyboardInterrupt:
        sys.stderr.write("Aborted by user\n")
        sys.exit(1)
