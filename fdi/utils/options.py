# -*- coding: utf-8 -*-
import getopt
import sys

import logging
logger = logging.getLogger(__name__)
# logger.debug('level %d' % (logger.getEffectiveLevel()))


def opt(ops, argv=None):
    """
    Example:
    ops = [
    {'long':'help', 'char':'h', 'default': false, 'description':'print help'},
    {'long':'verbose', 'char':'v', 'default': false, 'description':'print info'},
    {'long':'username=', 'char':'u', 'default': 'foo', 'description':'non-empty user name/ID'},
    {'long':'password=', 'char':'p', 'default': 'bar', 'description':'password'},
    {'long':'host=', 'char':'i', 'default': '0.0.0.0', 'description':'host IP/name'},
    {'long':'port=', 'char':'o', 'default': 5000, 'description':'port number'}
    ]

    Optionly use 'OPTSTART' in command line to start options an have ppreceeding ones ignored. Useful when application is invoked with other options, e.g. by pytest

    argv: if provided will be used in plsce of sys.argv.
    """

    if argv is None:
        argv = sys.argv
    #logger.debug('Input: %s' % ops)
    #stoken = 'OPTSTART'
    #sidx = argv.index(stoken) if stoken in argv else len(argv)

    # this will skip the executable's name at 0
    sidx = 0

    msg = 'Specify:\n'+''.join('%s (-%s or --%s) Default=%s\n\n' %
                               (i['description'], i['char'], i['long'], i['default']) for i in ops)
    # "hu:p:i:o:v"
    fmt = ''.join((i['char']+':' if i['long'].endswith('=')
                   else i['char'] for i in ops))
    try:
        opts, args = getopt.getopt(argv[sidx+1:], fmt, [
                                   i['long'] for i in ops])
    except getopt.GetoptError as err:
        # print help information and exit:
        # will print something like "option -a not recognized"
        logger.error(str(err) + 'Received: ' + str(argv))
        sys.exit(2)
    logger.debug('Command line options %s args %s' % (opts, args))

    for i in ops:
        switches = ('-'+i['char'], '--'+i['long'].replace('=', ''))
        i['result'] = i['default']
        for o, a in opts:
            if o in switches:
                if i['long'].endswith('='):
                    i['result'] = (i['default'].__class__)(a.lstrip().strip())
                else:
                    i['result'] = True
                    if i['long'] == 'help':
                        print(msg)
                        sys.exit(0)
    # logger.debug(str(ops))
    return ops
