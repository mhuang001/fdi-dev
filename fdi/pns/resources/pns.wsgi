#! /usr/bin/python3.6

import sys

import logging
import logging.config
# logging.basicConfig(stream=sys.stderr)

# where user classes can be found
# sys.path.insert(0, '/root/svom/engisim')
# sys.path.insert(0, '/root/svom/share')
sys.path.insert(0, '/root/svom/fdi')
from fdi.pns.logdict import logdict

# don't log to file. server will do the logging
#del logdict["loggers"][""]["handlers"][1]
#del logdict["root"]["handlers"][1]
logging.config.dictConfig(logdict)
logger = logging.getLogger()


from fdi.pns.server import app as application
application.secret_key = 'anything you wish'
