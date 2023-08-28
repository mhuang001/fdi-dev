#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" https://livecodestream.dev/post/python-flask-api-starter-kit-and-project-layout/ 
https://stackoverflow.com/questions/13751277/how-can-i-use-an-app-factory-in-flask-wsgi-servers-and-why-might-it-be-unsafe
"""

from fdi.httppool import create_app, LOGGING_NORMAL, LOGGING_DETAILED
# from fdi.httppool.route.httppool_server import init_httppool_server, httppool_api
from fdi.httppool.model.user import User

from fdi._version import __version__, __revision__
from fdi.utils import getconfig

import sys
import os
import argparse

# sys.path.insert(0, abspath(join(join(dirname(__file__), '..'), '..')))

# print(sys.path)


def setup_logging(lggng, logstream=None):
    lggng.basicConfig(stream=sys.stdout,
                      format='%(asctime)s.%(msecs)03d %(name)8s '
                      '%(process)d %(threadName)s %(levelname)3s '
                      '%(funcName)10s():%(lineno)3d- %(message)s',
                      datefmt="%Y-%m-%d %H:%M:%S")

    # lggng.getLogger("requests").setLevel(lggng.WARNING)
    # lggng.getLogger("filelock").setLevel(lggng.WARNING)
    logger = lggng.getLogger()
    if logstream:
        stream = open(logstream, 'a')
        handler = logging.StreamHandler(stream=stream)
        logger.addHandler(handler)
    return logger


if __name__ == '__main__':

    import logging
    logger = logging.getLogger()
    level = os.environ.get('PNS_DEBUG', LOGGING_NORMAL)
    logger.setLevel(level)
    # default configuration is provided. Copy config.py to ~/.config/pnslocal.py

    pc = getconfig.getConfig()

    # lev = pc['loggerlevel']

    # Get username and password and host ip and port.

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-u', '--username',
                        default=pc['self_username'], type=str, help='user name/ID. Prints hashed password if username is "hashed"')
    parser.add_argument('-p', '--password',
                        default=pc['self_password'], type=str, help='password')
    parser.add_argument('-i', '--host',
                        default=pc['self_host'], type=str, help='host IP/name')
    parser.add_argument('-o', '--port',
                        default=pc['self_port'], type=int, help='port number')
    parser.add_argument('-t', '--threads',
                        default=10, type=int, help='max number of threads. Default=100. 1 if debug is set')
    parser.add_argument('-s', '--server', default='httppool_server',
                        type=str, help='server type: pns or httppool_server')
    parser.add_argument('-P', '--preload', default=False,
                        action='store_true', help='Pre-load pools.')
    parser.add_argument('-w', '--wsgi', default=False,
                        action='store_true', help='run a WSGI server.')
    parser.add_argument('-d', '--debug', default=level, const=logging.DEBUG,
                        nargs='?', type=int,
                        help='run at the given logger level.')
    parser.add_argument('-l', '--logstream',
                        default=None, type=str, help='name of logfile')
    args = parser.parse_args()

    os.environ['PNS_SELF_USERNAME'] = args.username
    os.environ['PNS_SELF_PASSWORD'] = args.password
    os.environ['PNS_SELF_HOST'] = args.host
    os.environ['PNS_SELF_PORT'] = str(args.port)
    servertype = args.server
    wsgi = args.wsgi

    # create app only needs
    logger = setup_logging(logging, args.logstream)

    if args.username == 'hashed':
        print('Hashed password %s is\n' % args.password, User(
            'h', password=args.password).hashed_password)
        sys.exit(0)
    level = args.debug
    print(args)
    logger.setLevel(level)

    print('Check ' + pc['scheme'] + '://' + pc['self_host'] +
          ':' + str(pc['self_port']) + pc['baseurl'] +
          '/apidocs' + ' for API documents.')

    pc = getconfig.getConfig()
    lev = logger.getEffectiveLevel()
    print(
        'Server starting. Make sure no other instance is running. Initial logging level '+str(lev))

    if servertype == 'pns':
        print('======== %s ========' % servertype)
        # from fdi.pns.pns_server import app
        sys.exit(1)
    elif servertype == 'httppool_server':
        print('<<<<<< %s >>>>>' % servertype)
        app = create_app(pc, level=level,
                         logstream=args.logstream,
                         preload=args.preload
                         )
    else:
        logger.error('Unknown server %s' % servertype)
        sys.exit(-1)

    if wsgi:
        from waitress import serve
        serve(app, url_scheme='https',
              host=args.host, port=args.port,
              )
    else:
        # app may have changed debug, so do not use args.debug
        debug = app.debug
        logger.info(f"App.debug = {debug}")
        app.run(host=args.host, port=args.port,
                threaded=args.threads, processes=1,
                use_reloader=True, reloader_type='stat',
                debug=debug, passthrough_errors=debug,
                use_debugger=debug,
                )
