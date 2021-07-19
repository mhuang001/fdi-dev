# -*- coding: utf-8 -*-

from ..pns.config import pnsconfig as builtin_conf

from os.path import join, expanduser, expandvars, isdir
import functools
import sys
import importlib

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('logging level %d' % (logger.getEffectiveLevel()))


class Instance():

    def get(self, name=None, conf='pns'):
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


# @functools.lru_cache(8)
def getConfig(name=None, conf='pns'):
    """ Imports a dict named [conf]config.

    The contents of the config are defined in the ``.config/[conf]local.py`` file. The contenss are used to update defaults in ``fdi.pns.config``.
    Th config file directory can be modified by the environment variable ``CONF_DIR``, which if  not given or pointing to an existing directly is process owner's ``~/.config`` directory.

    name: if given the poolurl in ``poolurl_of`` is returned, else construct a poolurl from the contents in dict <conf>config.
    conf: configuration ID. default 'pns', so the file is 'pnslocal.py'.
    """
    # default configuration is provided. Copy pns/config.py to ~/.config/pnslocal.py
    config = builtin_conf

    epath = expandvars('$CONF_DIR')
    if isdir(epath):
        confp = epath
    else:
        # environment variable CONFIG_DIR is not set
        env = expanduser(expandvars('$HOME'))
        # apache wsgi will return '$HOME' with no expansion
        if env == '$HOME':
            env = '/root'
        confp = join(env, '.config')
    # this is the var_name part of filename and the name of the returned dict
    var_name = conf+'config'
    module_name = conf+'local'
    file_name = module_name + '.py'
    filep = join(confp, file_name)
    absolute_name = importlib.util.resolve_name(module_name, None)
    logger.debug('Reading from configuration file %s/%s. absolute mod name %s' %
                 (confp, file_name, absolute_name))
    # if sys.path[0] != confp:
    #    sys.path.insert(0, confp)
    # print(sys.path)
    # for finder in sys.meta_path:
    #     spec = finder.find_spec(absolute_name, filep)
    #     print(spec)  # if spec is not None:

    try:
        spec = importlib.util.spec_from_file_location(absolute_name, filep)
        #print('zz', spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[module_name] = module
        # the following suffers from non-updating loader
        # importlib.invalidate_caches()
        # module = importlib.import_module(module_name)
        # modul = __import__(module_name, globals(), locals(), [var_name], 0)
        config.update(getattr(module, var_name))
        logger.debug('Reading %s/%s done.' % (confp, file_name))
    except (ModuleNotFoundError, FileNotFoundError) as e:
        logger.warning(str(
            e) + '. Use default config in the package, such as fdi/pns/config.py. Copy it to ~/.config/[package]local.py and make persistent customization there.')

    if name:
        urlof = vars(c)['poolurl_of']
        if name in urlof:
            return urlof[name]
        else:
            return config['httphost'] + config['baseurl'] + '/' + name
    else:
        return config
