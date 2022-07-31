#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fdi.pns.config import pnsconfig as builtin_conf
from requests.auth import HTTPBasicAuth
from os.path import join, expanduser, expandvars, isdir
import functools
import socket
import getpass
import json
import os
import argparse
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


CONFIG = None

# @functools.lru_cache(8)


def getConfig(name=None, conf='pns', builtin=builtin_conf, force=False):
    """Imports a dict named [conf]config.

    The contents of the config are defined in the ``.config/[conf]local.py`` file. The contenss are used to update defaults in ``fdi.pns.config``.
    The config file directory can be modified by the environment
    variable ``CONF_DIR``, which, if not given or pointing to an
    existing directory, is the process owner's ``~/.config``
    directory.

    Parameters
    ----------
    name : str
        If found to be a key in ``poolurl_of`` in dict <conf>config, the value poolurl is returned, else construct a poolurl with ```scheme``` and ```node``` with ```/{name}``` at the end. Default ```None```.
    conf : str
        configuration ID. default 'pns', so the file is 'pnslocal.py'.
    builtin : dict
    force : bool
        reload from file instead of cache.

    Returns
    -------
    obj
        configured value.

    """

    "eturn    ------    "
    # default configuration is provided. Copy pns/config.py to ~/.config/pnslocal.py

    global CONFIG

    if CONFIG and conf in CONFIG and not force:
        config = CONFIG[conf]
    else:

        config = builtin

        epath = expandvars('$CONF_DIR_' + conf.upper())
        if isdir(epath):
            confp = epath
        else:
            # environment variable CONFIG_DIR_<conf> is not set
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
        if CONFIG:
            CONFIG[conf] = config
        else:
            CONFIG = {conf: config}

    urlof = config['lookup']
    if name is not None:
        #urlof = vars(module)['poolurl_of']
        if name in urlof:
            return urlof[name]
        else:
            return ''.join([config['scheme'],
                            '://',
                            config['node']['host'],
                            ':',
                            str(config['node']['port']),
                            config['baseurl'],
                            '/',
                            name])
    else:
        # name not given
        return config


def make_pool(pool, conf='pns', auth=None, wipe=False):
    """ Return a ProductStorage with given pool name or poolURL.

    ;name: PoolURL, or pool name (has no "://"), in which case a pool URL is made based on the result of `getConfig(name=pool, conf=conf)`. Default is ''.
    :auth: if is None will be set to `HTTPBasicAuth` using the `config`.
    :conf: passed to `getconfig` to determine which configuration. Default ```pns```.
    :wipe: whether to delete everything in the pool first.

    Exception
    ConnectionError
    """

    pc = getConfig()
    if '://' in pool:
        poolurl = pool
    else:
        poolurl = getConfig(pool)

    if auth is None:
        auth = HTTPBasicAuth(pc['node']['username'], pc['node']['password'])
    logger.info("PoolURL: " + poolurl)

    # create a product store
    from ..pal.productstorage import ProductStorage
    pstore = ProductStorage(poolurl=poolurl, auth=auth)
    if wipe:
        logger.info('Wiping %s...' % str(pstore))
        pstore.wipePool()
        # pstore.getPool(pstore.getPools()[0]).removeAll()
    # see what is in it.
    # print(pstore)

    return pstore


def get_mqtt_config():
    """ Get configured MQTT info from project configuration file.

    Overrideable by uppercased environment variables.
    Note that there is a '_' in the envirionment variable name, e.g. ```MQ_HOST``` for ```pc['mqhost']```
    ref `fdi.utils.getConfig` and your local ```~/.config/pnslocal.py```
    """
    pc = getConfig()
    # default mqtt settings
    mqttargs = dict(
        mqhost=os.getenv('MQ_HOST', pc['mqhost']),
        mqport=os.getenv('MQ_PORT', pc['mqport']),
        mquser=os.getenv('MQ_USER', pc['mquser']),
        mqpass=os.getenv('MQ_PASS', pc['mqpass']),
        qos=1,
        clean_session=True,
        client_id=socket.gethostname()+'_' + getpass.getuser()+'_' + str(os.getpid())
    )
    return mqttargs


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument("pname", nargs='?',
                       default=None, help="Same as, and mutually exclusive with '-n'.")
    group.add_argument("-n", "--name",
                       default=None, help="parameter name in the config file.")
    parser.add_argument("-u", "--url_of", type=str,
                        default=None, help="If found to be a key in ``poolurl_of`` in dict <conf>config, the value poolurl is returned, else construct a poolurl with ```scheme``` and ```node``` with ```/{name}``` at the end. Default ```None```.")
    parser.add_argument("-c", "--conf",
                        default='pns', help="Configuration ID. default 'pns', so the file is 'pnslocal.py'.")

    parser.add_argument("-f", "--force",  action='store_true',
                        default=False, help="")

    args, remainings = parser.parse_known_args(args=sys.argv[1:])

    if args.name is not None or args.pname is not None:
        conf = getConfig(conf=args.conf, force=args.force)
        p = args.name if args.name is not None else args.pname
        if p in conf:
            print(conf[p])
            sys.exit(0)
        else:
            print('')
            sys.exit(-1)
    conf = getConfig(name=args.url_of, conf=args.conf, force=args.force)
    if issubclass(conf.__class__, dict):
        print(json.dumps(conf, indent=4))
    else:
        print(conf)
    sys.exit(0)
