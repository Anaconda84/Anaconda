# Written by Arno Bakker
# see LICENSE.txt for license information
import os

STOP_FILE = os.path.join(os.getenv("APPDATA"), 'SwarmVideo', 'goodbay')

URLPATH_CONTENT_PREFIX = '/content'
URLPATH_TORRENT_POSTFIX = '.tstream'
URLPATH_NSMETA_POSTFIX = '.xml'
URLPATH_THUMBNAIL_POSTFIX = '/thumbnail'
URLPATH_HITS_PREFIX = '/hits'
URLPATH_SEARCH_PREFIX = '/search'
URLPATH_WEBIF_PREFIX = '/webUI'

# After this time the ATOM feed URL and all links are no longer valid.
HITS_TIMEOUT = 1800.0
 
UPDATE_SITES = 'http://localhost'
UPDATE_PATH = 'distr'

VERSION = '0.9'

# output log file filename or None(to screen)
LOG_FILE = None
#LOG_FILE = 'SwarmPlugin.log'
