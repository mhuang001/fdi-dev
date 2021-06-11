#!flask/bin/python
# -*- coding: utf-8 -*-

from fdi.utils.options import opt
from fdi.utils import getconfig

import logging
import sys

#sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

# print(sys.path)


def setuplogging(level=logging.WARN):
    global logging
    # create logger
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s-%(levelname)4s'
                        '-[%(filename)6s:%(lineno)3s'
                        '-%(funcName)10s()] - %(message)s',
                        datefmt="%Y%m%d %H:%M:%S")
    logging.getLogger("requests").setLevel(level)
    logging.getLogger("filelock").setLevel(level)
    if sys.version_info[0] > 2:
        logging.getLogger("urllib3").setLevel(level)
    return logging


logger = logging.getLogger(__name__)


if __name__ == '__main__':

    logger = logging.getLogger()
    # default configuration is provided. Copy config.py to ~/.config/pnslocal.py
    pc = getconfig.getConfig()

    lv = pc['logginglevel']
    logger.setLevel(lv)
    setuplogging(lv if lv > logging.WARN else logging.WARN)
    logger.info(
        'Server starting. Make sure no other instance is running.'+str(lv))

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
            'default': node['port'], 'description':'port number'},
        {'long': 'server=', 'char': 's',
            'default': 'pns', 'description': 'server type: pns or httppool_server'},
        {'long': 'wsgi', 'char': 'w', 'default': False,
            'description': 'run a WSGI server.'},
    ]

    out = opt(ops)
    verbose = out[1]['result']
    for j in range(2, 6):
        n = out[j]['long'].strip('=')
        node[n] = out[j]['result']
    servertype = out[6]['result']
    wsgi = out[7]['result']

    if verbose:
        logger.setLevel(logging.DEBUG)

    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    if node['username'] in ['', None] or node['password'] in ['', None]:
        logger.error(
            'Error. Specify non-empty username and password on commandline')
        exit(3)
    print('Check http://' + node['host'] + ':' + str(node['port']) +
          pc['baseurl'] + '/ for API list')

    if servertype == 'pns':
        print('======== %s ========' % servertype)
        from fdi.pns.pns_server import app
    elif servertype == 'httppool_server':
        print('<<<<<< %s >>>>>' % servertype)
        from fdi.pns.httppool_server import app
    else:
        logger.error('Unknown server %s' % servertype)
        sys.exit(-1)

    if wsgi:
        from waitress import serve
        serve(app, url_scheme='https', host=node['host'], port=node['port'])
    else:
        app.run(host=node['host'], port=node['port'],
                threaded=True, debug=verbose, processes=1, use_reloader=True)
