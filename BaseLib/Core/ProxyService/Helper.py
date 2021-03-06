import time 
# Written by Pawel Garbacki, George Milescu
# see LICENSE.txt for license information

import sys
from traceback import print_exc
from time import time
from collections import deque
from threading import Lock

from BaseLib.Core.BitTornado.bencode import bencode
from BaseLib.Core.BitTornado.BT1.MessageID import ASK_FOR_HELP, STOP_HELPING, REQUEST_PIECES, CANCEL_PIECE, JOIN_HELPERS, RESIGN_AS_HELPER, DROPPED_PIECE, PROXY_HAVE, PROXY_UNHAVE

from BaseLib.Core.Overlay.OverlayThreadingBridge import OverlayThreadingBridge
from BaseLib.Core.CacheDB.CacheDBHandler import PeerDBHandler, TorrentDBHandler 
from BaseLib.Core.Utilities.utilities import show_permid_short

# ???
MAX_ROUNDS = 200
# ???
DEBUG = False

class SingleDownloadHelperInterface:
    """ This interface should contain all methods that the PiecePiecker/Helper
        calls on the SingleDownload class.
    """
    def __init__(self):
        self.frozen_by_helper = False

    def helper_set_freezing(self,val):
        self.frozen_by_helper = val

    def is_frozen_by_helper(self):
        return self.frozen_by_helper

    def is_choked(self):
        pass

    def helper_forces_unchoke(self):
        pass

    def _request_more(self, new_unchoke = False):
        pass


class Helper:
    def __init__(self, torrent_hash, num_pieces, coordinator_permid, coordinator = None):
        
        self.torrent_hash = torrent_hash
        self.coordinator = coordinator

        if coordinator_permid is not None and coordinator_permid == '':
            self.coordinator_permid = None
        else:
            self.coordinator_permid = coordinator_permid

        # Get coordinator ip and address
        self.coordinator_ip = None  # see is_coordinator()
        self.coordinator_port = -1
        if self.coordinator_permid is not None:
            peerdb = PeerDBHandler.getInstance()
            peer = peerdb.getPeer(coordinator_permid)
            if peer is not None:
                self.coordinator_ip = peer['ip']
                self.coordinator_port = peer['port']
        
        self.overlay_bridge = OverlayThreadingBridge.getInstance()
        
        self.reserved_pieces = [False] * num_pieces
        self.ignored_pieces = [False] * num_pieces
        self.distr_reserved_pieces = [False] * num_pieces

        self.requested_pieces = deque()
        self.requested_pieces_lock = Lock()
        
        self.counter = 0
        self.completed = False
        self.marker = [True] * num_pieces
        self.round = 0
        self.encoder = None
        self.continuations = []
        self.outstanding = None
        self.last_req_time = 0
        
        # The challenge sent by the coordinator
        self.challenge = None
        

    def test(self):
        result = self.reserve_piece(10,None)
        print >> sys.stderr,time.asctime(),'-', "reserve piece returned: " + str(result)
        print >> sys.stderr,time.asctime(),'-', "Test passed"





    def notify(self):
        """ Called by HelperMessageHandler to "wake up" the download that's
            waiting for its coordinator to reserve it a piece 
        """
        if self.outstanding is None:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: notify: No continuation waiting?"
        else:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: notify: Waking downloader"
            sdownload = self.outstanding
            self.outstanding = None # must be not before calling self.restart!
            self.restart(sdownload)
            
            #self.send_reservation()
            l = self.continuations[:] # copy just to be sure
            self.continuations = []
            for sdownload in l:
                self.restart(sdownload)

    def restart(self,sdownload):
        """ TODO ???
        """
        # Chokes can get in while we're waiting for reply from coordinator.
        # But as we were called from _request_more() we were not choked
        # just before, so pretend we didn't see the message yet.
        if sdownload.is_choked():
            sdownload.helper_forces_unchoke()
        sdownload.helper_set_freezing(False)
        sdownload._request_more()





    #
    # Send messages
    # 

    def send_join_helpers(self, permid):
        """ Send a confirmation to the coordinator that the current node will provide proxy services
        
        Called by self.got_ask_for_help()
        
        @param permid: The permid of the node that will become coordinator
        """

        if DEBUG:
            print "helper: send_join_helpers: sending a join_helpers message to", show_permid_short(permid)

        olthread_send_join_helpers_lambda = lambda:self.olthread_send_join_helpers()
        self.overlay_bridge.add_task(olthread_send_join_helpers_lambda,0)

        
    def olthread_send_join_helpers(self):
        """ Creates a bridge connection for the join helpers message to be sent
        
        Called by the overlay thread.
        """
        # TODO: ??? We need to create the message according to protocol version, so need to pass all info.
        olthread_join_helpers_connect_callback_lambda = lambda e,d,p,s:self.olthread_join_helpers_connect_callback(e,d,p,s)
        self.overlay_bridge.connect(self.coordinator_permid,olthread_join_helpers_connect_callback_lambda)


    def olthread_join_helpers_connect_callback(self,exc,dns,permid,selversion):
        """ Sends the join helpers message on the connection with the coordinator
        
        Called by the overlay thread.
        
        @param exc: Peer reachable/unreachable information. None = peer reachable
        @param dns:
        @param permid: the permid of the coordinator
        @param selversion:
        """
        if exc is None:
            # Create message according to protocol version
            message = JOIN_HELPERS + self.torrent_hash

            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: olthread_join_helpers_connect_callback: Sending JOIN_HELPERS to",show_permid_short(permid)

            self.overlay_bridge.send(permid, message, self.olthread_join_helpers_send_callback)
        elif DEBUG:
            # The coordinator is unreachable
            print >> sys.stderr,time.asctime(),'-', "helper: olthread_join_helpers_connect_callback: error connecting to",show_permid_short(permid),exc


    def olthread_join_helpers_send_callback(self, exc, permid):
        """ Callback function for error checking in network communication
        
        Called by the overlay thread.
        
        @param exc: Peer reachable/unreachable information. None = peer reachable
        @param permid: the permid of the peer that is contacted for helping
        """

        if exc is not None:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: olthread_join_helpers_send_callback: error sending message to",show_permid_short(permid),exc
        
        pass





    def send_proxy_have(self, aggregated_haves):
        """ Send a list of aggregated have and bitfield information
        
        Called by Downloader.aggregate_and_send_haves
        
        @param aggregated_haves: A Bitfield object, containing an aggregated list of stored haves
        """

        if DEBUG:
            print "helper: send_proxy_have: sending a proxy_have message to", show_permid_short(self.coordinator_permid)

        aggregated_string = aggregated_haves.tostring()
        olthread_send_proxy_have_lambda = lambda:self.olthread_send_proxy_have(aggregated_string)
        self.overlay_bridge.add_task(olthread_send_proxy_have_lambda,0)

        
    def olthread_send_proxy_have(self, aggregated_string):
        """ Creates a bridge connection for the proxy_have message to be sent
        
        Called by the overlay thread.
        
        @param aggregated_string: a bitstring of available piesces
        """
        # TODO: ??? We need to create the message according to protocol version, so need to pass all info.
        olthread_proxy_have_connect_callback_lambda = lambda e,d,p,s:self.olthread_proxy_have_connect_callback(e,d,p,s,aggregated_string)
        self.overlay_bridge.connect(self.coordinator_permid,olthread_proxy_have_connect_callback_lambda)


    def olthread_proxy_have_connect_callback(self,exc,dns,permid,selversion, aggregated_string):
        """ Sends the proxy_have message on the connection with the coordinator
        
        Called by the overlay thread.
        
        @param exc: Peer reachable/unreachable information. None = peer reachable
        @param dns:
        @param permid: the permid of the coordinator
        @param selversion: selected (buddycast?) version
        @param aggregated_string: a bitstring of available pieces
        """
        if exc is None:
            # Create message according to protocol version
            message = PROXY_HAVE + self.torrent_hash + bencode(aggregated_string)

            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: olthread_proxy_have_connect_callback: Sending PROXY_HAVE to",show_permid_short(permid)

            self.overlay_bridge.send(permid, message, self.olthread_proxy_have_send_callback)
        elif DEBUG:
            # The coordinator is unreachable
            print >> sys.stderr,time.asctime(),'-', "helper: olthread_proxy_have_connect_callback: error connecting to",show_permid_short(permid),exc


    def olthread_proxy_have_send_callback(self, exc, permid):
        """ Callback function for error checking in network communication
        
        Called by the overlay thread.
        
        @param exc: Peer reachable/unreachable information. None = peer reachable
        @param permid: the permid of the peer that is contacted for helping
        """

        if exc is not None:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: olthread_proxy_have_send_callback: error sending message to",show_permid_short(permid),exc
        
        pass





    def send_resign_as_helper(self, permid):
        """ Send a message to the coordinator that the current node will stop providing proxy services
        
        Called by TODO
        
        @param permid: The permid of the coordinator
        """

        if DEBUG:
            print "helper: send_resign_as_helper: sending a resign_as_helper message to", permid

        olthread_send_resign_as_helper_lambda = lambda:self.olthread_send_resign_as_helper()
        self.overlay_bridge.add_task(olthread_send_resign_as_helper_lambda,0)

        
    def olthread_send_resign_as_helper(self):
        """ Creates a bridge connection for the resign_as_helper message to be sent
        
        Called by the overlay thread.
        """
        olthread_resign_as_helper_connect_callback_lambda = lambda e,d,p,s:self.olthread_resign_as_helper_connect_callback(e,d,p,s)
        self.overlay_bridge.connect(self.coordinator_permid,olthread_resign_as_helper_connect_callback_lambda)


    def olthread_resign_as_helper_connect_callback(self,exc,dns,permid,selversion):
        """ Sends the resign_as_helper message on the connection with the coordinator
        
        Called by the overlay thread.
        
        @param exc: Peer reachable/unreachable information. None = peer reachable
        @param dns:
        @param permid: the permid of the coordinator
        @param selversion:
        """
        if exc is None:
            # Create message according to protocol version
            message = RESIGN_AS_HELPER + self.torrent_hash

            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: olthread_resign_as_helper_connect_callback: Sending RESIGN_AS_HELPER to",show_permid_short(permid)

            self.overlay_bridge.send(permid, message, self.olthread_resign_as_helper_send_callback)
        elif DEBUG:
            # The coordinator is unreachable
            print >> sys.stderr,time.asctime(),'-', "helper: olthread_resign_as_helper_connect_callback: error connecting to",show_permid_short(permid),exc


    def olthread_resign_as_helper_send_callback(self,exc,permid):
        """ Callback function for error checking in network communication
        
        Called by the overlay thread.
        
        @param exc: Peer reachable/unreachable information. None = peer reachable
        @param permid: the permid of the peer that is contacted for helping
        """
        
        if exc is not None:
            if DEBUG:
                print >> sys.stderr,time.asctime(),'-', "helper: olthread_resign_as_helper_send_callback: error sending message to",show_permid_short(permid),exc
        
        pass

    
    
    

    #
    # Got (received) messages
    # 
    def got_ask_for_help(self, permid, infohash, challenge):
        """ Start helping a coordinator or reply with an resign_as_helper message
        
        @param permid: The permid of the node sending the help request message
        @param infohash: the infohash of the torrent for which help is requested 
        @param challenge: The challenge sent by the coordinator
        """
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "helper: got_ask_for_help: will answer to the help request from", show_permid_short(permid)
        if self.can_help(infohash):
            # Send JOIN_HELPERS
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "helper: got_ask_for_help: received a help request, going to send join_helpers"
            self.send_join_helpers(permid)
            self.challenge = challenge
        else:
            # Send RESIGN_AS_HELPER
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "helper: got_ask_for_help: received a help request, going to send resign_as_helper"
            self.send_resign_as_helper(permid)
            return False

        return True


    def can_help(self, infohash):
        """ Decide if the current node can help a coordinator for the current torrent
        
        @param infohash: the infohash of the torrent for which help is requested 
        """        
        #TODO: test if I can help the cordinator to download this file
        #Future support: make the decision based on my preference
        return True





    def got_stop_helping(self, permid, infohash):
        """ Stop helping a coordinator
        
        @param permid: The permid of the node sending the message
        @param infohash: the infohash of the torrent for which help is released 
        """        
        #TODO: decide what to do here
        return True





    def got_request_pieces(self, permid, piece):
        """ Start downloading the pieces that the coordinator requests
        
        @param permid: The permid of the node requesting the pieces
        @param piece: a piece number, that is going to be downloaded 
        """        
        if DEBUG:
            print "helper: got_request_pieces: received request_pieces for piece", piece

        # Mark the piece as requested in the local data structures
        self.reserved_pieces[piece] = True
#        if self.distr_reserved_pieces[piece] == True:
            # if the piece was previously requested by the same coordinator, don't do anything
            #self.distr_reserved_pieces[piece] = True
#            print "Received duplicate proxy request for", piece
#            return

        self.distr_reserved_pieces[piece] = True
        self.ignored_pieces[piece] = False
        
        self.requested_pieces_lock.acquire()
        self.requested_pieces.append(piece)
        self.requested_pieces_lock.release()

        # Start data connection
        self.start_data_connection()

    def start_data_connection(self):
        """ Start a data connection with the coordinator
        
        @param permid: The permid of the coordinator
        """
        # Do this always, will return quickly when connection already exists
        dns = (self.coordinator_ip, self.coordinator_port)
        if DEBUG:
            print >> sys.stderr,time.asctime(),'-', "helper: start_data_connection: Starting data connection to coordinator at", dns
        
        self.encoder.start_connection(dns, id = None, coord_con = True, challenge = self.challenge)



    #
    # Util functions
    #
    def is_coordinator(self, permid):
        """ Check if the permid is the current coordinator
        
        @param permid: The permid to be checked if it is the coordinator
        @return: True, if the permid is the current coordinator; False, if the permid is not the current coordinator
        """
        # If we could get coordinator_ip, don't help
        if self.coordinator_ip is None:
            return False

        if self.coordinator_permid == permid:
            return True
        else:
            return False


    def next_request(self):
        """ Returns the next piece in the list of coordinator-requested pieces
        
        Called by the PiecePicker
        
        @return: a piece number, if there is a requested piece pending download; None, if there is no pending piece
        """
        self.requested_pieces_lock.acquire()
        if len(self.requested_pieces) == 0:
            self.requested_pieces_lock.release()
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "helper: next_request: no requested pieces yet. Returning None"
            return None
        else:
            next_piece = self.requested_pieces.popleft()
            self.requested_pieces_lock.release()
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "helper: next_request: Returning", next_piece
            return next_piece
        
        
    def set_encoder(self, encoder):
        """ Sets the current encoder.
        
        Called from download_bt1.py
        
        @param encoder: the new encoder that will be set
        """
        self.encoder = encoder
        self.encoder.set_coordinator_ip(self.coordinator_ip)
        # To support a helping user stopping and restarting a torrent
        if self.coordinator_permid is not None:
            self.start_data_connection()   


    def get_coordinator_permid(self):
        """ Returns the coordinator permid
        
        Called from SingleDownload.py
        
        @return: Coordinator permid
        """
        return self.coordinator_permid


    def is_reserved(self, piece):
        """ Check if a piece is reserved (requested) by a coordinator
        
        Called by the network thread (Interface for PiecePicker and Downloader)
        
        @param piece: the piece whose status is to be checked
        @return: True, if the piece is reqested by a coordinator; False, otherwise.
        """
        if self.reserved_pieces[piece] or (self.coordinator is not None and self.is_complete()):
            return True
        return self.reserved_pieces[piece]


    def is_ignored(self, piece):
        """ Check if a piece is ignored by a coordinator
        
        Called by the network thread (Interface for PiecePicker and Downloader)
        
        @param piece: the piece whose status is to be checked
        @return: True, if the piece is ignored by a coordinator; False, otherwise.
        """
        if not self.ignored_pieces[piece] or (self.coordinator is not None and self.is_complete()):
            return False
        return self.ignored_pieces[piece]


    def is_complete(self):
        """ Check torrent is completely downloaded
        
        Called by the network thread (Interface for PiecePicker and Downloader)
        
        @return: True, all the pieces are downloaded; False, otherwise.
        """
        if self.completed:
            return True
        
        self.round = (self.round + 1) % MAX_ROUNDS
        
        if self.round != 0:
            return False
        if self.coordinator is not None:
            self.completed = (self.coordinator.reserved_pieces == self.marker)
        else:
            self.completed = (self.distr_reserved_pieces == self.marker)
        return self.completed