#!/usr/bin/env python3
"""
A script to pull in individual JPEG images from security cameras (over SCP), add subtitle date time information and
then encode the images into video files using FFMPEG. Finally, the original images are deleted.
"""

import sys, os, subprocess, re, time, threading
from PIL import Image, ImageDraw, ImageFont

USAGE = """
%s <SCP TARGETS>

Encodes downloads files from remote server, superimposes a date time stamp on the image and transcodes the still images
as an encode.
SCP TARGETS may be one or multiple scp targets, each one will be spawned in a thread
""" % sys.argv[0]

V = 1

class CamArchiver(threading.Thread):
    "A class to manage the lifecycle of camera image archiving."

    DATE_TIME_RE = re.compile(r"[0-9A-F]+\(.+\)_.+_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2}).+\.jpg")
    IMG_FMT = "img%08d.bmp" # Worst case at 1 frame per 2 seconds for 24 hours

    def __init__(self, target):
        "Sets up the archiving class and process"
        threading.Thread.__init__(self)
        if os.path.isfile("/usr/share/fonts/truetype/droid/DroidSans.ttf"):
            self.FONT = ImageFont.truetype("/usr/share/fonts/truetype/droid/DroidSans.ttf",22)
        elif os.path.isfile("/Library/Fonts/Andale Mono.ttf"):
            self.FONT = ImageFont.truetype("/Library/Fonts/Andale Mono.ttf",22)
        else:
            raise Exception("No supported font found")
        if ':' in target:
            self.scpTarget = target
            self.localTarget = None
        else:
            self.scpTarget = None
            self.localTarget = target
        if not scpTarget.endswith('/'): self.scpTarget += '/'
        self.dir = os.path.split(scpTarget)[1]
        self.tempDir = os.path.join(self.dir, "temp")
        self.subprocess = None
        self.remoteRmFiles = []

    def __del__(self):
        "Cleanup everything we've left lying around"
        if self.subprocess is not None:
            if self.subprocess.poll() is None:
                self.subprocess.kill()
                self.subprocess.wait()
                self.subprocess = None
        if os.path.isdir(self.tempDir):
            for fn in os.listdir(self.tempDir):
                os.remove(os.path.join(self.tempDir, fn))
            os.rmdir(self.tempDir)


    def downloadFiles(self):
        "SCPs the files over from the remote server"
        if not os.path.isdir(self.dir):
            os.mkdir(self.dir)
        if not os.path.isdir(self.tempDir):
            os.mkdir(self.tempDir)
        if V > 0: sys.stdout.write("Rsyncing files from target {}\n".format(self.scpTarget))
        rsyncCmd = ["rsync", "-a", self.scpTarget, self.tempDir]
        if V > 2: rsyncCmd.insert(2, "-v")
        self.subprocess = subprocess.Popen(rsyncCmd, stdout=sys.stdout, stdin=sys.stdin)
        ret = self.subprocess.wait()
        if ret != 0:
            sys.stderr.write("Rsyncing from {} to {} failed, exit code {}\n".format(self.scpTarget, self.dir, ret))
            return False
        else:
            return True

    def listFilesAndTimes(self):
        "Returns a list of all the files along with a list of date time stamps to apply to them, sorted by date time stamp"
        stills = []
        for fn in os.listdir(self.tempDir):
            m = self.DATE_TIME_RE.match(fn)
            if m is None:
                sys.stderr.write("Unexpected file in download: \"{}\"\r\n".format(fn))
            else:
                stills.append((fn, tuple((int(i) for i in m.groups())))) # Should do sort during insert but don't care
        self.remoteRmFiles = [fn for fn, dt in stills]
        stills.sort(key=lambda x: x[1]) # Sort by date time stamp, default sorting of number tuples works nicely here.
        return stills

    def annotateImage(self, img, time):
        "Adds date / time text to an image"
        draw = ImageDraw.Draw(img)
        draw.text((0,0), "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*time), (255, 128, 0), font=self.FONT)
        return draw

    def processImages(self):
        "Go through the files we've got, annotate them and get them ready to encode"
        frame = 0
        if V > 0: sys.stdout.write("Processing images:\n")
        fnDateTuples = self.listFilesAndTimes()
        if len(fnDateTuples) == 0:
            sys.stderr.write("No stills downloaded\n")
            return False
        for fn, dateTime in fnDateTuples:
            outFn = os.path.join(self.tempDir, self.IMG_FMT % frame)
            if not os.path.isfile(outFn): # Skip files that have already been generated
                if V > 1: sys.stdout.write("\t{} --> {}\n".format(fn, outFn))
                try:
                    img = Image.open(os.path.join(self.tempDir, fn))
                    self.annotateImage(img, dateTime)
                    img.save(outFn)
                except:
                    sys.stderr.write("Exception trying to annotate image {}, skipping\n".format(fn))
                    continue
            frame += 1
        return True

    def encode(self, framerate=(25,2), crf=30):
        "Encodes the images to the output"
        outputFn = os.path.join(self.dir, "{0:04d}-{1:02d}-{2:02d}.mp4".format(*time.localtime()))
        if V > 0: sys.stdout.write("Encoding images to video {}\n".format(outputFn))
        self.subprocess = subprocess.Popen(["ffmpeg", "-framerate", "{0:d}/{1:d}".format(*framerate), "-i", os.path.join(self.tempDir, self.IMG_FMT), "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", outputFn])
        ret = self.subprocess.wait()
        if ret != 0:
            sys.stderr.write("Encoding images to {} failed, exit code {}\r\n".format(outputFn, ret))
            return False
        else:
            return True

    def removeRemoteFiles(self):
        "Removes the remote files"
        if V > 0: sys.stdout.write("Removing remote files\n")
        remoteHost, remoteDir = self.scpTarget.split(':')
        rmScriptFn = "rm-encoded.bash"
        rmScriptPn = os.path.join(self.tempDir, rmScriptFn)
        rmScript = open(rmScriptPn, "w")
        for fn in self.remoteRmFiles:
            rmScript.write("rm '{}'\n".format(fn))
        rmScript.write("rm '{}'\n".format(rmScriptFn))
        rmScript.close()
        self.subprocess = subprocess.Popen(['scp', rmScriptPn, self.scpTarget])
        ret = self.subprocess.wait()
        if ret != 0:
            sys.stderr.write("Couldn't send remove encoded images script to remote host, exit code {}\r\n".format(ret))
            return False
        else:
            self.subprocess = subprocess.Popen(['ssh', remoteHost], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.subprocess.stdin.write("cd {}\n".format(remoteDir))
            self.subprocess.stdin.write("bash {}\n".format(rmScriptFn))
            self.subprocess.stdin.close()
            ret = self.subprocess.wait()
            if ret != 0:
                sys.stderr.write("Remove remote files commanded failed, exit code {}\r\n".format(ret))
                return False
            else:
                return True

    def run(self):
        "Run the encode task"
        if not self.downloadFiles(): return
        if not self.processImages(): return
        if not self.encode(): return
        if not self.removeRemoteFiles(): return

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(USAGE)
    else:
        threads = [CamArchiver(t) for t in sys.argv[1:]]
        for t in threads: t.start()
