
# toss.py
#
# Software by Michiel Overtoom, motoom@xs4all.nl, July 2009, April 2016.
#
# Tosses text files into subdirectories.

import glob
import os
import re

fns = [] # All filenames to process - all *.txt files in the current directory.
startlettercount = [0] * 26 # For each letter a..z, the number of files starting with that letter.
subdircount = 8 # How many subdirectories to create and toss into.
subdirletters = [[] for x in range(subdircount)] # Of each subdirectory, the letters that will be tossed into.

# Get all the files to process and count them.
for fullfn in glob.glob("ebooks/*.txt"):
    _, fn = fullfn.split(os.sep)
    fns.append(fn)
    startletter = fn[0].lower()
    startletter = min(max(startletter, 'a'), 'z')
    bin = ord(startletter) - ord('a')
    startlettercount[bin] += 1

# Distribute the files over the destination directories.
approxfilespersubdir = len(fns) / subdircount
print "%s text files in total, to be tossed into %s subdirectories, approximately %d files per subdirectory" % (len(fns), subdircount, approxfilespersubdir)
currentsubdir = 0
filesinsubdir = 0
for i in range(26):
    startletter = chr(ord('a') + i)
    subdirletters[currentsubdir].append(startletter)
    filesinsubdir += startlettercount[i]
    if filesinsubdir > approxfilespersubdir:
        currentsubdir += 1
        currentsubdir = min(currentsubdir, subdircount)
        filesinsubdir = 0

# Create the subdirectories and move the files into them.
for s in subdirletters:
    if not s: continue
    if len(s) == 1:
        subdirname = s[0]
    else:
        subdirname = s[0] + "-" + s[-1]
    subdirname = os.path.join("ebooks", subdirname)
    if not os.path.isdir(subdirname):
        os.mkdir(subdirname)
    for letter in s:
        print "Tossing files starting with '%s' to '%s'" % (letter, subdirname)
        for fn in fns:
            startletter = fn[0].lower()
            startletter = min(max(startletter, 'a'), 'z')
            if startletter == letter:
                os.rename(os.path.join("ebooks", fn), os.path.join(subdirname, fn))
