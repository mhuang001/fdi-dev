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
import argparse

#sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

# print(sys.path)

if __name__ == '__main__':

    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # default configuration is provided. Copy config.py to ~/.config/pnslocal.py

    pc = getconfig.getConfig()

    #lev = pc['loggerlevel']
    #logging = setup_logging(lev if lev < logging.WARN else logging.WARN)

    # Get username and password and host ip and port.

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-v', '--verbose', default=False,
                        action='store_true', help='Be verbose.')
    parser.add_argument('-u', '--username',
                        default=pc['self_username'], type=str, help='user name/ID')
    parser.add_argument('-p', '--password',
                        default=pc['self_password'], type=str, help='password')
    parser.add_argument('-i', '--host',
                        default=pc['self_host'], type=str, help='host IP/name')
    parser.add_argument('-o', '--port',
                        default=pc['self_port'], type=int, help='port number')
    parser.add_argument('-s', '--server', default='httppool_server',
                        type=str, help='server type: pns or httppool_server')
    parser.add_argument('-w', '--wsgi', default=False,
                        action='store_true', help='run a WSGI server.')
    parser.add_argument('-d', '--debug', default=False,
                        action='store_true', help='run in debug mode.')
    args = parser.parse_args()

    verbose = args.verbose
    pc['self_username'] = args.username
    pc['self_password'] = args.password
    pc['self_host'] = args.host
    pc['self_port'] = args.port
    servertype = args.server
    wsgi = args.wsgi

    if verbose:
        logger.setLevel(logging.DEBUG)
        pc['loggerlevel'] = logging.DEBUG
    print('Check ' + pc['scheme'] + '://' + pc['self_host'] +
          ':' + str(pc['self_port']) + pc['api_base'] +
          '/apidocs' + ' for API documents.')

    lev = logger.getEffectiveLevel()
    logger.info(
        'Server starting. Make sure no other instance is running. Initial logging level '+str(lev))

    if servertype == 'pns':
        print('======== %s ========' % servertype)
        #from fdi.pns.pns_server import app
        sys.exit(1)
    elif servertype == 'httppool_server':
        print('<<<<<< %s >>>>>' % servertype)
        app = create_app(pc)  # , level)
    else:
        logger.error('Unknown server %s' % servertype)
        sys.exit(-1)

    if wsgi:
        from waitress import serve
        serve(app, url_scheme='https',
              host=pc['self_host'], port=pc['self_port'])
    else:
        app.run(host=pc['self_host'], port=pc['self_port'],
                threaded=True, debug=args.debug, processes=1, use_reloader=True, passthrough_errors=args.debug)
