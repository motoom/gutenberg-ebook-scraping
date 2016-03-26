
# gutenberg.py
#
# Reformats and renames the downloaded etexts.
#
# Software by Michiel Overtoom, motoom@xs4all.nl, July 2009, amended April 2016.
#

import os
import re
import codecs
import glob

# Repetitive stuff I don't want to read a 1000 times on my eBook reader.
remove = ["Produced by","End of the Project Gutenberg","End of Project Gutenberg"]


def encoding(fn):
    for line in open(fn):
        if line.startswith("Character set encoding:"):
            _, encoding = line.split(":")
            return encoding.strip()
    return "latin1"

codecmap = {
    "latin1": "latin1",
    "ISO Latin-1": "latin1",
    "ISO-8859-1": "latin1",
    "UTF-8": "utf8",
    "ASCII": "ascii",
    }

def beautify(fn, outputdir):
    ''' Reads a raw Project Gutenberg etext, reformat paragraphs,
    and removes fluff.  Determines the title of the book and uses it
    as a filename to write the resulting output text. '''
    codec = codecmap.get(encoding(fn), "latin1")
    lines = [line.strip() for line in codecs.open(fn, "r", codec)]
    collect = False
    lookforsubtitle = False
    outlines = []
    startseen = endseen = False
    title=""
    for line in lines:
        if line.startswith("Title: "):
            title = line[7:]
            lookforsubtitle = True
            continue
        if lookforsubtitle:
            if not line.strip():
                lookforsubtitle = False
            else:
                subtitle = line.strip()
                subtitle = subtitle.strip(".")
                title += ", " + subtitle
        if ("*** START" in line) or ("***START" in line) or (line.startswith("*END THE SMALL PRINT!")):
            collect = startseen = True
            paragraph = ""
            continue
        if ("*** END" in line) or ("***END" in line):
            endseen = True
            break
        if not collect:
            continue
        if not line:
            paragraph = paragraph.strip()
            for term in remove:
                if paragraph.startswith(term):
                    paragraph = ""
            if paragraph:
                outlines.append(paragraph)
                outlines.append("")
            paragraph = ""
        else:
            paragraph += " " + line

    # Compose a filename.  Replace some illegal file name characters with alternatives.
    lastpart = fn
    parts = fn.split(os.sep)
    if len(parts):
        lastpart = parts[-1]
    ofn = title[:150] + ", " + lastpart
    ofn = ofn.replace("&", "en")
    ofn = ofn.replace("/", "-")
    ofn = ofn.replace("\"", "'")
    ofn = ofn.replace(":", ";")
    ofn = ofn.replace(",,", ",")

    # Report on anomalous situations, but don't make it a showstopper.
    if not title:
        print ofn
        print "    Problem: No title found\n"
    if not startseen:
        print ofn
        print "    Problem: No '*** START' seen\n"
    if not endseen:
        print ofn
        print "    Problem: No '*** END' seen\n"

    f = codecs.open(os.path.join(outputdir, ofn), "w", "utf8")
    f.write("\n".join(outlines))
    f.close()

if not os.path.exists("ebooks"):
    os.mkdir("ebooks")

for fn in glob.glob("ebooks-unzipped/*.txt"):
    beautify(fn, "ebooks")
