import time 
# Written by Arno Bakker 
# see LICENSE.txt for license information

from  threading import currentThread

from BaseLib.Core.API import *
from BaseLib.Video.VideoServer import VideoHTTPServer


def state_callback(d,ds):
    print >>sys.stderr,time.asctime(),'-', "main: Stats",dlstatus_strings[ds.get_status()],ds.get_progress(),"%",ds.get_error()

def vod_ready_callback(d,event,params):
    print >>sys.stderr,time.asctime(),'-', "main: VOD ready callback called",currentThread().getName(),"###########################################################",params["mimetype"]

    """
    f = open("video.avi","wb")
    while True:
        data = stream.read()
        print >>sys.stderr,time.asctime(),'-', "main: VOD ready callback: reading",type(data)
        print >>sys.stderr,time.asctime(),'-', "main: VOD ready callback: reading",len(data)
        if len(data) == 0:
            break
        f.write(data)
    f.close()
    stream.close()
    """

    videoserv = VideoHTTPServer.getInstance()
    videoserv.set_inputstream('video/mpeg',params["stream"],None)
    

if __name__ == "__main__":
    
    videoserv = VideoHTTPServer.getInstance() # create
    videoserv.background_serve()
    
    s = Session()
    
    if sys.platform == 'win32':
        tdef = TorrentDef.load('bla.torrent')
    else:
        tdef = TorrentDef.load('/tmp/bla.torrent')
    dcfg = DownloadStartupConfig.get_copy_of_default()
    #dcfg.set_saveas('/arno')
    dcfg = DownloadStartupConfig.get_copy_of_default()
    dcfg.set_video_start_callback(vod_ready_callback)
    #dcfg.set_selected_files('MATRIX-XP_engl_L.avi') # play this video
    #dcfg.set_selected_files('field-trip-west-siberia.avi')
    
    d = s.start_download(tdef,dcfg)
    d.set_state_callback(state_callback,1)
    #d.set_max_upload(100)
    
    time.sleep(10)
    
    """    
    d.stop()
    print "After stop"
    time.sleep(5)
    d.restart()
    """
    time.sleep(2500)
    
