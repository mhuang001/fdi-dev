#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ 
https://stackoverflow.com/questions/13751277/how-can-i-use-an-app-factory-in-flask-wsgi-servers-and-why-might-it-be-unsafe
"""

from fdi.httppool import setup_logging, create_app
from fdi.httppool.route.pools import pools_api
#from fdi.httppool.route.httppool_server import init_httppool_server, httppool_api

from fdi._version import __version__
from fdi.utils import getconfig
from flasgger import Swagger
from flask import Flask

import sys

#sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

# print(sys.path)

if __name__ == '__main__':

    import logging
    logger = logging.getLogger()
    # default configuration is provided. Copy config.py to ~/.config/pnslocal.py

    pc = getconfig.getConfig()

    lv = pc['logginglevel']
    logging = setup_logging(lv if lv > logging.WARN else logging.WARN)
    logger = logging.getLogger()
    logger.setLevel(lv)
    logger.info(
        'Server starting. Make sure no other instance is running.'+str(lv))

    node = pc['node']
    # Get username and password and host ip and port.

    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument('-v', '--verbose', default=False,
                        action='store_true', help='Be verbose.')
    parser.add_argument('-u', '--username',
                        default=node['username'], type=str, help='user name/ID')
    parser.add_argument('-p', '--password',
                        default=node['password'], type=str, help='password')
    parser.add_argument('-i', '--host',
                        default=node['host'], type=str, help='host IP/name')
    parser.add_argument('-o', '--port',
                        default=node['port'], type=int, help='port number')
    parser.add_argument('-s', '--server', default='httppool_server',
                        type=str, help='server type: pns or httppool_server')
    parser.add_argument('-w', '--wsgi', default=False,
                        action='store_true', help='run a WSGI server.')
    args = parser.parse_args()

    verbose = args.verbose
    node['username'] = args.username
    node['password'] = args.password
    node['host'] = args.host
    node['port'] = args.port
    servertype = args.server
    wsgi = args.wsgi

    if verbose:
        logger.setLevel(logging.DEBUG)
        pc['logginglevel'] = logging.DEBUG
    logger.info('logging level %d' % (logger.getEffectiveLevel()))
    print('Check ' + pc['scheme'] + '://' + node['host'] +
          ':' + str(node['port']) + pc['api_base'] +
          '/apidocs' + ' for API documents.')

    if servertype == 'pns':
        print('======== %s ========' % servertype)
        #from fdi.pns.pns_server import app
        sys.exit(1)
    elif servertype == 'httppool_server':
        print('<<<<<< %s >>>>>' % servertype)
        #from fdi.pns.httppool_server import app
        app = create_app(pc)
    else:
        logger.error('Unknown server %s' % servertype)
        sys.exit(-1)

    if wsgi:
        from waitress import serve
        serve(app, url_scheme='https',
              host=node['host'], port=node['port'])
    else:
        app.run(host=node['host'], port=node['port'],
                threaded=True, debug=verbose, processes=1, use_reloader=True)
