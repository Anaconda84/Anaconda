import time 
# -*- coding: utf-8 -*-

from threading import Thread, Event

import tornado.ioloop
import tornado.web
import sys
import socket
import urlparse
import time
import datetime

from defs import *
from sockjs.tornado import SockJSConnection, SockJSRouter, proto
import asyncore, socket

class Ports():
    pass

class WsServer(Thread):
    def __init__(self,i2iport, ws_serverport):
        Thread.__init__(self)
        self.setName('WsServer')
	Ports.i2iport = i2iport
	Ports.ws_serverport = ws_serverport

    def run(self):
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
	Router = SockJSRouter(WsConnection, '/websocket')
        
        # Create application
        app = tornado.web.Application(Router.urls)
        app.listen(Ports.ws_serverport)

	print >>sys.stderr,time.asctime(),'-', "WsServer: Listening on 0.0.0.0:",Ports.ws_serverport
        print 'Listening on 0.0.0.0:',Ports.ws_serverport

        tornado.ioloop.IOLoop.instance().start()


# Out broadcast connection
class WsConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        print >>sys.stderr,time.asctime(),'-', 'WsServer: Client connected.'
	self.s = ''
        self.clients.add(self)

    def on_message(self, msg):
	print >>sys.stderr,time.asctime(),'-', 'WsServer: Received message: ',msg

        if msg.startswith( 'START' ):
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect(('127.0.0.1',Ports.i2iport))
            print >>sys.stderr,time.asctime(),'-', "WSServer: Connected from to SwarmVideo server."

            torrenturl = msg.partition( ' ' )[2].strip()
            if torrenturl is None:
                raise ValueError('bg: Unformatted START command')
	    print >>sys.stderr, time.asctime(),'-', "WsServer: Receive START command from WS to Video server - ",torrenturl,'   localhost:',Ports.i2iport
            self.cmd = 'START'
            self.param = torrenturl
            if self.cmd == 'START':
              msg = self.cmd+' '+self.param+'\r\n'
              self.s.send(msg)
        
              while True:
                data = self.s.recv(1024)
                print >>sys.stderr,time.asctime(),'-', "WSServer: Got BG command",data
	        self.send(data)
                if len(data) == 0:
                    print >>sys.stderr,time.asctime(),'-', "WSServer: BG closes IC"
                    break
                elif data.startswith("PLAY"):
		    print >>sys.stderr,time.asctime(),'-', "WSServer: BG send PLAY command."
                    break

        if msg.startswith( 'VERSION' ):
	    print >>sys.stderr, time.asctime(),'-', "WsServer: Receive VERSION command from WS to Swarm - localhost: ",Ports.i2iport
            self.send(VERSION)


    def on_close(self):
        print >>sys.stderr,time.asctime(),'-', "WsServer: Client disconnected."
        self.clients.remove(self)
	if self.s:
	    self.s.close()

if __name__ == "__main__":
    ws_serv = WsServer(62062,6878)
    ws_serv.start()
