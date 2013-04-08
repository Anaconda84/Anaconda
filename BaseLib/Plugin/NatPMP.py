import time 
# -*- coding: utf-8 -*-

import sys
from threading import Thread, Event
try:
    import natpmp as NATPMP
except ImportError:
    import NATPMP

DEBUG = True

class NatPMP(Thread):
    def __init__(self, port1, port2, periodic):
        Thread.__init__(self)
        self.setName('NatPMP')
	self.port1 = int(port1)
	self.port2 = int(port2)
	self.periodic = int(periodic)

    def run(self):
	print >>sys.stderr,time.asctime(),'-', "NatPMP: Running NatPMP daemon."
        public_port1 = self.port1
        private_port1 = self.port1
        public_port2 = self.port2
        private_port2 = self.port2
        protocol = NATPMP.NATPMP_PROTOCOL_TCP
        lifetime = int(3600)
        gateway = NATPMP.get_gateway_addr()
	while True:
	  resp1 = NATPMP.map_port(protocol, public_port1, private_port1, lifetime, gateway_ip=gateway, use_exception=False)
	  resp2 = NATPMP.map_port(protocol, public_port2, private_port2, lifetime, gateway_ip=gateway, use_exception=False)
	  if DEBUG:
	     print >>sys.stderr,time.asctime(),'-', "NatPMP: ", resp1
	     print >>sys.stderr,time.asctime(),'-', "NatPMP: ", resp2
          time.sleep(self.periodic)

if __name__ == "__main__":
    nat_pmp = NatPMP(8621, 8888, 10)
    nat_pmp.start()
