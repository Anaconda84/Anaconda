import time 
# Written by Arno Bakker, Jie Yang
# see LICENSE.txt for license information
#
# Send free-form queries to all the peers you are connected to.
#
# TODO: make sure we return also items from download history, but need to verify if 
# their status is still checked.
#
#

import os
import sys
import re
from time import time
from sets import Set
from traceback import print_stack, print_exc
import datetime
import time as T

from M2Crypto import Rand

from BaseLib.Core.simpledefs import *
from BaseLib.Core.BitTornado.bencode import bencode,bdecode
from BaseLib.Core.CacheDB.sqlitecachedb import bin2str, str2bin
from BaseLib.Core.CacheDB.CacheDBHandler import ChannelCastDBHandler,PeerDBHandler
from BaseLib.Core.BitTornado.BT1.MessageID import *
from BaseLib.Core.BuddyCast.moderationcast_util import *
from BaseLib.Core.TorrentDef import TorrentDef
from BaseLib.Core.Overlay.SecureOverlay import OLPROTO_VER_SIXTH, OLPROTO_VER_NINETH, OLPROTO_VER_ELEVENTH, OLPROTO_VER_TWELFTH, OLPROTO_VER_THIRTEENTH
from BaseLib.Core.Utilities.utilities import show_permid_short,show_permid
from BaseLib.Core.Statistics.Logger import OverlayLogger
from BaseLib.Core.Utilities.unicode import dunno2unicode
from BaseLib.Core.Search.SearchManager import split_into_keywords

MAX_RESULTS = 20
QUERY_ID_SIZE = 20
MAX_QUERY_REPLY_LEN = 100*1024    # 100K
MAX_PEERS_TO_QUERY = 20

DEBUG = False

class FakeUtility:
    
    def __init__(self,config_path):
        self.config_path = config_path
        
    def getConfigPath(self):
        return self.config_path


class RemoteQueryMsgHandler:
    
    __single = None
    
    def __init__(self):
        if RemoteQueryMsgHandler.__single:
            raise RuntimeError, "RemoteQueryMsgHandler is singleton"
        RemoteQueryMsgHandler.__single = self

        self.connections = {}    # only connected remote_search_peers -> selversion
        self.query_ids2rec = {}    # ARNOCOMMENT: TODO: purge old entries...
        self.overlay_log = None
        self.registered = False
        self.logfile = None 

    def getInstance(*args, **kw):
        if RemoteQueryMsgHandler.__single is None:
            RemoteQueryMsgHandler(*args, **kw)
        return RemoteQueryMsgHandler.__single
    getInstance = staticmethod(getInstance)
        

    def register(self,overlay_bridge,launchmany,config,bc_fac,log=''):
        if DEBUG:
            print >> sys.stderr,time.asctime(),'-', "rquery: register"
        self.overlay_bridge = overlay_bridge
        self.session =  launchmany.session
        self.torrent_db = launchmany.torrent_db
        self.peer_db = launchmany.peer_db
        self.channelcast_db = launchmany.channelcast_db
        # debug
        # self.superpeer_db = launchmany.superpeer_db
        
        self.config = config
        self.bc_fac = bc_fac # May be None
        if log:
            self.overlay_log = OverlayLogger.getInstance(log)
        self.torrent_dir = os.path.abspath(self.config['torrent_collecting_dir'])
        self.registered = True
        
        # 14-04-2010, Andrea: limit the size of channel query results.
        # see create_channel_query_reply (here) and process_query_reply
        # for other details. (The whole thing is done to avoid freezes in the GUI
        # when there are too many results)
        self.max_channel_query_results = self.config['max_channel_query_results']
        
        

    #
    # Incoming messages
    # 
    def handleMessage(self,permid,selversion,message):
        if not self.registered:
            return True
        
        t = message[0]
        if t == QUERY:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "rquery: Got QUERY",len(message)
            return self.recv_query(permid,message,selversion)
        if t == QUERY_REPLY:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "rquery: Got QUERY_REPLY",len(message)
            return self.recv_query_reply(permid,message,selversion)
        else:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "rquery: UNKNOWN OVERLAY MESSAGE", ord(t)
            return False

    #
    # Incoming connections
    #
    def handleConnection(self,exc,permid,selversion,locally_initiated):
        if not self.registered:
            return True
        
        if DEBUG:
            print >> sys.stderr,time.asctime(),'-', "rquery: handleConnection",exc,"v",selversion,"local",locally_initiated, ";#conn:", len(self.connections)
        
        if selversion < OLPROTO_VER_SIXTH:
            return True

        if exc is None:
            self.connections[permid] = selversion
            #superpeers = self.superpeer_db.getSuperPeers()
            #if permid in superpeers:
             #   print >> sys.stderr,time.asctime(),'-', "rquery: handleConnection: Connect to superpeer"
        else:
            try:
                del self.connections[permid]
            except:
                pass
                #print_exc()

        return True

    #
    # Send query
    # 
    def send_query(self,query,usercallback,max_peers_to_query=MAX_PEERS_TO_QUERY):
        """ Called by GUI Thread """
        if max_peers_to_query is None or max_peers_to_query > MAX_PEERS_TO_QUERY:
            max_peers_to_query = MAX_PEERS_TO_QUERY
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rquery: send_query",`query`,max_peers_to_query
        if max_peers_to_query > 0:
            send_query_func = lambda:self.network_send_query_callback(query,usercallback,max_peers_to_query)
            self.overlay_bridge.add_task(send_query_func,0)


    def network_send_query_callback(self,query,usercallback,max_peers_to_query):
        """ Called by overlay thread """
        p = self.create_query(query,usercallback)
        m = QUERY+p
        query_conn_callback_lambda = lambda exc,dns,permid,selversion:self.conn_callback(exc,dns,permid,selversion,m)
        
        if query.startswith("CHANNEL"):
            wantminoversion = OLPROTO_VER_THIRTEENTH  # channel queries and replies only for the latest version (13) 
        elif query.startswith("SIMPLE+METADATA"):
            wantminoversion = OLPROTO_VER_TWELFTH
        else:
            wantminoversion =  OLPROTO_VER_SIXTH
            
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rquery: send_query: Connected",len(self.connections),"peers; minoversion=", wantminoversion
        
        #print "******** send query net cb:", query, len(self.connections), self.connections
        
        # 1. See how many peers we already know about from direct connections
        peers_to_query = 0
        for permid,selversion in self.connections.iteritems():
            if selversion >= wantminoversion:
                self.overlay_bridge.connect(permid,query_conn_callback_lambda)
                peers_to_query += 1
        
        # 2. If not enough, get some remote-search capable peers from BC
        if peers_to_query < max_peers_to_query and self.bc_fac and self.bc_fac.buddycast_core:
            query_cand = self.bc_fac.buddycast_core.getRemoteSearchPeers(max_peers_to_query-peers_to_query,wantminoversion)
            for permid in query_cand:
                if permid not in self.connections:    # don't call twice
                    self.overlay_bridge.connect(permid,query_conn_callback_lambda)
                    peers_to_query += 1
        
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rquery: send_query: Sent to",peers_to_query,"peers; query=", query
        
    def create_query(self,query,usercallback):
        d = {}
        d['q'] = query.strip().encode("UTF-8")
        d['id'] = self.create_and_register_query_id(query,usercallback)
        return bencode(d)
        
    def create_and_register_query_id(self,query,usercallback):
        id = Rand.rand_bytes(QUERY_ID_SIZE)
        queryrec = {'query':query,'usercallback':usercallback}
        self.query_ids2rec[id] = queryrec
        return id
        
    def is_registered_query_id(self,id):
        if id in self.query_ids2rec:
            return self.query_ids2rec[id]
        else:
            return None
        
    def conn_callback(self,exc,dns,permid,selversion,message):
        if exc is None and selversion >= OLPROTO_VER_SIXTH:
            self.overlay_bridge.send(permid,message,self.send_callback)
            
    def send_callback(self,exc,permid):
        #print "******* query was sent to", show_permid_short(permid), exc
        pass
    
    
    #
    # Receive query
    # 
    
    def recv_query(self,permid,message,selversion):
        if selversion < OLPROTO_VER_SIXTH:
            return False

        # Unpack
        try:
            d = bdecode(message[1:])
        except:
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rquery: Cannot bdecode QUERY message"
            #print_exc()
            return False
        
        if not isValidQuery(d,selversion):
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rquery: QUERY invalid",`d`
            return False

        # ACCESS CONTROL, INCLUDING CHECKING IF PEER HAS NOT EXCEEDED
        # QUERY QUOTUM IS DONE in Tribler/Core/RequestPolicy.py
        #

        # Process
        self.process_query(permid, d, selversion)
        
        return True

    def set_log_file(self, logfile):
        self.logfile = open(logfile, "a") 
   
   
    def log(self, permid, decoded_message):        
        lt = T.localtime(T.time())
        timestamp = "%04d-%02d-%02d %02d:%02d:%02d" % (lt[0], lt[1], lt[2], lt[3], lt[4], lt[5])
        ip = self.peer_db.getPeer(permid, "ip")
        #ip = "x.y.z.1"
        s = "%s\t%s\t%s\t%s\n"% (timestamp, bin2str(permid), ip, decoded_message)
        
        print dunno2unicode(s)
        self.logfile.write(dunno2unicode(s)) # bin2str(
        self.logfile.flush()
    
    
    #
    # Send query reply
    #
    def process_query(self, permid, d, selversion):
        hits = None
        p = None
        sendtorrents = False

        netwq = d['q']
        if netwq.startswith("SIMPLE"): # remote query
            # Format: 'SIMPLE '+string of space separated keywords or
            #         'SIMPLE+METADATA' +string of space separated keywords
            #
            # In the future we could support full SQL queries:
            # SELECT infohash,torrent_name FROM torrent_db WHERE status = ALIVE
            
            if netwq.startswith('SIMPLE+METADATA'):
                q = d['q'][len('SIMPLE+METADATA '):]
                sendtorrents = True
            else:
                q = d['q'][len('SIMPLE '):]
                    
            uq = self.clean_netwq(q)
            kws = split_into_keywords(uq)
            hits = self.search_torrents(kws, maxhits=MAX_RESULTS,sendtorrents=sendtorrents)
            p = self.create_remote_query_reply(d['id'],hits,selversion)
            
        elif netwq.startswith("CHANNEL"): # channel query
            if DEBUG:
                print>>sys.stderr, time.asctime(),'-', "Incoming channel query", d['q']
            q = d['q'][len('CHANNEL '):]
            uq = self.clean_netwq(q,channelquery=True)
            hits = self.channelcast_db.searchChannels(uq)
            p = self.create_channel_query_reply(d['id'],hits,selversion)

        # log incoming query, if logfile is set
        if self.logfile:
            self.log(permid, q)        
     
        m = QUERY_REPLY+p

        if self.overlay_log:
            nqueries = self.get_peer_nqueries(permid)
            # RECV_MSG PERMID OVERSION NUM_QUERIES MSG
            self.overlay_log('RECV_QRY', show_permid(permid), selversion, nqueries, repr(d))

            # RPLY_QRY PERMID NUM_HITS MSG
            self.overlay_log('RPLY_QRY', show_permid(permid), len(hits), repr(p))

        self.overlay_bridge.send(permid, m, self.send_callback)
        
        self.inc_peer_nqueries(permid)

 # This function need not be used, since it is handled quite well by split_into_keywords 
    def clean_netwq(self,q,channelquery=False):
        # Filter against bad input
        uq = q.decode("UTF-8")
        newq = u''
        for i in range(0,len(uq)):
            if uq[i].isalnum() or uq[i] == ' ' or (channelquery and uq[i] == '+') or (channelquery and uq[i] == '/'):
                newq += uq[i]
        return newq
            
        
    def create_remote_query_reply(self,id,hits,selversion):
        getsize = os.path.getsize
        join = os.path.join
        d = {}
        d['id'] = id
        d2 = {}
        for torrent in hits:
            r = {}
            # NEWDBSTANDARD. Do not rename r's fields: they are part of the 
            # rquery protocol spec.
            # Arno, 2010-01-28: name DB record contains the Unicode object
            r['content_name'] = torrent['name'].encode("UTF-8")  
            r['length'] = torrent['length']
            r['leecher'] = torrent['num_leechers']
            r['seeder'] = torrent['num_seeders']
            # Arno: TODO: sending category doesn't make sense as that's user-defined
            # leaving it now because of time constraints
            r['category'] = torrent['category']
            if selversion >= OLPROTO_VER_NINETH:
                r['torrent_size'] = getsize(join(self.torrent_dir, torrent['torrent_file_name']))
            if selversion >= OLPROTO_VER_ELEVENTH:
                r['channel_permid'] = torrent['channel_permid']
                # Arno, 2010-01-28: name DB record contains the Unicode object
                r['channel_name'] = torrent['channel_name'].encode("UTF-8")
            if selversion >= OLPROTO_VER_TWELFTH and 'metadata' in torrent:
                if DEBUG:
                    print >>sys.stderr,time.asctime(),'-', "rqmh: create_query_reply: Adding torrent file"
                r['metatype'] = torrent['metatype']
                r['metadata'] = torrent['metadata']
                
            d2[torrent['infohash']] = r
        d['a'] = d2
        return bencode(d)

    def create_channel_query_reply(self,id,hits,selversion):
        d = {}
        d['id'] = id
        
        # 14-04-2010, Andrea: sometimes apperently trivial queries like 'a' can produce
        # enormouse amounts of hit that will keep the receiver busy in processing them.
        # I made an "hack" in 'gotMessage" in ChannelSearchGridManager that drops results
        # when they are more then a threshold. At this point is better to limit the results
        # from the source to use less network bandwidth
        hitslen = len(hits)
        if hitslen > self.max_channel_query_results:
            if DEBUG:
                print >> sys.stderr, time.asctime(),'-', "Too many results for query (%d). Dropping to %d." % \
                    (hitslen,self.max_channel_query_results) 
            hits = hits[:self.max_channel_query_results] #hits are ordered by timestampe descending
       
        # 09-04-2010 Andrea: this code was exactly a duplicate copy of some
        # code in channelcast module. Refactoring performed
#        d2 = {}
#        for hit in hits:
#            r = {}
#            r['publisher_id'] = str(hit[0]) # ARNOUNICODE: must be str
#            r['publisher_name'] = hit[1].encode("UTF-8")  # ARNOUNICODE: must be explicitly UTF-8 encoded
#            r['infohash'] = str(hit[2])     # ARNOUNICODE: must be str
#            r['torrenthash'] = str(hit[3])  # ARNOUNICODE: must be str
#            r['torrentname'] = hit[4].encode("UTF-8") # ARNOUNICODE: must be explicitly UTF-8 encoded
#            r['time_stamp'] = int(hit[5])
#            # hit[6]: signature, which is unique for any torrent published by a user
#            signature = hit[6]
#            d2[signature] = r
        if self.bc_fac.channelcast_core is not None:
            d2 = self.bc_fac.channelcast_core.buildChannelcastMessageFromHits(hits,selversion,fromQuery=True)
            d['a'] = d2
        else:
            d['a'] = {}
        return bencode(d)
    
    #
    # Receive query reply
    #
    def recv_query_reply(self,permid,message,selversion):
        
        #print "****** recv query reply", len(message)
        
        if selversion < OLPROTO_VER_SIXTH:
            return False
        
        #if len(message) > MAX_QUERY_REPLY_LEN:
        #    return True    # don't close

        # Unpack
        try:
            d = bdecode(message[1:])
        except:
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rquery: Cannot bdecode QUERY_REPLY message", selversion
            return False
        
        if not isValidQueryReply(d,selversion):
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rquery: not valid QUERY_REPLY message", selversion
            return False

        
        # Check auth
        queryrec = self.is_registered_query_id(d['id'])
        if not queryrec:
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rquery: QUERY_REPLY has unknown query ID", selversion
            return False

        if selversion >= OLPROTO_VER_TWELFTH:
            if queryrec['query'].startswith('SIMPLE+METADATA'):
                for infohash,torrentrec in d['a'].iteritems():
                    if not 'metatype' in torrentrec:
                        if DEBUG:
                            print >>sys.stderr,time.asctime(),'-', "rquery: QUERY_REPLY has no metatype field", selversion
                        return False

                    if not 'metadata' in torrentrec:
                        if DEBUG:
                            print >>sys.stderr,time.asctime(),'-', "rquery: QUERY_REPLY has no metadata field", selversion
                        return False
                    if torrentrec['torrent_size'] != len(torrentrec['metadata']):
                        if DEBUG:
                            print >>sys.stderr,time.asctime(),'-', "rquery: QUERY_REPLY torrent_size != len metadata", selversion
                        return False
                    try:
                        # Validity test
                        if torrentrec['metatype'] == URL_MIME_TYPE:
                            tdef = TorrentDef.load_from_url(torrentrec['metadata'])
                        else:
                            metainfo = bdecode(torrentrec['metadata'])
                            tdef = TorrentDef.load_from_dict(metainfo)
                    except:
                        if DEBUG:
                            print_exc()
                        return False
                        

        # Process
        self.process_query_reply(permid,queryrec['query'],queryrec['usercallback'],d)
        return True


    def process_query_reply(self,permid,query,usercallback,d):
        
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rquery: process_query_reply:",show_permid_short(permid),query,d
        
        if len(d['a']) > 0:
            self.unidecode_hits(query,d)
            if query.startswith("CHANNEL"):
                # 13-04-2010 Andrea: The gotRemoteHits in SearchGridManager is too slow.
                # Since it is run by the GUIThread when there are too many hits the GUI
                # gets freezed.
                # dropping some random results if they are too many. 
                # It is just an hack, a better method to improve performance should be found.
                
                if len(d['a']) > self.max_channel_query_results:
                    if DEBUG:
                        print >> sys.stderr, time.asctime(),'-', "DROPPING some answers: they where %d" % len(d['a'])
                    newAnswers = {}
                    newKeys = d['a'].keys()[:self.max_channel_query_results] 
                    for key in newKeys:
                        newAnswers[key] = d['a'][key]
                    d['a'] = newAnswers
                    
                # Andrea 05-06-2010: updates the database through channelcast. Before this was
                # done by the GUIThread in SearchGridManager    
                self.bc_fac.channelcast_core.updateChannel(permid,query,d['a'])

                # Inform user of remote channel hits
                remote_query_usercallback_lambda = lambda:usercallback(permid,query,d['a'])
            else:
                remote_query_usercallback_lambda = lambda:usercallback(permid,query,d['a'])
            
            self.session.uch.perform_usercallback(remote_query_usercallback_lambda)
        elif DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rquery: QUERY_REPLY: no results found"


    def unidecode_hits(self,query,d):
        if query.startswith("SIMPLE"):
            for infohash,r in d['a'].iteritems():
                r['content_name'] = r['content_name'].decode("UTF-8")
        elif query.startswith("CHANNEL"):
            for signature,r in d['a'].iteritems():
                r['publisher_name'] = r['publisher_name'].decode("UTF-8")
                r['torrentname'] = r['publisher_name'].decode("UTF-8")
            

    def inc_peer_nqueries(self, permid):
        peer = self.peer_db.getPeer(permid)
        try:
            if peer is not None:
                nqueries = peer['num_queries']
                if nqueries is None:
                    nqueries = 0
                self.peer_db.updatePeer(permid, num_queries=nqueries+1)
        except:
            print_exc()

    def get_peer_nqueries(self, permid):
        peer = self.peer_db.getPeer(permid)
        if peer is None:
            return 0
        else:
            return peer['num_queries']


    def search_torrents(self,kws,maxhits=None,sendtorrents=False):
        
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rquery: search for torrents matching",`kws`
        
        allhits = self.torrent_db.searchNames(kws,local=False)
        if maxhits is None:
            hits = allhits
        else:
            hits = allhits[:maxhits]
            
        colltorrdir = self.session.get_torrent_collecting_dir()
        if sendtorrents:
            
            print >>sys.stderr,time.asctime(),'-', "rqmh: search_torrents: adding torrents"
            for hit in hits:
                filename = os.path.join(colltorrdir,hit['torrent_file_name'])
                try:
                    tdef = TorrentDef.load(filename)
                    if tdef.get_url_compat():
                        metatype = URL_MIME_TYPE
                        metadata = tdef.get_url()
                    else:
                        metatype = TSTREAM_MIME_TYPE
                        metadata = bencode(tdef.get_metainfo())
                except:
                    print_exc()
                    metadata = None
                hit['metatype'] = metatype
                hit['metadata'] = metadata
                
            # Filter out hits for which we could not read torrent file (rare)
            newhits = []
            for hit in hits:
                if hit['metadata'] is not None:
                    newhits.append(hit)
            hits = newhits
            
        return hits


def isValidQuery(d,selversion):
    if not isinstance(d,dict):
        if DEBUG:
            print >> sys.stderr, time.asctime(),'-', "rqmh: not dict"
        return False
    if not ('q' in d and 'id' in d):
        if DEBUG:
            print >> sys.stderr, time.asctime(),'-', "rqmh: some keys are missing", d.keys()
        return False
    if not (isinstance(d['q'],str) and isinstance(d['id'],str)):
        if DEBUG:
            print >> sys.stderr, time.asctime(),'-', "rqmh: d['q'] or d['id'] are not of string format", d['q'], d['id']
        return False
    if len(d['q']) == 0:
        if DEBUG:
            print >> sys.stderr, time.asctime(),'-', "rqmh: len(d['q']) == 0"
        return False
    if selversion < OLPROTO_VER_TWELFTH and d['q'].startswith('SIMPLE+METADATA'):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: SIMPLE+METADATA but old olversion",`d['q']`
        return False
    idx = d['q'].find(' ')
    if idx == -1:
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: no space in q",`d['q']`
        return False
    try:
        keyws = d['q'][idx+1:]
        ukeyws = keyws.decode("UTF-8").strip().split()
        for ukeyw in ukeyws:
            if not ukeyw.isalnum():
                # Arno, 2010-02-09: Allow for BASE64-encoded permid in CHANNEL queries
                rep = ukeyw.replace("+","p").replace("/","s")
                if not rep.isalnum():
                    if DEBUG:
                        print >>sys.stderr,time.asctime(),'-', "rqmh: not alnum",`ukeyw`
                    return False
    except:
        print_exc()
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: not alnum query",`d['q']`
        return False
    if len(d) > 2: # no other keys
        if DEBUG:
            print >> sys.stderr, time.asctime(),'-', "rqmh: d has more than 2 keys"
        return False
    return True


def isValidQueryReply(d,selversion):
    if not isinstance(d,dict):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: not dict"
        return False
    if not ('a' in d and 'id' in d):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: a or id key missing"
        return False
    if not (isinstance(d['a'],dict) and isinstance(d['id'],str)):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: a or id key not dict/str"
        return False
    if not isValidHits(d['a'],selversion):
        return False
    if len(d) > 2: # no other keys
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: too many keys, got",d.keys()
        return False
    return True

def isValidHits(d,selversion):
    if not isinstance(d,dict):
        return False
    ls = d.values()
    if len(ls)>0:
        l = ls[0]
        if 'publisher_id' in l: # channel search result
            if not validChannelCastMsg(d):
                return False
        elif 'content_name' in l: # remote search
            for key in d.keys():
        #        if len(key) != 20:
        #            return False
                val = d[key]
                if not isValidRemoteVal(val,selversion):
                    return False
    return True

def isValidChannelVal(d, selversion):
    if not isinstance(d,dict):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: torrentrec: value not dict"
        return False
    if not ('publisher_id' in d and 'publisher_name' in d and 'infohash' in d and 'torrenthash' in d and 'torrentname' in d and 'time_stamp' in d):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: a: key missing, got",d.keys()
        return False
    return True

def isValidRemoteVal(d,selversion):
    if not isinstance(d,dict):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "rqmh: reply: a: value not dict"
        return False
    if selversion >= OLPROTO_VER_TWELFTH:
        if not ('content_name' in d and 'length' in d and 'leecher' in d and 'seeder' in d and 'category' in d and 'torrent_size' in d and 'channel_permid' in d and 'channel_name' in d):
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rqmh: reply: torrentrec12: key missing, got",d.keys()
            return False
        if 'metatype' in d and 'metadata' in d:
            try:
                metatype = d['metatype']
                metadata = d['metadata']
                if metatype == URL_MIME_TYPE:
                    tdef = TorrentDef.load_from_url(metadata)
                else:
                    metainfo = bdecode(metadata)
                    tdef = TorrentDef.load_from_dict(metainfo)
            except:
                if DEBUG:
                    print >>sys.stderr,time.asctime(),'-', "rqmh: reply: torrentrec12: metadata invalid"
                    print_exc()
                return False

    elif selversion >= OLPROTO_VER_ELEVENTH:
        if not ('content_name' in d and 'length' in d and 'leecher' in d and 'seeder' in d and 'category' in d and 'torrent_size' in d and 'channel_permid' in d and 'channel_name' in d):
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rqmh: reply: torrentrec11: key missing, got",d.keys()
            return False
        
    elif selversion >= OLPROTO_VER_NINETH:
        if not ('content_name' in d and 'length' in d and 'leecher' in d and 'seeder' in d and 'category' in d and 'torrent_size' in d):
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rqmh: reply: torrentrec9: key missing, got",d.keys()
            return False
    else:
        if not ('content_name' in d and 'length' in d and 'leecher' in d and 'seeder' in d and 'category' in d):
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "rqmh: reply: torrentrec6: key missing, got",d.keys()
            return False
        
#    if not (isinstance(d['content_name'],str) and isinstance(d['length'],int) and isinstance(d['leecher'],int) and isinstance(d['seeder'],int)):
#        return False
#    if len(d) > 4: # no other keys
#        return False
    return True

        
