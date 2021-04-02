#! /usr/bin/python3.6

import sys
import logging
#import logging.config
# don't log to file. server will do the logging
# logging.config.dictConfig(logdict)
logger = logging.getLogger()

try:
    from fdi.pns.httppool_server import app as application
except Exception as e:
    logger.error(e)

logger.info(sys.path)


# where user classes can be found
sys.path.insert(0, os.path.dirname(__file__))


application.secret_key = 'anything you wish'
