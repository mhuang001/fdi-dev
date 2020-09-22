#!flask/bin/python
# -*- coding: utf-8 -*-

from fdi.pns.pnsconfig import pnsconfig as pc
from fdi.utils.options import opt
from fdi.pns.server import app
from fdi.utils.getconfig import getConfig

import pdb

#sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

# print(sys.path)


def setuplogging():
    import logging.config
    import logging
    from fdi.pns import logdict  # import logdict
    # create logger
    logging.config.dictConfig(logdict.logdict)
    return logging


logging = setuplogging()
logger = logging.getLogger()


if __name__ == '__main__':

    logger.info(
        'Pipline Node Server starting. Make sure no other instance is running')
    # default configuration is provided. Copy pnsconfig.py to ~/.config/pnslocal.py
    pc.update(getConfig())
    logger.setLevel(pc['logginglevel'])

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
    print('Check http://' + node['host'] + ':' + str(node['port']) +
          pc['baseurl'] + '/ for API list')
    app.run(host=node['host'], port=node['port'],
            threaded=False, debug=verbose, processes=5)
