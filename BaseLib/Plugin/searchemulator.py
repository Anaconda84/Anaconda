import time 

import sys
import urllib
import socket

url = 'http://127.0.0.1:6879/search?q=episode&collection=metafeed&metafeed=http%3A%2F%2Fp2pnextfeed1.rad0.net%2Fcontent%2Ffeed%2Fbbc'
print >>sys.stderr,time.asctime(),'-', "searchemu: opening"
x = urllib.urlopen(url)
print >>sys.stderr,time.asctime(),'-', "searchemu: reading"
print >>sys.stderr, time.asctime(),'-', x.read()
