#!/usr/bin/python

__doc__ = """pygaller, a python script to generate an photo gallery including XHTML
code, thumbnails and resized images if specified. Files containing code to go
above and below the gallery code can also be specified in addition to the images.
Usage:
    pygallery.py -h|--help
    pygallery.py --genconf
    pygallery.py FOLDER_CONTAINING_IMAGE_FILES

All the parameters for he gallery generation are controlled by an XML file in
the directory called galfmt.xml. The file is optional and if no file named
galfmt.xml is found in the specified directory, default values are used. Run
pygallery with the --genconf argument to generate a blank XML file to start
from. import Use the following tags in the file inside the root element
<gallery></gallery>, all tags are optional:
<captions [useFileNames="true"]>[<file name="" caption="" /> ...]</captions> --
    A list of filenames with captions to be associated with them in the generated
    gallery. If the caption tag is not included no captions are used. If the tags
    are included but not all files have captions specified, pygallery will ask
    for captions on the terminal unless the useFileNames="true" attribute is set
    in which case the images are captioned with their filenames.
<header file="" /> -- A file containing XHTML code to go above the gallery code
    in the generated gallery. If unspecified a generic header is used.
<footer file="" /> -- A file containing XHTML code to go below the gallery code
    in the generated gallery. If unspecified a generic footer is used.
<names>[<file oldname="" name="" /> ...]</names> -- Similar to captions. If
    names is used but not all files have names associated with them, pygallery
    will ask for names at the terminal. If the names tag is omitted no renaming
    is done.
<resize size="" /> -- The 'fullsize' to resize the image to. Specify the long
    dimension of the image, the script automatically detects whether the image
    is vertical or horizontal. If unspecified no resizing is done to the full
    size image.
<thumb size="" /> -- The size of thumbnail to create for each image to display
    in the gallery. As with resize, specify the long dimension. If left
    unspecified the default value of 150 is used.
"""
__version__ = '0.1'
__status__ = 'development'

import sys, os
from xml.dom import minidom
try:
    from PIL import Image
except ImportError:
    sys.stderr.write("""Unable to import PIL.Image
Check that the PIL library is correctly installed.
""")
    sys.exit(1)

DEFAULT_HEADER = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>Gallery</title>
    <meta name="generator" content="pygallery version""" + __version__ + """ " />
</head>
<body>
"""
DEFAULT_FOOTER = """
</body>
</html>
"""
DEFAULT_THUMB_SIZE = 150
ROW_WIDTH_LIMIT = 640

class Captions:
    def __init__(self, node):
        try:
            ufnValue = node.attributes['useFileNames'].value
        except KeyError:
            self.useFileNames = False
        else:
            if ufnValue == 'true':
                self.useFileNames = True
            else:
                self.useFileNames = False
        self.fileNodes = node.getElementsByTagName('file')
    
    def getCaption(self, fileName):
        
        for node in self.fileNodes:
            try:
                if node.attributes['name'].value == fileName:
                    return node.attributes['caption'].value
            except KeyError:
                pass # Ignore tags without proper filenames
        return None # If we've gotten here there's no matching entry
        
    def rename(self, oldName, newName):
        for node in self.fileNodes:
            try:
                if node.attributes['name'].value == oldName:
                    node.attributes['name'].value = newName
                    return True # We did rename something
            except KeyError:
                pass # Ignore tags without proper filenames
        return False # We didn't rename anything

class Names:
    def __init__(self, node):
        self.fileNodes = node.getElementsByTagName('file')
        
    def getName(self, fileName):
        for node in self.fileNodes:
            print node.toxml()
            try:
                if node.attributes['oldname'].value == fileName:
                    return node.attributes['name'].value
            except KeyError:
                pass # Ignore tags without proper filenames
        return None # If we've gotten here there's no matching entry

class GalOpts:
    """GalOpts is constructed with a path and looks for a galfmt.xml
file in the given directory. If it finds a file it attempts to parse
it and initalize its configuration options with those values. If no
file is found, it sets the configuration values to the defaults."""
    
    def __init__(self, path):
        self.path = os.path.normpath(path)
        file = os.path.join(self.path, 'galfmt.xml')
        try:
            FH = open(file, 'r')
        except IOError, inst:
            if inst.args[0] == 2:
                print "No galfmt.xml file found so using default behaviors."
                self.captions = None
                self.names    = None
                self.header   = DEFAULT_HEADER
                self.footer   = DEFAULT_FOOTER
                self.resize   = None
                self.thumb    = DEFAULT_THUMB_SIZE
            else:
                print sys.stderr.write("IO exception while trying to process galfmt.xml" + inst + "\n")
        else:
            try:
                confXML = minidom.parse(FH)
            except:
                print "Couldn't parse galfmt.xml file"
                sys.exit(1)    
            # Now that we have the parsed file, lets figure out what it means
            # Captions
            nodes = confXML.getElementsByTagName('captions')
            if len(nodes) == 0:
                self.captions = None
            else:
                self.captions = Captions(nodes[0])
            # Names
            nodes = confXML.getElementsByTagName('names')
            # Renaming doesn't work yet so disabled.
            #if len(nodes) == 0:
            #    self.names = None
            #else:
            #    self.names = Names(nodes[0])
            self.names = None
            # Header
            nodes = confXML.getElementsByTagName('header')
            if len(nodes) == 0:
                self.header = DEFAULT_HEADER
            else:
                self.header = self.readXHTMLFile(nodes[0])
            # Footer
            nodes = confXML.getElementsByTagName('footer')
            if len(nodes) == 0:
                self.footer = DEFAULT_FOOTER
            else:
                self.footer = self.readXHTMLFile(nodes[0])
            # Resize
            nodes = confXML.getElementsByTagName('resize')
            if len(nodes) == 0:
                self.resize = None
            else:
                self.resize = self.getSize(nodes[0])
            # Thumb
            nodes = confXML.getElementsByTagName('thumb')
            if len(nodes) == 0:
                self.thumb = DEFAULT_THUMB_SIZE
            else:
                self.thumb = self.getSize(nodes[0])
        
    def readXHTMLFile(self, node):
        try:
           fileName = os.path.normpath(node.attributes['file'].value)
        except KeyError:
            print "Malformed " + node.tagName + " file specification"
            sys.exit(1)
        try:
            fileName = os.path.join(self.path, fileName)
            FH = open(fileName, 'r')
            try:
                return FH.read()
            finally:
               FH.close()
        except IOError, inst:
            print "IO exception while processing the specified XHTML file: " + fileName
            print inst
            sys.exit(inst.args[0])
            
    def getSize(self, node):
        try:
            size = int(node.attributes['size'].value)
        except KeyError:
            print "Malformed " + node.tagName + " size specification"
            sys.exit(1)
        return size;
# End GalOpts
        
def writeConfFile():
    try:
        fmtFile = open('galfmt.xml', 'w')
    except IOError, inst:
        print sys.stderr.writelines("Couldn't write galfmt.txt", inst)
    print fmtFile.write("""<?xml version="1.0" ?>
<gallery>
    Add tags here
</gallery>
""")
# End writeConfFile

def makeGallery(opts):
    # We'll be using this function a lot so make a shortcut
    fixPath = lambda fn: os.path.join(opts.path, fn)
    try:
        files = [f for f in os.listdir(opts.path) if os.path.isfile(fixPath(f))]
    except OSError:
        print sys.stderr.write("Couldn't get directory listing for " + opts.path)
        sys.exit(1)
    try:
        indexFH = open(fixPath('index.html'), 'w')
        try:
            indexFH.write(opts.header)
            indexFH.write('<table alt="image gallery thumbnails">\n')
            row = 1 # One based index
            for f in files:
                try:
                    img = Image.open(fixPath(f))
                except IOError:
                    pass # Just ignore files that don't seem to be images
                else:
                    # Rename images if nessisary
                    if opts.names:
                        newName = opts.names.getName(f)
                        if not newName:
                            newName = promptUser(img, 'Please enter a name for ' + f)
                            newRoot, newExt = os.path.splitext(newName)
                            oldRoot, oldExt = os.path.splitext(f)
                            if not newRoot:
                                newRoot = oldRoot
                            newName = newRoot + oldExt
                        try:
                            os.rename(fixPath(f), fixPath(newName))
                        except OSError:
                            print sys.stderr.write("Couldn't rename file "
                                                   + fixPath(f))
                        else:
                            opts.captions.rename(fixPath(f), fixPath(newName))
                            f = newName
                    # Resize the image if nessisary
                    if opts.resize:
                        # Use the thumbnail function to resize the image
                        # instead of resize because we want to resize to
                        # fit in a box and this is what thumbnail does
                        # whereas resize 1) resizes to specific dimensions
                        # and 2) copies the image, neither of which we want
                        if max(img.size) > opts.resize:
                            img.thumbnail((opts.resize,opts.resize))
                            img.save(fixPath(f))
                    # Make a thumbnail
                    img.thumbnail((opts.thumb,opts.thumb))
                    img.save(fixPath(thumbName(f)))
                    # Write the XHTML
                    if row == 1:
                        indexFH.write('<tr>\n')
                    elif row*opts.thumb >= ROW_WIDTH_LIMIT:
                        indexFH.write('</tr>\n')
                        row = 1
                    writeTableCell(indexFH, f, img, opts)
                    row += 1
            indexFH.write('</tr>\n</table>')
            indexFH.write(opts.footer)
        finally:
            indexFH.close()
    except IOError, inst:
        print sys.stderr.write("IO Exception " + inst)
        sys.exit(1)
# End makeGallery

def promptUser(image, prompt):
    try:
        image.show()
    except:
        pass # If we couldn't show the image just prompt
    return raw_input(prompt + ' > ')
# End promptUser

def thumbName(fileName):
    root, ext = os.path.splitext(fileName)
    return root + '_thumb' + ext
# End thumbName

def writeTableCell(fileHandle, fileName, image, opts):
    caption = ''
    if opts.captions:
        if opts.captions.useFileNames:
            caption = os.path.splitext(fileName)
        else:
            caption, junk = opts.captions.getCaption(fileName)
        if not caption:
            caption = promptUser(image, 'Please supply a caption for ' + fileName)
    fileHandle.write('<td><a href="' + fileName +
                     '"><img src="'  + thumbName(fileName) +
                     '" alt="'       + fileName + 
                     '" width="'     + str(image.size[0]) +
                     '" height="'    + str(image.size[1]) +
                     '" /></a><br/>' + caption + '</td>\n')
# End writeTableCell

if __name__ == '__main__':
    try:
        if len(sys.argv) < 2:
            print __doc__
            sys.exit(2)
        else:
            for arg in sys.argv[1:]:
                if arg == '-h' or arg == '--help':
                    print __doc__
                    sys.exit(2)
                elif arg == '--genconf':
                    writeConfFile()
                    sys.exit(0)
                elif not os.path.isdir(arg):
                    print "No such directory: " + arg
                    sys.exit(1)
                else:
                    makeGallery(GalOpts(arg))
    except KeyboardInterrupt:
        print "Aborted by user\n"
        sys.exit(1)
