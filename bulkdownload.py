
# bulkdownload.py
#
# Downloads all eBooks from a mirror of Project Gutenberg's website, for a specific language.
#
# Software by Michiel Overtoom, motoom@xs4all.nl, July 2009, March 2012. Adapted in 2016 for mirrors.

'''
Scraping eBooks from Gutenbergs web site isn't allowed anymore.
Instead, you look in http://www.gutenberg.org/MIRRORS.ALL for a mirror nearby you.
You might want to choose a HTTP mirror because FTP mirrors are slow with urllib.urlretrieve (but FTP mirrors are OK if you can use wget).
Choose a suitable mirror URL and put it in the MIRROR variable below.

The program then fetches {MIRROR}/GUTINDEX.ZIP, which is the compressed book index.
In this zip is a textfile called GUTINDEX.ALL, in it every eBook is listed starting on the beginning
of a line, followed by lines of attributes:

    Zur Psychopathologie des Alltagslebens, by Sigmund Freud                 24429
      [Subtitle: Uber Vergessen, Versprechen, Vergreifen, Aberglaube und Irrtum]
      [Language: German]
    Hempfield, by David Grayson                                              33251
     [Subtitle: A Novel]
     [Illustrator: Thomas Fogarty]
    De slavernij in Suriname, by Julien Wolbers                              31060
     [Subtitle: of dezelfde gruwelen der slavernij, die in de 'Negerhut'
      geschetst zijn, bestaan ook in onze West-Indische Kolonien]
     [Language: Dutch]
    De schipbreuk van de "Berlin" 21 Februari 1907, by Jean Louis Pisuisse   33254
     [Subtitle: Volledig verhaal van de scheepsramp
      aan den Hoek van Holland]
     [Illustrator: Louis Raemaekers]
     [Language: Dutch]

The first line has a title and an eBook id number ("De slavernij in Suriname, by J.W.  31060").
Now, where to find the eBook text 31060?
For that, the program fetches {MIRROR}/ls-lR.gz, which contains the compressed directory & file index
in a textfile called 'ls-lR'. It contains chunks like:

    ./3/1/0/6/31060:
    total 156
    -rw-rw-r-- 1 gbnewby pg 77617 Jan 24  2010 31060-8.txt
    -rw-rw-r-- 1 gbnewby pg 29926 Jan 24  2010 31060-8.zip
    drwxrwxr-x 3 gbnewby pg  4096 Jan 24  2010 31060-h
    -rw-rw-r-- 1 gbnewby pg 35794 Jan 24  2010 31060-h.zip

We're interested in the file '31060-0.zip', '31060-8.zip' or '31060.zip'.
From the chunk above we learn it can be found in the directory /3/1/0/6/31060, thus:

    {MIRROR}/3/1/0/6/31060/31060-8.zip

This file is downloaded in the directory 'ebooks-zipped', and contains the eBook text '31060-8.txt',
which is eventually extracted into 'ebooks-unzipped'. Other programs take it from there.

'''


import urllib
import re
import os
import zipfile
import gzip
import datetime
import codecs
import glob
import shutil

MIRROR = "http://www.mirrorservice.org/sites/ftp.ibiblio.org/pub/docs/books/gutenberg/"
LANGUAGE = "Dutch"


def older(a, b):
    '''Return True is file 'a' is older than file 'b'.'''
    if not os.path.exists(a) or not os.path.exists(b):
        return False
    sta = os.stat(a)
    stb = os.stat(b)
    return sta <= stb


def fetch(mirrorurl, filename, outputfilename):
    '''Fetch a file from a gutenberg mirror, if it hasn't been fetched earlier today.'''
    mustdownload = False
    if os.path.exists(filename):
        st = os.stat(filename)
        modified = datetime.date.fromtimestamp(st.st_mtime)
        today = datetime.date.today()
        if modified == today:
            print "%s exists, and is up-to-date. No need to download it." % filename
        else:
            print "%d exists, but is out of date. Downloading..." % filename
            mustdownload = True
    else:
        print "%s not found, downloading..." % filename
        mustdownload = True

    if mustdownload:
        url = mirrorurl + filename
        urllib.urlretrieve(url, outputfilename)


# Ensure directories exist.
if not os.path.exists("indexes"):
    os.mkdir("indexes")

if not os.path.exists("ebooks-zipped"):
    os.mkdir("ebooks-zipped")

if not os.path.exists("ebooks-unzipped"):
    os.mkdir("ebooks-unzipped")


# Download the book index, and unzip it.
fetch(MIRROR, "GUTINDEX.zip", "indexes/GUTINDEX.zip")
if not os.path.exists("indexes/GUTINDEX.ALL") or older("indexes/GUTINDEX.ALL", "indexes/GUTINDEX.zip"):
    print "Extracting GUTINDEX.ALL from GUTINDEX.zip..."
    zipfile.ZipFile("indexes/GUTINDEX.zip").extractall("indexes/")


# Download the file index, and gunzip it.
fetch(MIRROR, "ls-lR.gz", "indexes/ls-lR.gz")
if not os.path.exists("indexes/ls-lR") or older("indexes/ls-lR", "indexes/ls-lR.gz"):
    print "Extracting ls-lR from ls-lR.gz..."
    inf = gzip.open("indexes/ls-lR.gz", "rb")
    outf = open("indexes/ls-lR", "wb")
    outf.write(inf.read())
    inf.close()
    outf.close()


# Parse the file index
print "Parsing file index..."
mirrordir = {}
mirrorname = {}
re_txt0file = re.compile(r".*? (\d+\-0\.zip)") # UTF-8 encoded (?)
re_txt8file = re.compile(r".*? (\d+\-8\.zip)") # latin-8 encoded (?)
re_txtfile = re.compile(r".*? (\d+\.zip)") # ascii encoded (?)
for line in open("indexes/ls-lR"):
    if line.startswith("./"):
        line = line[2:].strip()
        if line.endswith(":"):
            line = line[:-1]
        if line.endswith("old") or "-" in line:
            continue
        lastseendir = line
        continue
    m = re_txt0file.match(line)
    if not m:
        m = re_txt8file.match(line)
    if not m:
        m = re_txtfile.match(line)
    if m:
        filename = m.groups()[0]
        if "-" in filename: # For filenames like '12104-0.zip'.
            nr, _ = filename.split("-")
        elif "." in filename: # For filenames like '32901.zip'.
            nr, _ = filename.split(".")
        else:
            print "Unexpected filename:", filename
        ebookno = int(nr)
        if not ebookno in mirrordir:
            mirrordir[ebookno] = lastseendir
            mirrorname[ebookno] = filename


# Parse the GUTINDEX.ALL file and extract all language-specific titles from it.
print "Parsing book index..."
inpreamble = True
ebooks = {} # number -> title
ebookslanguage = {} # number -> language
ebookno = None
nr = 0
langre = re.compile(r"\[Language: (\w+)\]")
for line in codecs.open("indexes/GUTINDEX.ALL", encoding="utf8"):
    line = line.replace(u"\xA0", u" ") # Convert non-breaking spaces to ordinary spaces.

    if inpreamble: # Skip the explanation at the start of the file.
        if "TITLE and AUTHOR" in line and "ETEXT NO." in line:
            inpreamble = False
        else:
            continue

    if not line.strip():
        continue # Ignore empty lines.

    if line.startswith("<==End of GUTINDEX.ALL"):
        break # Done.

    if line.startswith((u" ", u"\t", u"[")):
        # Attribute line; see if it specifies the language.
        m = langre.search(line)
        if m:
            language = m.group(1)
            ebookslanguage[ebookno] = language
    else:
        # Possibly title line: "The German Classics     51389"
        parts = line.strip().rsplit(" ", 1)
        if len(parts) < 2:
            continue
        title, ebookno = parts
        title = title.strip()
        try:
            if ebookno.endswith(("B", "C")):
                ebookno = ebookno[:-1]
            ebookno = int(ebookno)
            # It's a genuine title.
            ebooks[ebookno] = title
        except ValueError:
            continue # Missing or invalid ebook number

# Default language is English; mark every eBook which hasn't a language specified as English.
for nr, title in ebooks.iteritems():
    if not nr in ebookslanguage:
        ebookslanguage[nr] = "English"

if 0:
    # Print report of found eBooks.
    nr = 0
    for ebookno in sorted(ebooks.keys()):
        if ebookslanguage[ebookno] != LANGUAGE:
            continue
        titel = ebooks[ebookno].encode("ascii", "replace")
        filename = mirrorname.get(ebookno, "UNKNOWN")
        filedir = mirrordir.get(ebookno, "UNKNOWN")
        print "%d. %s (%s in %s)" % (ebookno, titel, filename, filedir)
        nr += 1
    print "%d ebooks found for language %s" % (nr, LANGUAGE)

# Fetch the eBook zips.
for nr, ebookno in enumerate(sorted(ebooks.keys())):
    if ebookslanguage[ebookno] != LANGUAGE: # Only fetch books for specified language.
        continue
    filedir = mirrordir.get(ebookno)
    filename = mirrorname.get(ebookno)
    if not filedir or not filename:
        continue
    url = MIRROR + filedir + "/" + filename
    fn = os.path.join("ebooks-zipped", filename)
    if os.path.exists(fn):
        print "(%d/%d) %s exists, download not necessary" % (nr, len(ebooks), fn)
    else:
        print "(%d/%d) downloading %s..." % (nr, len(ebooks), fn)
        # Slow with FTP mirrors; prefer a HTTP mirror.
        urllib.urlretrieve(url, fn)

        # Fast, but requires external wget utility.
        # cmd = "wget -O %s %s" % (fn, url)
        # os.system(cmd)

# Unzip them.
errors = []
for fn in glob.glob("ebooks-zipped/*.zip"):
    print "extracting", fn
    try:
        zipfile.ZipFile(fn).extractall("ebooks-unzipped/")
    except zipfile.BadZipfile:
        errors.append("Error: can't unzip %s" % fn) # Some files in the Gutenberg archive are damaged.

# Some extracted files will end up in a subdirectory. Move them up into 'ebooks-unzipped' and remove the empty subdirectory.
for dirn in glob.glob("ebooks-unzipped/*"):
    if os.path.isdir(dirn):
        print "moving", dirn
        for fn in glob.glob(os.path.join(dirn, "*")):
            parts = fn.split(os.sep)
            ofn = os.path.join("ebooks-unzipped", parts[-1])
            if os.path.exists(ofn):
                os.unlink(ofn)
            shutil.move(fn, "ebooks-unzipped")
        os.rmdir(dirn)

if errors:
    print "Errors:"
    for error in errors:
        print error
