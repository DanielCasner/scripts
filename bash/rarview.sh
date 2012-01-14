#!/bin/bash
# This script extracts a rar archive to a temp dir and opens it with an
# image viewer. It creates a unique temp dir for each archive (based on 
# file size) and deletes any other directories from the cache. That way, 
# the same archive may be opened numerous times until one finishes reading
# it, and opens another.
# Copyright Dan Zwell, 2005. Anybody is free to distribute and/or modify
# this code in any way they see fit, though I would appreciate your keeping
# my name here unless you modify the code significantly.
umask 077

usage() {
	echo
	echo rarview: Everyone knows that for reading comics and manga, CDisplay is the
	echo best Windows program. It opens an archive "(rar, cbr, zip, tar, tar.gz,"
	echo "or tar.bz2) full of images and displays them."
	echo
	echo This script is made to do the same thing for Linux. You must have gqview 
	echo or some other image viewer installed. The preference can be set by 
	echo changing the environment variable '$image_viewer'. This could be set in
	echo a config file '~'/.rarview/config. Just add a line, "image_viewer=gthumb", 
	echo or something similar.
	echo
	echo usage: "$0" "<file>"
	echo
	exit 0
}
if [ $# -lt 1 ]; then usage; fi
if [ ! -r "$1" ]; then usage; fi

archive="$1" # protect the original command line argument, because the "case"
			 # command cycles through the arguments and deletes them all.
while [ "$#" -ne 0 ] # displays help when -h or --* is part of the arguments.
do
case $1 in
	--help)
		usage ;;
	-h)
		usage ;;
	-*)
		usage ;;
esac
shift
done

# Checks to see whether an image viewer is set, and tries to guess which is installed.
if [ -e "$HOME"/.rarview/config ]; then . "$HOME"/.rarview/config; fi
if [ -z $image_viewer ]; then # if the image viewer is not initialized or zero:
	if which gqview &>/dev/null; 
	then image_viewer=gqview
	elif which gthumb &>/dev/null; 
	then image_viewer=gthumb
	elif which pornview &>/dev/null; 
	then image_viewer=pornview
	else
		echo Neither gqview, gthumb, or pornview are installed on your system.
		echo You will need to install one of these programs, or use a different
		echo comic viewer and set '$image_viewer' environment variable to the
		echo name of that application, i.e., '"export image_viewer=<program-name>".'
		exit
	fi
fi

if ! which $image_viewer &>/dev/null; then 
	echo $image_viewer is not installed. You should install it or unset or change
	echo the '$image_viewer' environment variable. '"unset $image_viewer"'.
	exit
fi

# Convert the filename from relative to absolute: (if it isn't absolute already)
if ! echo "$archive" | grep -q ^/
then image_file=`pwd`/"$archive"
fi
TEMPDIR="$HOME/.rarview"
FILESIZE=`du -k "$archive" | cut -f 1`

mkdir -p "$TEMPDIR"
if [ ! -w "$TEMPDIR" ]
then
	echo "directory unwriteable."
	exit
else cd "$TEMPDIR"; fi

# delete all cache dirs from other files (that is, other sizes)
ls | grep -v $FILESIZE | grep -v config | xargs rm -rf 2>/dev/null

mkdir -p $FILESIZE
if [ $? -ne 0 ]
then echo "Cannot create cache dir $TEMPDIR/$FILESIZE. Exiting."; exit; fi

cd $FILESIZE

# Checks to see whether the given decompression program is installed:
programcheck() {
	if ! which "$1" &>/dev/null
	then echo You either do not have "$1" installed, or it is not in your PATH
		echo variable. You need to install it to view this archive.
		exit
	fi
}

# What type of archive is the image file? What command should I use
# to extract it? Is that program installed?
if echo "$image_file" | grep -q cbr$
then programcheck rar; decompress="rar e -o-"
elif echo "$image_file" | grep -q rar$
then programcheck rar; decompress="rar e -o-"
elif echo "$image_file" | grep -q zip$
then programcheck unzip; decompress="unzip -n"
elif echo "$image_file" | grep -q tar$
then programcheck tar; decompress="tar -xkf"
elif echo "$image_file" | grep -q tar.bz2$
then programcheck tar; decompress="tar -xkjf"
elif echo "$image_file" | grep -q tar.gz$
then programcheck tar; decompress="tar -xkzf"
else echo Currently, only .cbr, .rar, .zip, .tar, .tar.bz2, and .tar.gz archives
	echo are supported. If you want to use this program with a different type
	echo of archive, you could modify the source code. It is really not very
	echo hard to understand. Good luck.
	exit
fi

echo $decompress "$image_file"
$decompress "$image_file"
$image_viewer

exit 0
