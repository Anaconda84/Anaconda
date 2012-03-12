# Written by Arno Bakker
# see LICENSE.txt for license information

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# This is the SwarmEngine.py for the SwarmPlugin which currently doesn't self 
# destruct when the browser quits.
#
# So there are two SwarmEngine.py's
#

from BaseLib.Plugin.BackgroundProcess import run_bgapp


I2I_LISTENPORT = 62062
BG_LISTENPORT = 8621
VIDEOHTTP_LISTENPORT = 6878
WS_SERVERPORT = 6868

if __name__ == '__main__':
    run_bgapp("SwarmVideo","0.0.8",I2I_LISTENPORT,BG_LISTENPORT,VIDEOHTTP_LISTENPORT,WS_SERVERPORT,killonidle=False)
