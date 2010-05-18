
# testfiles.py
#
# Software by Michiel Overtoom, motoom@xs4all.nl, july 2009.
#
# Creates test files for toss.py

import random

count = 500
print "Creating %d test files." % count

for i in range(count):
    fn=""
    for i in range(8):
        fn += random.choice("_abcdddddefghhhhhhhhijklmnopqrstuvwxyz~")
    fn += ".txt"
    f=open(fn, "wt")
    f.write("Test file %d\n" % i)
    f.close()

print "Done."

    
