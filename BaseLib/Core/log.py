import time 
import glob
import logging
import logging.handlers
import time
import sys

class Log():
    """
    Class for logging and rotate logging.
    """
    def __init__(self, logfile):
        """ Internal constructor
        @param logfile - log file full name
        @param mode - debug, info, warning,  error, critical 
        """
        self.logfile = logfile
	sys.stderr = file( self.logfile, "a+" )
        self.my_logger = logging.getLogger('MyLogger')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#	formatter = logging.Formatter('%(asctime)s %(levelname)s in \'%(module)s\' at line %(lineno)d: %(message)s')
        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(
              self.logfile, backupCount=1)
	handler.setFormatter(formatter)
        self.my_logger.addHandler(handler)

    def setLevel(self, level):
        """  Set output level. """
        if level == 'debug':
            self.my_logger.setLevel(logging.DEBUG)
        if level == 'info':
            self.my_logger.setLevel(logging.INFO)
        if level == 'warning':
           self.my_logger.setLevel(logging.WARNING)
        if level == 'error':
            self.my_logger.setLevel(logging.ERROR)
        if level == 'critical':
            self.my_logger.setLevel(logging.CRITICAL)

    def rotate(self):
        """  Rotate logs. """
        # Add timestamp
        print >> sys.stderr,time.asctime(),'-', '\n---------\nLog closed on %s.\n---------\n' % time.asctime()
	sys.stderr.flush()
	sys.stderr.close()
        # Roll over on application start
        self.my_logger.handlers[0].doRollover()
	sys.stderr = file( self.logfile, "a+" )
        # Add timestamp
        print >> sys.stderr,time.asctime(),'-', '\n---------\nLog started on %s.\n---------\n' % time.asctime()
	sys.stderr.flush()

    def message(self, level, msg, *args):
        """ Output message
        @param level - log level ( debug, info, warning,  error, critical )
        @param msg - output message 
        """
        for arg in args:
	    msg = msg +' '+str(arg)
        if level == 'debug':
            self.my_logger.debug(msg)
        if level == 'info':
            self.my_logger.info(msg)
        if level == 'warning':
           self.my_logger.warning(msg)
        if level == 'error':
            self.my_logger.error(msg)
        if level == 'critical':
            self.my_logger.critical(msg)



if __name__ == '__main__':
    my_log = Log('logging_rotatingfile_example.out')
    print >> sys.stderr,time.asctime(),'-', 'Durak!!!!!!!!!!!';
    my_log.rotate()
    print >> sys.stderr,time.asctime(),'-', 'Idiot!!!!!!!!!!!';
