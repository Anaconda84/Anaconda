import time 
# Written by Arno Bakker, Diego Rabioli
# see LICENSE.txt for license information
#
# Notes: 
# - Implement play while hashcheck?
#        Not needed when proper shutdown & restart was done.
# - load_checkpoint with DLSTATUS_DOWNLOADING for Plugin? 
#        Nah, if we start BG when plugin started we have a video to play soon,
#        so start others in STOPPED state (rather than switching them all
#        to off and restart one in VOD mode just after)
#

# History:
#
# NSSA API 1.0.1rc1
#
#     * Added INFO message to convey NSSA info to plugin for providing feedback
#       to the user.
#
# NSPlugin JavaScript API 1.0.1rc1
#     * Added input.p2pstatus read-only property giving the latest status as
#       reported by the NSSA.
#
# 

import os
import sys
import time
import random
import binascii
import tempfile
import urllib
from cStringIO import StringIO
from base64 import b64encode
from traceback import print_exc,print_stack
from threading import Thread,currentThread,Lock

if sys.platform == "win32":
    import win32event
    import win32api

try:
    import wxversion
    wxversion.select('2.8')
except:
    pass
import wx

from Tribler.Core.API import *
from Tribler.Core.osutils import *
from Tribler.Core.Utilities.utilities import get_collected_torrent_filename
from Tribler.Utilities.LinuxSingleInstanceChecker import *
from Tribler.Utilities.Instance2Instance import InstanceConnectionHandler,InstanceConnection
from Tribler.Utilities.TimedTaskQueue import TimedTaskQueue
from Tribler.Player.BaseApp import BaseApp
from Tribler.Player.swarmplayer import get_status_msgs
from Tribler.Plugin.defs import *
from Tribler.Plugin.Search import *
from Tribler.Plugin.AtomFeedParser import *

from Tribler.Video.defs import *
from Tribler.Video.utils import videoextdefaults
from Tribler.Video.VideoServer import VideoHTTPServer,MultiHTTPServer

from Tribler.Core.Statistics.StatusReporter import get_reporter_instance


DEBUG = False
ALLOW_MULTIPLE = False


class BackgroundApp(BaseApp):

    def __init__(self, redirectstderrout, appname, params, single_instance_checker, installdir, i2iport, sport):

        self.videoHTTPServer = VideoHTTPServer(VIDEOHTTP_LISTENPORT)
        self.videoHTTPServer.register(self.videoservthread_error_callback,self.videoservthread_set_status_callback)
        self.videoHTTPServer.background_serve()

        #self.searchHTTPServer = MultiHTTPServer(VIDEOHTTP_LISTENPORT+1)
        #self.searchHTTPServer.register(self.videoservthread_error_callback,self.videoservthread_set_status_callback)
        self.searchHTTPServer = self.videoHTTPServer

        BaseApp.__init__(self, redirectstderrout, appname, params, single_instance_checker, installdir, i2iport, sport)
        
        # SEARCH:P2P
        # Maps a query ID to the original searchstr, timestamp and all hits (local + remote)
        self.id2hits = Query2HitsMap()
        
        # Maps a URL path received by HTTP server to the requested resource,
        # reading or generating it dynamically.
        #
        # For saving .torrents received in hits to P2P searches using
        # SIMPLE+METADATA queries
        self.tqueue = TimedTaskQueue(nameprefix="BGTaskQueue")
        self.searchmapper = SearchPathMapper(self.s,self.id2hits,self.tqueue)
        self.hits2anypathmapper = Hits2AnyPathMapper(self.s,self.id2hits)
        
        self.searchHTTPServer.add_path_mapper(self.searchmapper)
        self.searchHTTPServer.add_path_mapper(self.hits2anypathmapper)
        self.searchHTTPServer.background_serve()
        self.searchurl = 'http://127.0.0.1:'+str(self.searchHTTPServer.get_port())+URLPATH_SEARCH_PREFIX


        # Maps Downloads to a using InstanceConnection and streaminfo when it 
        # plays. So it contains the Downloads in VOD mode for which there is
        # active interest from a plugin.
        #
        # At the moment each Download is used/owned by a single IC and a new
        # request for the same torrent will stop playback to the original IC
        # and resume it to the new user.
        #
        self.dusers = {}   
        self.approxplayerstate = MEDIASTATE_STOPPED

        self.counter = 0 # counter for the stats reported periodically
        self.interval = 120 # report interval
        
        if sys.platform == "win32":
            # If the BG Process is started by the plug-in notify it with an event
            startupEvent = win32event.CreateEvent( None, 0, 0, 'startupEvent' )
            win32event.SetEvent( startupEvent )
            win32api.CloseHandle( startupEvent ) # TODO : is it possible to avoid importing win32api just to close an handler?

    def OnInit(self):
        try:
            # Do common initialization
            BaseApp.OnInitBase(self)
            print >>sys.stderr,time.asctime(),'-', "bg: Awaiting commands"
            return True

        except Exception,e:
            print_exc()
            self.show_error(str(e))
            self.OnExit()
            return False


    # Arno: SEARCH: disable overlay for now
    # Also need to ensure that *stats*db SQL scripts are copied along during
    # build and crap.
    """
    def configure_session(self):
        # Leave buddycast, etc. enabled for SEARCH
        self.sconfig.set_social_networking(False)
        self.sconfig.set_bartercast(False)
        self.sconfig.set_crawler(False) # Arno: Cleanup million stats dbs first
    """

    #
    # InstanceConnectionHandler interface. Called by Instance2InstanceThread
    #
    def external_connection_made(self,s):
        ic = BGInstanceConnection(s,self,self.readlinecallback,self.videoHTTPServer)
        self.singsock2ic[s] = ic
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "bg: Plugin connection_made",len(self.singsock2ic),"++++++++++++++++++++++++++++++++++++++++++++++++"
          
        # Arno: Concurrency problems getting SEARCHURL message to work, 
        # JavaScript can't always read it. TODO  
        ##ic.searchurl(self.searchurl)

    def connection_lost(self,s):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "bg: Plugin: connection_lost ------------------------------------------------" 

        ic = self.singsock2ic[s]
        InstanceConnectionHandler.connection_lost(self,s)
        wx.CallAfter(self.gui_connection_lost,ic)
        
    def gui_connection_lost(self,ic):
        # IC may or may not have been shutdown:
        # Not: sudden browser crashes
        # Yes: controlled stop via ic.shutdown()
        ic.shutdown() # idempotent
        
        # Now apply cleanup policy to the Download, but only after X seconds
        # so if the plugin comes back with a new request for the same stuff
        # we can give it to him pronto. This is expected to happen a lot due
        # to page reloads / history navigation.
        #
        ic_delayed_remove_if_lambda = lambda:self.i2ithread_delayed_remove_if_not_complete(ic)
        # h4x0r, abuse Istance2Instance server task queue for the delay
        self.i2is.add_task(ic_delayed_remove_if_lambda,20.0)
        
    def i2ithread_delayed_remove_if_not_complete(self,ic):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "bg: i2ithread_delayed_remove_if_not_complete"
        wx.CallAfter(self.gui_delayed_remove_if_not_complete,ic)
        
    def gui_delayed_remove_if_not_complete(self,ic):
        for d,duser in self.dusers.iteritems():
            if duser['uic'] == ic:
                # should not remove download if in the meantime a
                # new request for this content has been made.
                # In this case the Download is still used by the old IC.
                d.set_state_callback(self.sesscb_remove_playing_callback)
                break
            
    def remove_playing_download(self,d2remove):
        """ Called when sesscb_remove_playing_callback has determined that
        we should remove this Download, because it would take too much
        bandwidth to download it and the user is apparently no longer
        interested. 
        """
        BaseApp.remove_playing_download(self,d2remove)
        if d2remove in self.dusers:
            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "bg: remove_playing_download"
            if 'streaminfo' in self.dusers[d2remove]:
                stream = self.dusers[d2remove]['streaminfo']['stream']
                stream.close() # Close original stream. 
            del self.dusers[d2remove]
        
        
    def i2ithread_readlinecallback(self,ic,cmd):
        """ Called by Instance2Instance thread """
        wx.CallAfter(self.gui_readlinecallback,ic,cmd)
        
    def gui_readlinecallback(self,ic,cmd):
        """ Receive command from Plugin """
        
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "bg: Got command:",cmd
        try:
            # START command
            if cmd.startswith( 'START' ):
                torrenturl = cmd.partition( ' ' )[2]
                if torrenturl is None:
                    raise ValueError('bg: Unformatted START command')
                else:
                    self.get_torrent_start_download(ic,torrenturl)
        
            # SHUTDOWN command
            elif cmd.startswith( 'SHUTDOWN' ):
                ic.shutdown()
            #elif cmd.startswith( 'SEARCH' ):
            #    searchstr = cmd.partition(' ')[2]
            #    self.process_search_metafeed(ic,searchstr)
            else:
                raise ValueError('bg: Unknown command: '+cmd)
        except:
            print_exc()
            ic.shutdown()
    
    
    def get_torrent_start_download(self,ic,url):
        """ Retrieve torrent file from url and start it in VOD mode, if not already """
        tdef  = TorrentDef.load_from_url(url)
        
        # Select which video to play (if multiple)
        if tdef.get_live():
            videofiles = tdef.get_files()
        else:
            videofiles = tdef.get_files(exts=videoextdefaults)
        if len(videofiles) == 1:
            dlfile = videofiles[0]
        elif len(videofiles) == 0:
            raise ValueError("bg: get_torrent_start_download: No video files found! Giving up")
        elif len(videofiles) > 1:
            raise ValueError("bg: get_torrent_start_download: Too many files found! Giving up")

        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "bg: get_torrent_start_download: Found video file",dlfile

        infohash = tdef.get_infohash()
        oldd = None
        for d in self.s.get_downloads():
            if d.get_def().get_infohash() == infohash:
                oldd = d
                break
        
        #
        # Start a new Download, or if it already exists, start playback from
        # beginning. This means that we don't currently support two ICs
        # playing the same video. That is, two browser windows cannot play the
        # same video.
        #
        if oldd is None or (oldd not in self.downloads_in_vodmode):
            # New Download, or Download exists, but not in VOD mode, restart
          
            if DEBUG:
                if oldd is None:
                    print >>sys.stderr,time.asctime(),'-', "bg: get_torrent_start_download: Starting new Download"
                else:
                    print >>sys.stderr,time.asctime(),'-', "bg: get_torrent_start_download: Restarting old Download in VOD mode"
            
            d = self.start_download(tdef,dlfile)
            duser = {'uic':ic}
            self.dusers[d] = duser
        else:
            # oldd is already running in VOD mode. If it's a VOD torrent we
            # don't need to restart, we can just seek(0) on the stream.
            # If it's a live torrent, we should tell EOF to any old IC and
            # continue playback to the new IC where it left off.
            #
            duser = self.dusers[d]
            olduic = duser['uic']
            olduic.shutdown()
            duser['uic'] = ic
            if 'streaminfo' not in duser:
                # Hasn't started playing yet, ignore.
                pass
            else:
                # Already playing. Tell previous owner IC to quit, let new IC 
                # start either from start (VOD) or where previous left off 
                # (live).
                if not tdef.get_live():
                    duser['streaminfo']['stream'].seek(0)
                ic.set_streaminfo(duser['streaminfo'])
                
                ic.start_playback(infohash)
                
        duser['said_start_playback'] = False
        duser['decodeprogress'] = 0
        
    #
    # DownloadStates
    #
    def gui_states_callback(self,dslist,haspeerlist):
        """ Override BaseApp """
        (playing_dslist,totalhelping,totalspeed) = BaseApp.gui_states_callback(self,dslist,haspeerlist)
        try:
            self.report_periodic_vod_stats(playing_dslist)
        except:
            print_exc()
       
        for ds in playing_dslist:
            d = ds.get_download()
            duser = self.dusers[d]
            uic = duser['uic']
            
            # Generate info string for all
            [topmsg,msg,duser['said_start_playback'],duser['decodeprogress']] = get_status_msgs(ds,self.approxplayerstate,self.appname,duser['said_start_playback'],duser['decodeprogress'],totalhelping,totalspeed)
            info = msg
            #if DEBUG:
            #    print >>sys.stderr, time.asctime(),'-', 'bg: 4INFO: Sending',info
            uic.info(info)
            
    def sesscb_vod_event_callback( self, d, event, params ):
        """ Registered by BaseApp. Called by SessionCallbackThread """
        wx.CallAfter(self.gui_vod_event_callback,d,event,params)
        
    def gui_vod_event_callback( self, d, event, params ):
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', "bg: gui_vod_event_callback: Event: ", event
            print >>sys.stderr,time.asctime(),'-', "bg: gui_vod_event_callback: Params: ", params
        
        if event == VODEVENT_START:
            if params['filename']:
                stream = open( params['filename'], "rb" )
            else:
                stream = params['stream']
    
            blocksize = d.get_def().get_piece_length()
            #Ric: add svc on streaminfo, added bitrate
            streaminfo = { 'mimetype': params['mimetype'], 'stream': stream, 'length': params['length'], 'blocksize':blocksize, 'svc': d.get_mode() == DLMODE_SVC, 'bitrate': params['bitrate'] }

            duser = self.dusers[d]
            duser['streaminfo'] = streaminfo
            duser['uic'].set_streaminfo(duser['streaminfo'])
            duser['uic'].start_playback(d.get_def().get_infohash())
            
            self.approxplayerstate = MEDIASTATE_PLAYING
            
        elif event == VODEVENT_PAUSE:
            duser = self.dusers[d]
            duser['uic'].pause()
            self.approxplayerstate = MEDIASTATE_PAUSED
            
        elif event == VODEVENT_RESUME:
            duser = self.dusers[d]
            duser['uic'].resume()
            self.approxplayerstate = MEDIASTATE_PLAYING

    def get_supported_vod_events(self):
        return [ VODEVENT_START, VODEVENT_PAUSE, VODEVENT_RESUME ]

    #
    # VideoServer status/error reporting
    #
    def videoservthread_error_callback(self,e,url):
        """ Called by HTTP serving thread """
        wx.CallAfter(self.videoserver_error_guicallback,e,url)
        
    def videoserver_error_guicallback(self,e,url):
        print >>sys.stderr,time.asctime(),'-', "bg: Video server reported error",str(e)
        #    self.show_error(str(e))
        pass
        # ARNOTODO: schedule current Download for removal?

    def videoservthread_set_status_callback(self,status):
        """ Called by HTTP serving thread """
        wx.CallAfter(self.videoserver_set_status_guicallback,status)

    def videoserver_set_status_guicallback(self,status):
        print >>sys.stderr,time.asctime(),'-', "bg: Video server sets status callback",status
        # ARNOTODO: Report status to plugin

    #
    # reports vod stats collected periodically
    #
    def report_periodic_vod_stats(self,playing_dslist):
        #print >>sys.stderr, time.asctime(),'-', "VOD Stats"
        self.counter += 1
        if self.counter%self.interval == 0:
            event_reporter = get_reporter_instance()
            for ds in playing_dslist:
                dw = ds.get_download()
                b64_infohash = b64encode(dw.get_def().get_infohash())
                vod_stats = ds.get_vod_stats()
                #if vod_stats_has_key("prebuf"): event_reporter.add_event(b64_infohash, "prebufp:%d" % vod_stats['prebuf']) # prebuffering time that was needed
                if vod_stats.has_key("stall"): event_reporter.add_event(b64_infohash, "stall:%d" % vod_stats['stall']) # time the player stalled
                if vod_stats.has_key("late"): event_reporter.add_event(b64_infohash, "late:%d" % vod_stats['late']) # number of pieces arrived after they were due
                if vod_stats.has_key("dropped"): event_reporter.add_event(b64_infohash, "dropped:%d" % vod_stats['dropped']) # number of pieces lost
                if vod_stats.has_key("pos"): event_reporter.add_event(b64_infohash, "pos:%d" % vod_stats['pos']) # playback position


class BGInstanceConnection(InstanceConnection):
    
    def __init__(self,singsock,connhandler,readlinecallback,videoHTTPServer):
        InstanceConnection.__init__(self, singsock, connhandler, readlinecallback)
        
        self.bgapp = connhandler
        self.videoHTTPServer = videoHTTPServer
        self.urlpath = None
        self.cstreaminfo = {}
        self.shutteddown = False


    def set_streaminfo(self,streaminfo):
        """ Copy streaminfo contents and replace stream with a ControlledStream """
        """
        For each IC we create separate stream object and a unique path in the 
        HTTP server. This avoids nasty thread synchronization with the server
        when a new IC wants to play the same content. The Tribler Core stream
        does not allow multiple readers. This means we would have to stop
        the HTTP server from writing the stream to the old IC, before we
        can allow the new IC to read.
        
        We solved this as follows. The original Tribler Core stream is
        wrapped in a ControlledStream, one for each IC. When a new IC 
        wants to play we tell the old IC's ControlledStream to generate
        an EOF to the HTTP server, and tell the old IC to SHUTDOWN. We
        then either rewind the Tribler Core stream (VOD) or leave it (live)
        and tell the new IC to PLAY. The new ControlledStream will then
        be read by the HTTP server again.
        """
        self.cstreaminfo.update(streaminfo)
        stream = streaminfo['stream']
        cstream = ControlledStream(stream)
        self.cstreaminfo['stream'] = cstream

    def start_playback(self,infohash):
        """ Register cstream with HTTP server and tell IC to start reading """
        
        self.urlpath = URLPATH_CONTENT_PREFIX+'/'+infohash2urlpath(infohash)+'/'+str(random.random())

        self.videoHTTPServer.set_inputstream(self.cstreaminfo,self.urlpath)
        
        if DEBUG:
            print >> sys.stderr, time.asctime(),'-', "bg: Telling plugin to start playback of",self.urlpath
        
        self.write( 'PLAY '+self.get_video_url()+'\r\n' )

    def get_video_url(self):
        return 'http://127.0.0.1:'+str(self.videoHTTPServer.get_port())+self.urlpath

    def pause(self):
        self.write( 'PAUSE\r\n' )
        
    def resume(self):
        self.write( 'RESUME\r\n' )

    def info(self,infostr):
        self.write( 'INFO '+infostr+'\r\n' )        

    def searchurl(self,searchurl):
        
        print >>sys.stderr,time.asctime(),'-', "SENDING SEARCHURL 2 PLUGIN"
        self.write( 'SEARCHURL '+searchurl+'\r\n' )

    def shutdown(self):
        # SHUTDOWN Service
        if DEBUG:
            print >>sys.stderr,time.asctime(),'-', 'bg: Shutting down connection to Plugin'
        if not self.shutteddown:
            self.shutteddown = True
            # Cause HTTP server thread to receive EOF on inputstream
            if len(self.cstreaminfo) != 0:
                self.cstreaminfo['stream'].close()
                
                # Arno, 2009-12-11: Take this out of critical path on MainThread
                http_del_inputstream_lambda = lambda:self.videoHTTPServer.del_inputstream(self.urlpath)
                self.bgapp.tqueue.add_task(http_del_inputstream_lambda,0) 
            
            self.write( 'SHUTDOWN\r\n' )
            # Will cause BaseApp.connection_lost() to be called, where we'll
            # handle what to do about the Download that was started for this
            # IC.
            self.close() 


class ControlledStream:
    """ A file-like object that throws EOF when closed, without actually closing
    the underlying inputstream. See BGInstanceConnection.set_streaminfo() for
    an explanation on how this is used. 
    """
    def __init__(self,stream):
        self.stream = stream
        self.done = False # Event()
        
    def read(self,nbytes=None):
        if not self.done:
            return self.stream.read(nbytes)
        else:
            return '' # EOF

    def seek(self,pos,whence=os.SEEK_SET):
        self.stream.seek(pos,whence)
        
    def close(self):
        self.done = True
        # DO NOT close original stream


##############################################################
#
# Main Program Start Here
#
##############################################################
def run_bgapp(appname,params = None):
    if params is None:
        params = [""]
    
    if len(sys.argv) > 1:
        params = sys.argv[1:]
    
    # Create single instance semaphore
    # Arno: On Linux and wxPython-2.8.1.1 the SingleInstanceChecker appears
    # to mess up stderr, i.e., I get IOErrors when writing to it via print_exc()
    #
    if sys.platform != 'linux2':
        single_instance_checker = wx.SingleInstanceChecker(appname+"-"+ wx.GetUserId())
    else:
        single_instance_checker = LinuxSingleInstanceChecker(appname)

    #print "[StartUpDebug]---------------- 1", time()-start_time
    if not ALLOW_MULTIPLE and single_instance_checker.IsAnotherRunning():
        if params[0] != "":
            torrentfilename = params[0]
            i2ic = Instance2InstanceClient(I2I_LISTENPORT,'START',torrentfilename)
            time.sleep(1)
            return
        
    arg0 = sys.argv[0].lower()
    if arg0.endswith('.exe'):
        installdir = os.path.abspath(os.path.dirname(sys.argv[0]))
    else:
        installdir = os.getcwd()  

    # Launch first single instance
    app = BackgroundApp(0, appname, params, single_instance_checker, installdir, I2I_LISTENPORT, BG_LISTENPORT)
    app.MainLoop()
    
    print >>sys.stderr,time.asctime(),'-', "Sleeping seconds to let other threads finish"
    time.sleep(2)

    if not ALLOW_MULTIPLE:
        del single_instance_checker
        
    # Ultimate catchall for hanging popen2's and what not
    os._exit(0)


if __name__ == '__main__':
    run_bgapp("SwarmPlugin")

