# -*- coding: utf-8 -*-

from os.path import join, expanduser, expandvars
from collections import OrderedDict
import sys
import pdb

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def getConfig(conf='pns'):
    """ Imports a dict named [conf]config defined in ~/.config/[conf]local.py
    """
    # default configuration is provided. Copy pnsconfig.py to ~/.config/pnslocal.py
    env = expanduser(expandvars('$HOME'))
    # apache wsgi will return '$HOME' with no expansion
    env = '/root' if env == '$HOME' else env
    confp = join(env, '.config')
    sys.path.insert(0, confp)
    try:
        logger.debug('Reading from configuration file in dir '+confp)
        c = __import__(conf+'local', globals(), locals(),
                       [conf+'config'], 0)
        return c.__dict__[conf+'config']
    except ModuleNotFoundError as e:
        logger.warning(str(
            e) + '. Use default config in the package, such as fdi/pns/pnsconfig.py. Copy it to ~/.config/[package]local.py and make persistent customization there.')
        return {}
