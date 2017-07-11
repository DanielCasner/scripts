#!/usr/bin/env python3
"""
A script to pull in individual JPEG images from security cameras (over SCP or locally), add
subtitle date time information and then encode the images into video files using FFMPEG.
Finally, the original images are deleted.
"""
__author__ = "Daniel Casner <daniel@danielcasner.org>"
__version__ = "0.2.0"

import sys
import os
import argparse
import subprocess
import re
import time
from multiprocessing import Pool, cpu_count

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("No module PIL found, try pip3 install pillow")

USAGE = """
%s <SCP TARGETS>

Encodes downloads files from remote server, superimposes a date time stamp on the image and transcodes the still images
as an encode.
SCP TARGETS may be one or multiple scp targets, each one will be spawned in a thread
""" % sys.argv[0]

V = 3

DATE_TIME_RE = re.compile(
    r".*/[0-9A-F]+\(.+\)_.+_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2}).+\.jpg"
)
IMG_FMT = "img%08d.bmp"  # Worst case at 1 frame per 2 seconds for 24 hours

if os.path.isfile("/usr/share/fonts/truetype/droid/DroidSans.ttf"):
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/droid/DroidSans.ttf", 22)
elif os.path.isfile("/Library/Fonts/Andale Mono.ttf"):
    FONT = ImageFont.truetype("/Library/Fonts/Andale Mono.ttf", 22)
else:
    raise sys.exit("No supported font found")


def vprint(level, log):
    "Prints log only if global V >= level"
    if V >= level:
        sys.stdout.write(log)
        sys.stdout.write(os.linesep)
        sys.stdout.flush()


def generate_out_name(in_file_name, enumeration):
    "Generates an enumerated file name from the incoming file name and enumeration value"
    path, _ = os.path.split(in_file_name)
    return os.path.join(path, IMG_FMT % enumeration)


def annotate_image(args):
    "Adds date / time text to an image"
    enumeration, (in_file_name, annotate_time) = args
    if V >= 3:  # Can't use vprint here because we don't want the automatic new line
        sys.stdout.write("{0:d}\r".format(enumeration))
    out_file_name = generate_out_name(in_file_name, enumeration)
    if os.path.isfile(out_file_name):
        # Skip files which have already been generated
        return out_file_name
    try:
        img = Image.open(in_file_name)
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*annotate_time),
                  (255, 128, 0), font=FONT)
        img.save(out_file_name)
    except Exception as exp:
        sys.stderr.write("Failed to annotate image \"{}\":{linesep}{}{linesep}".format(
            in_file_name, exp, linesep=os.linesep
        ))
        return None
    else:
        return out_file_name


def match_image(file_path_name):
    """Checks if image matches the expeted file name RE and parses out date time stamp
    tuple if it does"""
    match = DATE_TIME_RE.match(file_path_name)
    if match is None:
        sys.stderr.write("Unexpected file in target: \"{}\"{linesep}".format(
            file_path_name, linesep=os.linesep))
        return None
    return file_path_name, tuple((int(i) for i in match.groups()))


class CamArchiver(object):
    "A class to manage the lifecycle of camera image archiving."

    def __init__(self, target, pool, parallel):
        "Sets up the archiving class and process"
        self.dir = target
        self.pool = pool
        self.threads = parallel
        self.subprocess = None
        self.rm_files = []

    def __del__(self):
        "Cleanup everything we've left lying around"
        if self.subprocess is not None:
            if self.subprocess.poll() is None:
                self.subprocess.kill()
                self.subprocess.wait()
                self.subprocess = None

    def list_files(self):
        """Returns a list of all the files along with a list of date time
        stamps to apply to them, sorted by date time stamp"""
        vprint(2, "\tListing directory {}".format(self.dir))
        candidates = (os.path.abspath(os.path.join(self.dir, file_name))
                      for file_name in os.listdir(self.dir))
        vprint(2, "\tMatching stills for encoding")
        stills = [i for i in self.pool.map(match_image, candidates) if i is not None]
        vprint(1, "Have {} stills to process".format(len(stills)))
        # Sort by date time stamp, default sorting of number tuples works nicely here.
        stills.sort(key=lambda x: x[1])
        self.rm_files.extend((fpn for fpn, _ in stills))
        return stills

    def process_images(self):
        "Go through the files we've got, annotate them and get them ready to encode"
        vprint(1, "Processing images")
        queue = self.list_files()
        if not queue:
            sys.stderr.write("Nothing to do!{linesep}".format(linesep=os.linesep))
            return False
        vprint(2, "\tAnnotating images")
        annotated_fpns = self.pool.map(annotate_image, enumerate(queue))
        self.rm_files.extend((fpn for fpn in annotated_fpns if fpn is not None))
        return True

    def encode(self, output_directory, framerate=(25, 2), crf=30):
        "Encodes the images to the output"
        output = os.path.abspath(os.path.join(
            output_directory,
            "{name}_{0:04d}-{1:02d}-{2:02d}.mp4".format(*time.localtime(), name=self.dir)))
        vprint(1, "Encoding images to video {}".format(output))
        ffmpeg_loglevel = -8 + 8*V  # See man ffmpeg
        self.subprocess = subprocess.Popen(["ffmpeg",
                                            "-framerate",
                                            "{0:d}/{1:d}".format(*framerate),
                                            "-i", os.path.join(self.dir, IMG_FMT),
                                            "-c:v",
                                            "libx264",
                                            "-crf",
                                            str(crf),
                                            "-pix_fmt",
                                            "yuv420p",
                                            '-threads',
                                            str(self.threads),
                                            '-loglevel',
                                            str(ffmpeg_loglevel),
                                            output])
        ret = self.subprocess.wait()
        if ret != 0:
            sys.stderr.write("Encoding images to {} failed, exit code {}\r\n".format(output, ret))
            return False
        return True

    def remove_files(self):
        "Remove all processed and temprary files"
        vprint(1, "Removing {} files".format(len(self.rm_files)))
        for file_path_name in self.rm_files:
            os.remove(file_path_name)

    def run(self, encode_args):
        "Run the encode task"
        if not self.process_images():
            return
        if not self.encode(*encode_args):
            return
        if not self.remove_files():
            return


def main():
    "Main function for script to encode images from multiple directories"
    parser = argparse.ArgumentParser("Security camera archiver")
    parser.add_argument('-v', '--verbose', action="count", default=0,
                        help="Increase debugging verbosity")
    parser.add_argument('-o', '--output_directory', default=os.path.curdir,
                        help="Where to put encoded video files")
    parser.add_argument('-c', '--change_directory',
                        help="Change working directory before running."
                        "Inputs and outputs if relative will be this path")
    parser.add_argument('-p', '--parallel', type=int, default=cpu_count(),
                        help="How many processes to fork, default is cpu count")
    parser.add_argument('--framerate', type=int, nargs=2, default=[25, 2],
                        help="Framerate for encoded video, numerator, denominator")
    parser.add_argument('--crf', type=int, nargs=1, default=35,
                        help="Quality for encoded video")
    parser.add_argument('inputs', nargs='+',
                        help="Directories of stills to encode")
    args = parser.parse_args()

    global V
    V = args.verbose

    if args.change_directory:
        try:
            os.chdir(args.change_directory)
        except FileNotFoundError as e:
            sys.exit("Could not change working directory to {0:s}: {1!s}".format(args.change_directory, e))

    if not os.path.isdir(args.output_directory):
        sys.exit('No such output directory "{}"'.format(args.output_directory))
    for i in args.inputs:
        if not os.path.isdir(i):
            sys.exit('No such input directory "{}"'.format(i))

    process_pool = Pool(args.parallel)

    vprint(0, os.linesep)
    vprint(0, '#'*80)
    vprint(0, "Camarchive starting at: {}".format(time.ctime()))

    for archive in (CamArchiver(t, process_pool, args.parallel) for t in args.inputs):
        archive.run((args.output_directory, args.framerate, args.crf))


if __name__ == '__main__':
    main()
