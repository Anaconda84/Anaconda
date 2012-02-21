
==============================================================================
                             Next-Share: 
      The next generation Peer-to-Peer content delivery platform
    
                       http://www.p2p-next.org/
==============================================================================

LICENSE
-------
See LICENSE.txt and binary-LICENSE.txt.


PREREQUISITES
-------------

To run the Next-Share platform from source you will need to install the
following software packages. See www.p2p-next.org for binary distributions.

   Python >= 2.5
   M2Crypto >= 0.16
   wxPython >= 2.8 UNICODE (i.e., use --enable-unicode to build)
   APSW aka. python-apsw >= 3.6.x (Python wrappers for SQLite database)
   pywin32 >= Build 208 (Windows only, for e.g. UPnP support)
   vlc:
        For SwarmPlayer V1: VLC >= 1.0.5 with its Python bindings
	For SwarmPlugin: VLC >= 1.0.5 with P2P-Next extension
   simplejson >= 2.1.1 (if Python < 2.6)
   xulrunner-sdk >= 1.9.1.5 < 1.9.2 (optional, to run SwarmPlayer V2/SwarmTransport)
   7-Zip >= 4.6.5 (optional, to build SwarmPlayer V2/SwarmTransport)

Next-Share runs on Windows (XP,Vista), Mac OS X and Linux. On Linux, it is 
easiest to try to install these packages via a package manager such as
Synaptic (on Ubuntu). To run from the source on Windows it is easiest to use
binary distribution of all packages. On Mac, we advice to use MacPorts.

INSTALLING ON LINUX
-------------------
 
1. Unpack the main source code.

2. Change to the Next-Share directory.

2. The peer-to-peer video player SwarmPlayer that is part of Next-Share can now
   be started by running

     PYTHONPATH="$PYTHONPATH":Next-Share:.
     export PYTHONPATH
     python2.5 BaseLib/Player/swarmplayer.py
  

INSTALLING ON WINDOWS
---------------------

1. Unpack the main source code.

2. Open an CMD Prompt, change to the Next-Share directory.
   
3. The peer-to-peer video player SwarmPlayer that is part of Next-Share can now
   be started by running

     set PYTHONPATH=%PYTHONPATH%:Next-Share:.
     C:\Python25\python2.5.exe BaseLib\Player\swarmplayer.py
   
To build the SwarmPlugin, i.e., the browser plugin for P2P-based video
delivery and playback, or the SwarmPlayer V2 aka SwarmTransport, i.e., the
browser extension that adds P2P-based delivery as a new tribe:// transport
protocol, see the instructions in the D6.5.4 deliverable in the Publications
section of www.p2p-next.org.

Arno Bakker, 2010-08-16
