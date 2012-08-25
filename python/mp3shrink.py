#!/usr/bin/env python
__doc__ = """
----------------------------------------------------------------------------
  This file is constitutes mp3shrink

  mp3shrink is free software: you can redistribute it
  and/or modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation, either version 3 of
  the License, or (at your option) any later version.

  mp3shrink is distributed in the hope that it will be
  useful, but WITHOUT ANY WARRANTY; without even the implied warranty
  of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with mp3shrink.  If not, see <http://www.gnu.org/licenses/>.
----------------------------------------------------------------------------
 This is an update of my earlier perl script for reencoding MP3s at a
 different bit rate. It now uses FFMPEG to make everything much simpler.
 I was hoping to accomplish this task entirely with bash scripts but bash
 just isn't up to handling the path names that are leagal in OSX.
"""
__author__ = "Daniel Casner <www.danielcasner.org>"
__version__ = "1.0"

import sys, os, time, subprocess, getopt

USAGE = """
%s [options] <input file or directory> <output directory>

Transcodes 1 file or a whole directory.

Options:
    -b --bitrate= Set the output bitrate. Default 128kbps
    -m --mono     Force the output to be mono. Default False
    -t --type=    Set the output file type. Default MP3.
    -h --help     Prints this help message.

""" % sys.argv[0]

def coreCount():
    "Detects the number of CPUs on a system. Cribbed from pp."
    
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
        if ncpus > 0:
            return ncpus
    return 1 # Default

class Transcode(subprocess.Popen):
    "A thin class wrapper around an FFMEG transcoding process."

    def __init__(self, input_file, output_file, bit_rate, mono=False):
        "Starts the ffmpeg transcode process"
        if mono:
            sys.stderr.write('Mono is not yet supported. Ignoring.')
        subprocess.Popen.__init__(self, ['ffmpeg', '-i', input_file, '-b:a', bit_rate, output_file])

    @property
    def complete(self):
        "Tests if the encoding is done"
        return self.poll() is not None

def outPathName(in_path_name, out_path, out_type):
    "Returns the output pathname based in input path name and output directory and type."
    path, name = os.path.split(in_path_name)
    base, ext = os.path.splitext(name)
    return os.path.join(out_path, base+out_type)

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "b:mt:h", ('bitrate=', 'mono', 'type=', 'help'))
    except getopt.GetoptError:
        sys.stderr.write('Error parsing arguments, please try "%s --help"\n' % sys.argv[0])
        sys.exit(1)
    else:
        if len(args) < 2:
            sys.stderr.write('Two arguments must be specified, an input file or directory and an output directory.\n')
            sys.exit(1)
        else:
            inpath, outpath = args
            cores = coreCount()
            bitrate = '128k'
            mono = False
            outtype = '.mp3'
            for opt, val in opts:
                if opt == '-h' or opt == '--help':
                    sys.stdout.write(USAGE)
                    sys.exit(0)
                elif opt == '-b' or opt == '--bitrate':
                    bitrate = val
                elif opt == '-m' or opt == '--mono':
                    mono = True
                elif opt == '-t' or opt == '--type':
                    outtype = val
                    if not outtype.startswith('.'): outtype = '.' + outtype
            if os.path.isfile(inpath):
                p = Transcode(inpath, outPathName(inpath, outpath, outtype), bitrate, mono)
                while not p.complete: time.sleep(0.1)
                sys.exit(p.poll())
            else:
                toXcode = []
                def append_appropriate(l, dirname, fnames):
                    l.extend([os.path.join(dirname, f) for f in fnames if f.endswith('.mp3')])
                sys.stdout.write('Finding files to transcode...')
                os.path.walk(inpath, append_appropriate, toXcode)
                sys.stdout.write('%d found.\n' % len(toXcode))
                procs = []
                while toXcode or procs:
                    procs = [p for p in procs if not p.complete]
                    while toXcode and len(procs) < cores:
                        ipn = toXcode.pop(0)
                        sys.stdout.write('Commencing transcode of "%s"\n' %ipn)
                        procs.append(Transcode(ipn, outPathName(ipn, outpath, outtype), bitrate, mono))
                    time.sleep(0.1)
                        
