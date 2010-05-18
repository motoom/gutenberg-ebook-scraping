
# gutenberg.py
#
# Reformats and renames the downloaded etexts.
#
# Software by Michiel Overtoom, motoom@xs4all.nl, july 2009.
# 

import os
import re

# Repetive stuff I don't want to read a 1000 times on my eBook reader.
remove = ["Produced by","End of the Project Gutenberg","End of Project Gutenberg"]

def beautify(fn):
    ''' Reads a raw Project Gutenberg etext, reformat paragraphs,
    and removes fluff.  Determines the title of the book and uses it
    as a filename to write the resulting output text. '''
    lines = [line.strip() for line in open(fn)]
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
        if ("*** START" in line) or ("***START" in line):
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
    ofn = title[:150] + ", " + fn
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
        
    f = open(ofn, "wt")
    f.write("\n".join(outlines))
    f.close()

sourcepattern = re.compile("^[0-9]{4,5}\-[0-9]\.txt$")
for fn in os.listdir("."):
    if sourcepattern.match(fn):
        beautify(fn)
