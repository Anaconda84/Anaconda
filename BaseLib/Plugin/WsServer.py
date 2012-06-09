import time 
# -*- coding: utf-8 -*-

from threading import Thread, Event

import tornado.ioloop
import tornado.web
import sys
import socket
import urlparse
import time

from defs import *
from sockjs.tornado import SockJSConnection, SockJSRouter, proto

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
        self.clients.add(self)

    def on_message(self, msg):
	print >>sys.stderr,time.asctime(),'-', 'WsServer: Received message: ',msg
        if msg.startswith( 'START' ):
            torrenturl = msg.partition( ' ' )[2].strip()
            if torrenturl is None:
                raise ValueError('bg: Unformatted START command')
	    print >>sys.stderr, time.asctime(),'-', "WsServer: Receive START command from WS to Swarm - ",torrenturl,'   localhost:',Ports.i2iport,"\n"
	    self.ws_serv_to_swarm = WsServerToSwarm(self,Ports.i2iport,"START",torrenturl)   
	    self.ws_serv_to_swarm.start()
        if msg.startswith( 'VERSION' ):
	    print >>sys.stderr, time.asctime(),'-', "WsServer: Receive VERSION command from WS to Swarm - localhost: ",Ports.i2iport,"\n"
	    self.ws_serv_to_swarm = WsServerToSwarm(self,Ports.i2iport,"VERSION",'')   
	    self.ws_serv_to_swarm.start()

    def on_close(self):
        print >>sys.stderr,time.asctime(),'-', 'WsServer: Client disconnected.'
	self.disconnect_to_swarm()
        self.clients.remove(self)

    def disconnect_to_swarm(self):
	if self.ws_serv_to_swarm.s is not None:
	    self.ws_serv_to_swarm.s.close()
	    print >>sys.stderr,time.asctime(),'-', "WSServer: Disconnected from WS to Swarm."
	self.ws_serv_to_swarm.stop_flag = True

class WsServerToSwarm(Thread):
    def __init__(self,wsconnection,port,cmd,param):
        Thread.__init__(self)
        self.setName('WsServerToSwarm')
	self.wsconnection = wsconnection
	self.port = port
	self.cmd = cmd
	self.param = param

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('127.0.0.1',self.port))
        print >>sys.stderr,time.asctime(),'-', "WSServer: Connected from WS to Swarm."
        if self.cmd == 'START':
            msg = self.cmd+' '+self.param+'\r\n'
            self.s.send(msg)
        
	    self.stop_flag = False
            while not self.stop_flag:
                data = self.s.recv(1024)
                print >>sys.stderr,time.asctime(),'-', "WSServer: Got BG command",data
	        self.wsconnection.send(data)
                if len(data) == 0:
                    print >>sys.stderr,time.asctime(),'-', "WSServer: BG closes IC"
                    return
                elif data.startswith("PLAY"):
                   self.stop_flag = True
                   break
        if self.cmd == 'VERSION':
            self.wsconnection.send(VERSION)

        print >>sys.stderr,time.asctime(),'-', "WSServer: Shutdown process WsServerToSwarm."

if __name__ == "__main__":
    ws_serv = WsServer(62062,6878,6868)
    ws_serv.start()
