import time 
# written by Fabian van der Werf, Arno Bakker
# Modified by Raul Jimenez to integrate KTH DHT
# see LICENSE.txt for license information

import sys
from traceback import print_exc

dht_imported = False

if sys.version.split()[0] >= '2.5':
    try:
        from Tribler.Core.DecentralizedTracking.kadtracker.kadtracker import KadTracker
        dht_imported = True
    except (ImportError), e:
        print_exc()

DEBUG = False

dht = None

def init(*args, **kws):
    global dht
    global dht_imported
    if DEBUG:
        print >>sys.stderr,time.asctime(),'-', 'dht: DHT initialization', dht_imported
    if dht_imported and dht is None:
        dht = KadTracker(*args, **kws)
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', 'dht: DHT running'

def control():

def deinit():
    global dht
    if dht is not None:
        try:
            dht.stop()
        except:
            pass
