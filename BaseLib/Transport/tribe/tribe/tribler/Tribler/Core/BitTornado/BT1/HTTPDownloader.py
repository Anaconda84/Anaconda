import time 
# Written by John Hoffman
# see LICENSE.txt for license information

from Tribler.Core.BitTornado.CurrentRateMeasure import Measure
from random import randint
from urlparse import urlparse
from httplib import HTTPConnection
from urllib import quote
from threading import Thread
from Tribler.Core.BitTornado.__init__ import product_name,version_short
#TODO : Diego : remove
import sys
# 2fastbt_
try:
    from Tribler.Core.CoopDownload.Helper import SingleDownloadHelperInterface
except ImportError:
    class SingleDownloadHelperInterface:
        
        def __init__(self):
            pass

# _2fastbt

try:
    True
except:
    True = 1
    False = 0

# 2fastbt_
DEBUG = False
# _2fastbt

EXPIRE_TIME = 60 * 60

VERSION = product_name+'/'+version_short

class haveComplete:
    def complete(self):
        return True
    def __getitem__(self, x):
        return True
haveall = haveComplete()

# 2fastbt_
class SingleDownload(SingleDownloadHelperInterface):
# _2fastbt
    def __init__(self, downloader, url):
# 2fastbt_
        SingleDownloadHelperInterface.__init__(self)
# _2fastbt
        self.downloader = downloader
        self.baseurl = url
        try:
            (scheme, self.netloc, path, pars, query, fragment) = urlparse(url)
        except:
            self.downloader.errorfunc('cannot parse http seed address: '+url)
            return
        if scheme != 'http':
            self.downloader.errorfunc('http seed url not http: '+url)
            return
        try:
            self.connection = HTTPConnection(self.netloc)
        except:
            self.downloader.errorfunc('cannot connect to http seed: '+url)
            return
        self.seedurl = path
        # DIE
#        if pars:
#            self.seedurl += ';'+pars
#        self.seedurl += '?'
#        if query:
#            self.seedurl += query+'&'
#        self.seedurl += 'info_hash='+quote(self.downloader.infohash)
        # DIE

        self.measure = Measure(downloader.max_rate_period)
        self.index = None
        # DIE
        print >>sys.stderr, time.asctime(),'-', "DEBUG DIEGO : SingleDownload (HTTP), SeedURL: ", self.seedurl
        self.pice_size = self.downloader.storage._piecelen( 0 )
        self.total_len = self.downloader.storage.total_length
        # DIE
        self.url = ''
        self.requests = []
        self.request_size = 0
        self.endflag = False
        self.error = None
        self.retry_period = 30
        self._retry_period = None
        self.errorcount = 0
        self.goodseed = False
        self.active = False
        self.cancelled = False
        self.resched(randint(2, 10))
        # DIE
        self.last_piece = 0
        # DIE


    def resched(self, len = None):
        if len is None:
            len = self.retry_period
        if self.errorcount > 3:
            len = len * (self.errorcount - 2)
        self.downloader.rawserver.add_task(self.download, len)

    def _want(self, index):
        if self.endflag:
            return self.downloader.storage.do_I_have_requests(index)
        else:
            return self.downloader.storage.is_unstarted(index)

    def download(self):
# 2fastbt_
        if DEBUG:
            print "http-sdownload: download()"
        if self.is_frozen_by_helper():
            if DEBUG:
                print "http-sdownload: blocked, rescheduling"
            self.resched(1)
            return
# _2fastbt    
        self.cancelled = False
        if self.downloader.picker.am_I_complete():
            self.downloader.downloads.remove(self)
            return
        self.index = self.downloader.picker.next(haveall, self._want, self)
# 2fastbt_
        if self.index is None and self.frozen_by_helper:
            self.resched(0.01)
            return
# _2fastbt
        if ( self.index is None and not self.endflag
                     and not self.downloader.peerdownloader.has_downloaders() ):
            self.endflag = True
            self.index = self.downloader.picker.next(haveall, self._want, self)
        if self.index is None:
            self.endflag = True
            self.resched()
        else:
            # DIE
            self.url = self.seedurl
            start = self.pice_size * self.index
            end   = start + self.downloader.storage._piecelen( self.index )
            if( end == self.total_len ):
                end -= 1
                self.last_piece = 1
            self.request_range = '%d-%d' % ( start, end )
#            self.url = ( self.seedurl+'&piece='+str(self.index) )
            self._get_requests()
#            if self.request_size < self.downloader.storage._piecelen(self.index):
#                self.url += '&ranges='+self._request_ranges()
            # DIE
            rq = Thread(target = self._request)
            rq.setName( "HTTPDownloader"+rq.getName() )
            rq.setDaemon(True)
            rq.start()
            self.active = True

    def _request(self):
        import encodings.ascii
        import encodings.punycode
        import encodings.idna
        
        self.error = None
        self.received_data = None
        try:
            # DIE
            #print >>sys.stderr, time.asctime(),'-', 'HTTP bytes %s/%d' % ( self.request_range, self.total_len )
            self.connection.request( 'GET',self.url, None,
                                {'Host': self.netloc,
                                 'User-Agent': VERSION,
                                 'Range' : 'bytes=%s' % self.request_range } )

#            self.connection.request('GET', self.url, None, 
#                                {'User-Agent': VERSION})
            # DIE
            r = self.connection.getresponse()
            self.connection_status = r.status
            self.received_data = r.read()
        except Exception, e:
            self.error = 'error accessing http seed: '+str(e)
            try:
                self.connection.close()
            except:
                pass
            try:
                self.connection = HTTPConnection(self.netloc)
            except:
                self.connection = None  # will cause an exception and retry next cycle
        self.downloader.rawserver.add_task(self.request_finished)

    def request_finished(self):
        self.active = False
        if self.error is not None:
            if self.goodseed:
                self.downloader.errorfunc(self.error)
            self.errorcount += 1
        if self.received_data:
            self.errorcount = 0
            if not self._got_data():
                self.received_data = None
        if not self.received_data:
            self._release_requests()
            self.downloader.peerdownloader.piece_flunked(self.index)
        if self._retry_period:
            self.resched(self._retry_period)
            self._retry_period = None
            return
        self.resched()

    def _got_data(self):
        # DIE
        #print >>sys.stderr, time.asctime(),'-', "DIEGO DEBUG : response status = ", self.connection_status
        # DIE
        if self.connection_status == 503:   # seed is busy
            try:
                self.retry_period = max(int(self.received_data), 5)
            except:
                pass
            return False
        # DIE
        # 206 = partial download OK
        if self.connection_status != 200 and self.connection_status != 206:
        # DIE
            self.errorcount += 1
            return False
        # DIE
        # TODO : Tune _retry_period (as low as possible)
        self._retry_period = 0.001
        if not self.last_piece:
             self.received_data = self.received_data[:-1] # trim last byte (probably \n or \r)
        else:
             self.last_piece = 0

#        self._retry_period = 1
        # DIE
        if len(self.received_data) != self.request_size:
            if self.goodseed:
                self.downloader.errorfunc('corrupt data from http seed - redownloading')
            return False
        self.measure.update_rate(len(self.received_data))
        self.downloader.measurefunc(len(self.received_data))
        if self.cancelled:
            return False
        if not self._fulfill_requests():
            return False
        if not self.goodseed:
            self.goodseed = True
            self.downloader.seedsfound += 1
        if self.downloader.storage.do_I_have(self.index):
            self.downloader.picker.complete(self.index)
            self.downloader.peerdownloader.check_complete(self.index)
            self.downloader.gotpiecefunc(self.index)
        return True
    
    def _get_requests(self):
        self.requests = []
        self.request_size = 0L
        while self.downloader.storage.do_I_have_requests(self.index):
            r = self.downloader.storage.new_request(self.index)
            self.requests.append(r)
            self.request_size += r[1]
        self.requests.sort()

    def _fulfill_requests(self):
        start = 0L
        success = True
        while self.requests:
            begin, length = self.requests.pop(0)
# 2fastbt_
            if not self.downloader.storage.piece_came_in(self.index, begin, [],
                            self.received_data[start:start+length], length):
# _2fastbt
                success = False
                break
            start += length
        return success

    def _release_requests(self):
        for begin, length in self.requests:
            self.downloader.storage.request_lost(self.index, begin, length)
        self.requests = []

    def _request_ranges(self):
        s = ''
        begin, length = self.requests[0]
        for begin1, length1 in self.requests[1:]:
            if begin + length == begin1:
                length += length1
                continue
            else:
                if s:
                    s += ','
                s += str(begin)+'-'+str(begin+length-1)
                begin, length = begin1, length1
        if s:
            s += ','
        s += str(begin)+'-'+str(begin+length-1)
        return s

# 2fastbt_
    def helper_forces_unchoke(self):
        pass

    def helper_set_freezing(self,val):
        self.frozen_by_helper = val
# _2fastbt


    
class HTTPDownloader:
    def __init__(self, storage, picker, rawserver,
                 finflag, errorfunc, peerdownloader,
                 max_rate_period, infohash, measurefunc, gotpiecefunc):
        self.storage = storage
        self.picker = picker
        self.rawserver = rawserver
        self.finflag = finflag
        self.errorfunc = errorfunc
        self.peerdownloader = peerdownloader
        self.infohash = infohash
        self.max_rate_period = max_rate_period
        self.gotpiecefunc = gotpiecefunc
        self.measurefunc = measurefunc
        self.downloads = []
        self.seedsfound = 0

    def make_download(self, url):
        # DIE
        print >>sys.stderr, time.asctime(),'-', "DIEGO DEBUG : make_download : URL = ", url
        # DIE
        self.downloads.append(SingleDownload(self, url))
        return self.downloads[-1]

    def get_downloads(self):
        if self.finflag.isSet():
            return []
        return self.downloads

    def cancel_piece_download(self, pieces):
        for d in self.downloads:
            if d.active and d.index in pieces:
                d.cancelled = True
