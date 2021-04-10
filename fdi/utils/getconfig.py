# -*- coding: utf-8 -*-

from os.path import join, expanduser, expandvars
import functools
import sys

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('logging level %d' % (logger.getEffectiveLevel()))


@functools.lru_cache(5)
def getConfig(poolname=None, conf='pns'):
    """ Imports a dict named [conf]config defined in ~/.config/[conf]local.py
    """
    # default configuration is provided. Copy pnsconfig.py to ~/.config/pnslocal.py
    env = expanduser(expandvars('$HOME'))
    # apache wsgi will return '$HOME' with no expansion
    env = '/root' if env == '$HOME' else env
    confp = join(env, '.config')
    sys.path.insert(0, confp)
    # this is the stem part of filename and the name of the returned dict
    stem = conf+'config'
    logger.info('Reading from configuration file %s/%s.py' % (confp, stem))

    try:
        c = __import__(conf+'local', globals(), locals(), [stem], 0)
        logger.debug('Reading %s/%s.py done.' % (confp, stem))
        config = c.__dict__[stem]
        if poolname:
            urlof = c.__dict__['poolurl_of']
            if poolname in urlof:
                return urlof[poolname]
            else:
                return config['httphost'] + config['baseurl'] + '/' + poolname
        else:
            return config
    except ModuleNotFoundError as e:
        logger.warning(str(
            e) + '. Use default config in the package, such as fdi/pns/pnsconfig.py. Copy it to ~/.config/[package]local.py and make persistent customization there.')
        if poolname:
            return None
        else:
            return {}
