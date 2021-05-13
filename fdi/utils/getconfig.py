# -*- coding: utf-8 -*-

from os.path import join, expanduser, expandvars
import functools
import sys

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('logging level %d' % (logger.getEffectiveLevel()))


class Instance():

    def get(self, name=None, conf='pns'):
        global CONFIG
        if name:
            try:
                return self._cached_conf
            except AttributeError:
                self._cached_conf = getConfig(name=name, conf=conf)
                return self._cached_conf
        else:
            try:
                return self._cached_poolurl
            except AttributeError:
                self._cached_poolurl = getConfig(name=name, conf=conf)
                return self._cached_poolurl


@functools.lru_cache(8)
def getConfig(name=None, conf='pns'):
    """ Imports a dict named [conf]config defined in ~/.config/[conf]local.py to update defaults in pns.pnsconfig.

    name: if given the return is poolurl in ``poolurl_of`` or a poolurl constructed from <conf>config.
    conf: configuration ID. default 'pns', so the file is 'pnsconfig.py'.
    """
    # default configuration is provided. Copy pnsconfig.py to ~/.config/pnslocal.py
    from fdi.pns.pnsconfig import pnsconfig as config
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
        config.update(c.__dict__[stem])
    except ModuleNotFoundError as e:
        logger.warning(str(
            e) + '. Use default config in the package, such as fdi/pns/pnsconfig.py. Copy it to ~/.config/[package]local.py and make persistent customization there.')

    if name:
        urlof = vars(c)['poolurl_of']
        if name in urlof:
            return urlof[name]
        else:
            return config['httphost'] + config['baseurl'] + '/' + name
    else:
        return config
