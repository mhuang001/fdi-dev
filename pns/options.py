# -*- coding: utf-8 -*-
import getopt
import sys

from .logdict import logdict
import logging
logger = logging.getLogger(__name__)
#logger.debug('level %d' % (logger.getEffectiveLevel()))


def opt(node):
    """Get username and password and host ip and port
    """

    logger.debug('username %s password %s host=%s port=%d' %
                 (node['username'], node['password'],
                  node['host'], node['port']))
    msg = 'Specify non-empty username (-u or --username=) and password (-p or --password= ) host IP (-i or --ip=) and port (-o or --port=) on commandline.'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:p:i:o:v",
                                   [
                                       "help",
                                       "username=",
                                       "password=",
                                       "ip=",
                                       "port=",
                                       'verbose'
        ])
    except getopt.GetoptError as err:
        # print help information and exit:
        # will print something like "option -a not recognized"
        logger.error(str(err))
        logger.info(msg)
        sys.exit(2)
    logger.debug('Command line options %s args %s' % (opts, args))
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", '--help'):
            print(msg)
            sys.exit(0)
        elif o in ("-u", '--username'):
            node['username'] = a
        elif o in ('-p', '--password'):
            node['password'] = a
        elif o in ("-i", '--ip'):
            node['host'] = a
        elif o in ('-o', '--port'):
            node['port'] = int(a)
        else:
            logger.error("unhandled option")
            print(msg)
            sys.exit(1)
    logger.debug('username %s password %s host=%s port=%d' %
                 (node['username'], node['password'],
                  node['host'], node['port']))
    return node, verbose
