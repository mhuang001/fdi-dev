#! /usr/bin/python3.6

from from fdi.pns.pns_server import app as application

import sys

import logging
import logging.config


# where user classes can be found
# sys.path.insert(0, '/{USER}/svom/engisim')
# sys.path.insert(0, '/{USER}/svom/share')
sys.path.insert(0, '/{USER}/svom/fdi')

# don't log to file. server will do the logging
logging.config.dictConfig(logdict)
logger = logging.getLogger()


application.secret_key = 'anything you wish'
