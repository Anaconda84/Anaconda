# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import os
import time
import sys
import string
from threading import Thread, Event
from BaseLib.Core.osutils import *

max_size=2**16
DEBUG = True

def bytestr2int(b):
    if b == "":
        return None
    else:
        return int(b)

class BtPorts():
    pass

class BtServer(Thread):
    def __init__(self, bt_port):
        Thread.__init__(self)
        self.setName('BtServer')
	BtPorts.PORT = bt_port

    def run(self):
	application = tornado.web.Application([ (r"/(.+)", MainHandler), ])
        application.listen(BtPorts.PORT)
        print >>sys.stderr,time.asctime(),'-', "Starting BtHTTPServer am port", BtPorts.PORT
	print 'Listening on 0.0.0.0:',BtPorts.PORT
        tornado.ioloop.IOLoop.instance().start()


class MainHandler(tornado.web.RequestHandler):
    CHUNK_SIZE = 512000         # 0.5 MB
    @tornado.web.asynchronous  # не закрывать сокет когда отработает эта функция (закрывать self.finish())
    def get(self, filename):
        if filename == 'favicon.ico':
           self.write('')
           return

	state_dir = get_appstate_dir()
	filename = os.path.join(state_dir, '.SwarmVideo', 'downloads', filename)
	print >>sys.stderr,time.asctime(),'-', "BtHTTPSErver: filename=", filename

	self._fd = open(filename, "rb")
	if self._fd:
            nbytes2send = None
            nbyteswritten= 0
            length = os.path.getsize(filename)
	    lastbyte = length-1
            firstbyte = 0
            if length is not None:
                lastbyte = length-1
            else:
                lastbyte = None
	    
            range = self.request.headers.get('range')
	    if length and range:
                bad = False
	        type, seek = string.split(range,'=')
	        if seek.find(",") != -1:
		    bad = True
	        else:
	            firstbytestr, lastbytestr = string.split(seek,'-')
	            firstbyte = bytestr2int(firstbytestr)
	            lastbyte = bytestr2int(lastbytestr)
                    if length is None:
                        # - No length (live) 
                        bad = True
                    elif firstbyte is None and lastbyte is None:
                        # - Invalid input
                        bad = True
                    elif firstbyte >= length:
                        bad = True
                    elif lastbyte >= length:
                        if firstbyte is None:
                            """ If the entity is shorter than the specified 
                                suffix-length, the entire entity-body is used.
                            """
                            lastbyte = length-1
                        else:
                            bad = True

                if bad:
                    # Send 416 - Requested Range not satisfiable and exit
		    self.set_status(416)
                    if length is None:
                        crheader = "bytes */*"
                    else:
                        crheader = "bytes */"+str(length)
                    self.set_header('Content-Range',crheader)
                    return

                if firstbyte is not None and lastbyte is None:
                    # "100-" : byte 100 and further
                    nbytes2send = length - firstbyte
                    lastbyte = length - 1
                elif firstbyte is None and lastbyte is not None:
                    # "-100" = last 100 bytes
                    nbytes2send = lastbyte
                    firstbyte = length - lastbyte
                    lastbyte = length - 1
                else:
                    nbytes2send = lastbyte+1 - firstbyte
            
                crheader = "bytes "+str(firstbyte)+"-"+str(lastbyte)+"/"+str(length)
	        self.set_status(206)
                self.set_header('Content-Range',crheader)
            else:
                # Normal GET request
                nbytes2send = length
                self.set_status(200)

            if DEBUG:
                print >>sys.stderr,time.asctime(),'-', "BtHTTPSErver: do_GET: final range",firstbyte,lastbyte,nbytes2send

            try:
                self._fd.seek(firstbyte)
            except:
                print_exc()

            self.set_header('Connection', 'Keep-Alive')
            self.set_header('Keep-Alive', 'timeout=15, max=100')
            content_type = self.request.headers.get('Content-Type')

	    if content_type: 
	        if content_type == 'video/x-webm':
	    	    self.set_header('Content-Type', 'video/webm')
	    	    print >>sys.stderr,time.asctime(),'-', "Replace Content-Type: ",content_type," to Content-Type: video/webm"
	        else:
                    self.set_header('Content-Type', content_type)
	    else:
                self.set_header('Content-Type', 'video/webm')

            self.set_header('Accept-Ranges', 'bytes')

            if length is not None:
                self.set_header('Content-Length', nbytes2send)
            else:
                self.set_header('Transfer-Encoding', 'chunked')

	    self.flush()  # отправляем заголовки

	    self.write_more()

    def write_more(self):
        data = self._fd.read(self.CHUNK_SIZE)
        if not data:  # если весь файл отправлен...
            self.finish()  # сбрасываем буфер и закрываем сокет
            self._fd.close()  # закрываем файл
            return
        self.write(data)
        # зацикливаемся - вызываем write_more только когда данные полностью уйдут клиенту
        self.flush(callback=self.write_more)

#application = tornado.web.Application([ (r"/(.+)", MainHandler), ])

if __name__ == "__main__":
    PORT = 8888
    application = tornado.web.Application([ (r"/(.+)", MainHandler), ])
    application.listen(PORT)
    print "Starting BtHTTPServer am port", PORT
    tornado.ioloop.IOLoop.instance().start()

