#!/usr/bin/env python
#----------------------------------------------------------------------------
#  This file is constitutes mp3cp
#
#  mp3cp is free software: you can redistribute it
#  and/or modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3 of
#  the License, or (at your option) any later version.
#
#  mp3cp is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty
#  of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with mp3cp.  If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------------
"""
mp3cp (Replicate directory structure transcoding ogg to mp3 where nessisary)
ogg2mp3 (Transcode OGG to MP3)

Requirements:
* python
* oggdec
* ogginfo
* lame

History:
--------
2005-07-06  Darren Stone  Created.  http://bitmason.com
2007-02-25  Darren Stone  Fixed shell quote bug
2007-10-14  Darren Stone  More decode + encode error trapping. Detect unrecognized genres (LAME limitation).
2007-12-08  Darren Stone  Case-insensitive match on ogginfo keys. (Thanx to Owen Emmerson for the catch.)
2009-02-27  Daniel Casner Walk directories and replicate structure, transcoding files as nessisary

Run with --help for usage.

Distribute, use, and modify freely, but please keep the
history above and usage below up to date!
"""


from sys import argv, exit, stdout, stderr
from os import system, stat, getpid, listdir, unlink, mkdir, path
from signal import signal, SIGINT
from commands import getoutput
from shutil import copy
import string

# base LAME command.
# 1. ID3 tags, etc. will be automatically appended if available
# 2. user-supplied command line options will also be appended
lame_cmd_base = 'lame --quiet --ignore-tag-errors'

# Describes mapping from ogginfo keys to LAME ID3 tag commands.
# Match will be case-insensitive on the OGG side.
ogg_to_id3 = {
  'TITLE': '--tt',
  'ARTIST': '--ta',
  'ALBUM': '--tl',
  'GENRE': '--tg',
  'COMMENT': '--tc',
  'DATE': '--ty',
  'TRACKNUMBER': '--tn',
  }

# supported ID3 genres
LAME_GENRES = []

# temporary WAV file will be created (and later removed) in current working directory
WAV_FILENAME_PREFIX = "/tmp/ogg2mp3_"

def init_lame_genres():
  """
  LAME supports only a limited set of textual genres (despite ID3V2 allowing for
  user defined strings).  This helps us detect and report this limitation.
  """
  for line in getoutput("lame --genre-list").splitlines():
    try:
      LAME_GENRES.append(line.strip().split(' ', 1)[1].lower())
    except:
      pass

def ogg_info_dict(oggfilename):
  """
  Return dictionary of ogginfo, containing at least the keys in
  ogg_to_id3 -if- they are present in the ogg file.
  """
  d = {}
  out = getoutput("ogginfo %s" % shell_quote(oggfilename))
  out = out.splitlines()
  for line in out:
    for k in ogg_to_id3.keys():
      i = line.lower().find(k.lower()+'=')
      if i != -1:
        d[k] = line[i+len(k)+1:].strip()
  return d


def file_size(filename):
  """
  Return size of file, in bytes.
  """
  return stat(filename).st_size


def size_to_human(bytes):
  """
  Return string representation of the byte count, human-readable
  (i.e. in B, KB, MB, or GB)
  """
  if bytes >= 1024*1024*1024:
    return "%0.1f GB" % (float(bytes)/1024.0/1024.0/1024.0)
  elif bytes >= 1024*1024:
    return "%0.1f MB" % (float(bytes)/1024.0/1024.0)
  elif bytes >= 1024:
    return "%0.1f KB" % (float(bytes)/1024.0)
  else:
    return "%d B" % bytes


def file_size_human(filename):
  """
  Return string representation of the filename, human-readable
  (i.e. in B, KB, MB, or GB)
  """
  return size_to_human(stat(filename).st_size)


def shell_quote(s):
  """
  Quote and escape the given string (if necessary) for inclusion in
  a shell command
  """
  return "\"%s\"" % s.replace('"', '\"')

def sanitize_name(title):
    "Accepts a name and modifies it to be a safe file name."
    acceptable = string.letters+string.digits+path.sep+" _-.'"
    return ''.join([c for c in title if c in acceptable])

def transcode(oggfilename, mp3filename=None):
  """
  Transcode given OGG to MP3 in current directory, with .mp3 extension,
  transferring meta info where possible.
  Return (oggsize, mp3size).
  """
  try:
    wavfilename = "%s%d.wav" % (WAV_FILENAME_PREFIX, getpid())
    if mp3filename is None: mp3filename = "%s.mp3" % path.basename(oggfilename)[:-4]
    oggsize = file_size_human(oggfilename)
    stdout.write("%s (%s)\n" % (oggfilename, oggsize))
    oggdict = ogg_info_dict(oggfilename)
    encode_cmd = lame_cmd_base
    for k in oggdict.keys():
      k = k.upper()
      knote = ''
      if k in ogg_to_id3.keys():
        if k == 'GENRE' and oggdict[k].lower() not in LAME_GENRES:
          knote = "[WARNING: Unrecognized by LAME so MP3 genre will be 'Other']"
        encode_cmd = "%s %s %s" % (encode_cmd, ogg_to_id3[k], shell_quote(oggdict[k]))
        stdout.write("  %s: %s %s\n" % (str(k), str(oggdict[k]), knote))
    stdout.write("%s " % mp3filename)
    stdout.flush()
    decode_cmd = "oggdec --quiet -o %s %s 2>/dev/null" % (shell_quote(wavfilename), shell_quote(oggfilename))
    system(decode_cmd)
    wavsize = 0
    try:
      wavsize = file_size(wavfilename)
    except:
      pass
    if wavsize <= 0:
      stdout.write("[FAILED] OGG did not decode to intermediate WAV\n\n")
      return (file_size(oggfilename), 0)
    encode_cmd = "%s %s %s 2>/dev/null" % (encode_cmd, wavfilename, shell_quote(mp3filename))
    system(encode_cmd)
    try:
      mp3size = file_size_human(mp3filename)
    except:
      stdout.write("[FAILED] OGG decoded but MP3 encoding and/or tagging failed\n\n")
      return (file_size(oggfilename), 0)
    stdout.write("(%s)\n\n" % mp3size)
  except Exception, e:
    stdout.write(str(e))
  try:
    unlink(wavfilename)
  except:
    pass
  return (file_size(oggfilename), file_size(mp3filename))

def cp_tree(root):
    """
    Replicate a directory tree trancoding files as nessisary.
    """
    def recurse(base_path, new_path):
        new_path = sanitize_name(new_path)
        if not path.isdir(new_path):
            mkdir(new_path)
        for f in listdir(base_path):
            f_path = path.join(base_path, f)
            n_path = path.join(new_path, f)
            if path.isdir(f_path):
                stdout.write('Entering directory "%s"\n' % f_path)
                recurse(f_path, n_path)
            elif f_path.endswith('.mp3'):
                if path.isfile(n_path):
                    stdout.write('%s already exists, skipping\n' % n_path)
                else:
                    stdout.write('%s -> %s\n' % (f_path, n_path))
                    copy(f_path, n_path)
            elif f_path.endswith('.ogg'):
                n_path = n_path[:-3] + 'mp3'
                if path.isfile(n_path):
                    stdout.write('%s already exists, skipping\n' % n_path)
                else:
                  try:
                    transcode(f_path, n_path[:-3] + 'mp3')
                  except OSError, inst:
                    stderr.write("Couldn't transcode %s: %s" % (n_path, inst))
            else:
                stdout.write('Skipping unsupported file "%s"\n' % f)
    recurse(root, path.split(path.normpath(root))[-1])


def sig_int_handler(p0, p1):
  """ Make CTRL-C less catasrophic """
  exit(1)

if __name__ == '__main__':

  # TODO: ensure oggdec, ogginfo, lame are available 

  signal(SIGINT, sig_int_handler)

  if len(argv) < 2 or (len(argv) >= 2 and argv[1] in ('-h', '--help', '-?')):
    progname = path.basename(argv[0])
    stdout.write("""
Usage:
    %s SOURCE_TREES

    Recusively copies files from the source trees into the current directory
    transcoding OGGs to MP3s as nessisary.

""")
    exit(1)

  # append user-supplied cmd line options (for LAME)
  argv.pop(0)
  while not path.isdir(argv[0]):
      lame_cmd_base = "%s %s" % (lame_cmd_base, argv[0])
      argv.pop(0)

  init_lame_genres()

  for dir in argv:
      cp_tree(dir)
