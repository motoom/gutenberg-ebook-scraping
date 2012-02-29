
# bulkdownload.py
#
# Downloads all Dutch etexts from Project Gutenberg's website.
# Todo: Implement other languages as well.
#
# Software by Michiel Overtoom, motoom@xs4all.nl, july 2009, march 2012.

import urllib2
import re
import os

# To isolate etext book numbers from the index.
# Index sourec looks like: <li class="pgdbetext"><a href="/etext/17077">Over literatuur</li>
hrefpat = re.compile("href=\"\/ebooks\/([0-9]{5})\"")

# Fetch id's of texts.  No need to parse the HTML source, since we only need to grab numbers.
ids = set()
f = urllib2.urlopen("http://www.gutenberg.org/browse/languages/nl") # all dutch etexts (approx. 400)
for line in f:
    m = hrefpat.search(line)
    if m:
        bookid=m.group(1) # 17077
        ids.add(bookid)
        print "Found ebook id", bookid
f.close()

# Fetch etexts from locations like http://www.gutenberg.org/files/25257/25257-8.txt
for id in ids:
    ofn = "%s-8.txt" % id
    if os.path.isfile(ofn):
        print "Already downloaded:", ofn
        continue

    f = None
    for filemask in ("%s.txt", "%s-8.txt", "%s-0.txt"):
        fn = filemask % id
        baseurl = "http://www.gutenberg.org/files/%s" % id
        url = "%s/%s" % (baseurl, fn)
        try:
            f = urllib2.urlopen(url)
            print "Fetching", url
            break
        except urllib2.HTTPError:
            continue
    if not f:
        print "Not found:", baseurl
        continue

    contents=f.read()
    f.close()
    if contents:
        of = open("%s-8.txt" % id,"wb")
        of.write(contents)
        of.close()
    else:
        print "Empty:", url
