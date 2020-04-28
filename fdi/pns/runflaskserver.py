#!flask/bin/python
# -*- coding: utf-8 -*-

# This is to be able to test w/ or w/o installing the package
# https://docs.python-guide.org/writing/structure/
#from pycontext import fdi
from os.path import expanduser, expandvars
from fdi.pns.pnsconfig import pnsconfig as pc
from fdi.utils.options import opt
from fdi.pns.server import app
import logging.config
import logging
from fdi.pns import logdict  # import logdict
import fdi
import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')))

# print(sys.path)


# create logger
logging.config.dictConfig(logdict.logdict)
logger = logging.getLogger()
logger.debug('logging level %d' % (logger.getEffectiveLevel()))


# default configuration is provided. Copy pnsconfig.py to ~/local.py
env = expanduser(expandvars('$HOME'))
sys.path.insert(0, env)
try:
    from local import pnsconfig as pc
except Exception:
    pass

if __name__ == '__main__':

    logger.info(
        'Pipline Node Server starting. Make sure no other instance is running')
    node = pc['node']
    # Get username and password and host ip and port.
    ops = [
        {'long': 'help', 'char': 'h', 'default': False, 'description': 'print help'},
        {'long': 'verbose', 'char': 'v', 'default': False,
            'description': 'print info'},
        {'long': 'username=', 'char': 'u',
            'default': node['username'], 'description':'user name/ID'},
        {'long': 'password=', 'char': 'p',
            'default': node['password'], 'description':'password'},
        {'long': 'host=', 'char': 'i',
            'default': node['host'], 'description':'host IP/name'},
        {'long': 'port=', 'char': 'o',
            'default': node['port'], 'description':'port number'}
    ]
    out = opt(ops)
    verbose = out[1]['result']
    for j in range(2, 6):
        n = out[j]['long'].strip('=')
        node[n] = out[j]['result']

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    if node['username'] in ['', None] or node['password'] in ['', None]:
        logger.error(
            'Error. Specify non-empty username and password on commandline')
        exit(3)

    app.run(host=node['host'], port=node['port'],
            threaded=False, debug=verbose, processes=5)
