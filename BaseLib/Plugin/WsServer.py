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
	    print >>sys.stderr, "WsServer: Connecting from WsServer to Swarm - ",torrenturl,'   localhost:',Ports.i2iport,"\n"
	    self.ws_serv_to_swarm = WsServerToSwarm(self,Ports.i2iport,"START",torrenturl)   
	    self.ws_serv_to_swarm.start()

    def on_close(self):
        print >>sys.stderr,'WsServer: Client disconnected.'
	self.disconnect_to_swarm()
        self.clients.remove(self)

    def disconnect_to_swarm(self):
	if self.ws_serv_to_swarm.s is not None:
	    self.ws_serv_to_swarm.s.close()
	    print >>sys.stderr,"WSServer: Disconnected from WS to Swarm."
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
        print >>sys.stderr,"WSServer: Connected from WS to Swarm."
        msg = self.cmd+' '+self.param+'\r\n'
        self.s.send(msg)
        
	self.stop_flag = False
        while not self.stop_flag:
            data = self.s.recv(1024)
            print >>sys.stderr,"WSServer: Got BG command",data
	    self.wsconnection.send(data)
            if len(data) == 0:
                print >>sys.stderr,"WSServer: BG closes IC"
                return
            elif data.startswith("PLAY"):
                self.stop_flag = True
                break
        print >>sys.stderr,"WSServer: Shutdown process WsServerToSwarm."

if __name__ == "__main__":
    ws_serv = WsServer(62062,6878,6868)
    ws_serv.start()
