# -*- coding: utf-8 -*-

from threading import Thread, Event

import tornado.ioloop
import tornado.web
import sys
import socket
import urlparse
import time


from sockjs.tornado import SockJSConnection, SockJSRouter, proto

class Ports():
    pass

class WsServer(Thread):
    def __init__(self,i2iport, httpport, ws_serverport):
        Thread.__init__(self)
#        self.setDaemon(True)
        self.setName('WsServer')
	Ports.i2iport = i2iport
	Ports.httpport = httpport
	Ports.ws_serverport = ws_serverport

    def run(self):
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
	Router = SockJSRouter(WsConnection, '/websocket')
        
        # Create application
        app = tornado.web.Application(Router.urls)
        app.listen(Ports.ws_serverport)

	print >>sys.stderr,"WsServer: Listening on 0.0.0.0:",Ports.ws_serverport
        print 'Listening on 0.0.0.0:',Ports.ws_serverport

        tornado.ioloop.IOLoop.instance().start()


# Out broadcast connection
class WsConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        print >>sys.stderr,'WsServer: Client connected.'
        self.clients.add(self)

    def on_message(self, msg):
	print >>sys.stderr,'WsServer: Received message: ',msg
        if msg.startswith( 'START' ):
            torrenturl = msg.partition( ' ' )[2].strip()
            if torrenturl is None:
                raise ValueError('bg: Unformatted START command')
	    print >>sys.stderr, "WsServer: Connect from WsServer to Swarm - ",torrenturl,'   localhost:',Ports.i2iport,"\n"
            self.connect_to_swarm(Ports.i2iport,"START",torrenturl)
	       
#        self.send(msg)

    def on_close(self):
        print >>sys.stderr,'WsServer: Client disconnected.'
        self.clients.remove(self)

    def connect_to_swarm(self,port,cmd,param):
#	import ipdb; ipdb.set_trace()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1',port))
        msg = cmd+' '+param+'\r\n'
        s.send(msg)
        
        while True:
            data = s.recv(1024)
            print >>sys.stderr,"pe: Got BG command",data
	    self.send(data)
            if len(data) == 0:
                print >>sys.stderr,"pe: BG closes IC"
                return
            elif data.startswith("PLAY"):
                
                f = open("bla.bat","wb")
                f.write("\"\\Program Files\\GnuWin32\\bin\\wget.exe\" -S "+data[4:])
                f.close()
                break

        time.sleep(1000)
        return


if __name__ == "__main__":
    ws_serv = WsServer(62062,6878,6868)
    ws_serv.start()
