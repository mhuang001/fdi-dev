#! /usr/bin/python3.6

#import sys

import logging
# logging.basicConfig(stream=sys.stderr)
#logging.basicConfig( filename='/tmp/pns/pns.log')

#sys.path.insert(0, '/tmp/pns/')
from pns.logdict import logdict
import logging.config
# don't log to file. server will do the logging
del logdict["loggers"][""]["handlers"][1]
del logdict["root"]["handlers"][1]
logging.config.dictConfig(logdict)
logger = logging.getLogger()


from pns.server import app as application
application.secret_key = 'anything you wish'
