#! /usr/bin/env python

"""
wallpaper - finds a random picture and sets it as wallpaper

        you need another program (this uses bsetbg) for actually
        setting the wallpaper

In a unix/linux/bsd system, you can schedule this to run regularly
using crontab.  For example, I run this every hour. So I go
to a shell and run
       crontab -e
This opens up my crontab file. I add the following line:
01 * * * * /usr/local/bin/wallpaper > /dev/null
learn more about cron format at
    http://www.uwsg.iu.edu/edcert/slides/session2/automation/crontab5.html
"""
# all the folders you want to scan
folders = [
    '~/backgrounds/1024x768',
    '~/backgrounds/800x600',
    ]

# these are the valid image types - case sensitive
use_types = ['.jpg', '.gif', '.png']


# the command to execute for setting wallpaper. %s will be
# substituted by the image path
cmd = "bsetbg -f %s"

# ---------------- main routine ------------------------------
import os
from random import choice


# initialize a list to hold all the images that can be found
imgs = []

for d in folders: #for each item in folders
    if os.path.exists(d) and os.path.isdir(d): #is it a valid folder?
        for f in os.listdir(d):                #get all files in that folder

            try:  #splitext[1] may fail
                if os.path.splitext(f)[1] in use_types: #is that file of proper type?
                    imgs.append(d + os.sep + f)         #if so, add it to our list
            except:
                pass

wallpaper = choice(imgs)   #get a random entry from our list
print cmd % wallpaper
os.system(cmd % wallpaper) #execute the command
