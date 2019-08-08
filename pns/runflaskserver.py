#!flask/bin/python
# -*- coding: utf-8 -*-

from pns import module  # absolute import
from pns import logdict  # import logdict
import logging
import logging.config
# create logger
logging.config.dictConfig(logdict.logdict)
logger = logging.getLogger()
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

from pns.server import app
from pns.options import opt

from pns.pnsconfig import pnsconfig as pc

# default configuration is provided. Copy pnsconfig.py to ~/local.py
import sys
from os.path import expanduser, expandvars
env = expanduser(expandvars('$HOME'))
sys.path.insert(0, env)
try:
    from local import pnsconfig as pc
except Exception:
    pass

if __name__ == '__main__':

    logger.info(
        'Pipline Node Server starting. Make sure no other instance is running')
    node, verbose = opt(pc['node'])
    pc['node'].update(node)
    
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    if node['username'] in ['', None] or node['password'] in ['', None]:
        logger.error(
            'Error. Specify non-empty username and password on commandline')
        exit(3)

    app.run(host=node['host'], port=node['port'], debug=verbose)
