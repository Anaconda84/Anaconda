# Written by Arno Bakker
# see LICENSE.txt for license information

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# This is the SwarmEngine.py for the SwarmPlugin which currently doesn't self 
# destruct when the browser quits.
#
# So there are two SwarmEngine.py's
#

from BaseLib.Plugin.BackgroundProcess import run_bgapp

from BaseLib.Core.osutils import *
from BaseLib.Core.log import *
from defs import *

I2I_LISTENPORT = 62062
BG_LISTENPORT = 8621
VIDEOHTTP_LISTENPORT = 6878
WS_SERVERPORT = 6868

# Run log rotate
logdir = get_appstate_dir()
logdir = os.path.join(logdir, '.SwarmVideo', 'Log')
if not os.path.isdir(logdir):
   os.makedirs(logdir)

if LOG_FILE:
   logfile = os.path.join(logdir, LOG_FILE)
   my_log = Log(logfile)
   my_log.rotate()

if __name__ == '__main__':
    run_bgapp("SwarmVideo","0.0.8",I2I_LISTENPORT,BG_LISTENPORT,VIDEOHTTP_LISTENPORT,WS_SERVERPORT,killonidle=False)
