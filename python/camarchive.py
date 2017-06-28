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

V = 2

DATE_TIME_RE = re.compile(
    r".*/[0-9A-F]+\(.+\)_.+_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2}).+\.jpg"
)
IMG_FMT = "img%08d.bmp" # Worst case at 1 frame per 2 seconds for 24 hours

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

    def __init__(self, target, pool):
        "Sets up the archiving class and process"
        self.dir = target
        self.pool = pool
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

    def encode(self, framerate=(25, 2), crf=30):
        "Encodes the images to the output"
        output = os.path.abspath(os.path.join(
            self.dir, "{0:04d}-{1:02d}-{2:02d}.mp4".format(*time.localtime())))
        vprint(1, "Encoding images to video {}".format(output))
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
                                            output])
        ret = self.subprocess.wait()
        if ret != 0:
            sys.stderr.write("Encoding images to {} failed, exit code {}\r\n".format(output, ret))
            return False
        return True

    def remove_files(self):
        "Remove all processed and temprary files"
        for file_path_name in self.rm_files:
            os.remove(file_path_name)

    def run(self):
        "Run the encode task"
        if not self.process_images():
            return
        if not self.encode():
            return
        if not self.remove_files():
            return

def main(directories):
    "Main function for script to encode images from multiple directories"
    process_pool = Pool(cpu_count())
    for archive in (CamArchiver(t, process_pool) for t in directories):
        archive.run()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(USAGE)
    else:
        main(sys.argv[1:])
