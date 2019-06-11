#! /usr/bin/python3.6

import sys

import logging
# logging.basicConfig(stream=sys.stderr)
#logging.basicConfig( filename='/tmp/pns/pns.log')

sys.path.insert(0, '/tmp/pns/')
from logdict import logdict
import logging.config
logging.config.dictConfig(logdict)
logger = logging.getLogger()


from pns import app as application
application.secret_key = 'anything you wish'
