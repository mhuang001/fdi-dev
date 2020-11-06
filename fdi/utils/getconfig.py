# -*- coding: utf-8 -*-

from os.path import join, expanduser, expandvars
import functools
import sys

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('logging level %d' % (logger.getEffectiveLevel()))


@functools.lru_cache(5)
def getConfig(conf='pns'):
    """ Imports a dict named [conf]config defined in ~/.config/[conf]local.py
    """
    # default configuration is provided. Copy pnsconfig.py to ~/.config/pnslocal.py
    env = expanduser(expandvars('$HOME'))
    # apache wsgi will return '$HOME' with no expansion
    env = '/root' if env == '$HOME' else env
    confp = join(env, '.config')
    sys.path.insert(0, confp)
    # logger.debug('Reading from configuration file in dir '+confp)

    try:
        c = __import__(conf+'local', globals(), locals(),
                       [conf+'config'], 0)
        logger.debug('Reading %s/%slocal.py done.' % (confp, conf))
        return c.__dict__[conf+'config']
    except ModuleNotFoundError as e:
        logger.warning(str(
            e) + '. Use default config in the package, such as fdi/pns/pnsconfig.py. Copy it to ~/.config/[package]local.py and make persistent customization there.')
        return {}
