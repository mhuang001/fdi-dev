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
import copy
import sys
import importlib

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('logging level %d' % (logger.getEffectiveLevel()))


@functools.lru_cache(8)
def get_file_conf(conf):
    CU = conf.upper() + '_'
    envname = CU + 'CONF_DIR'
    epath = os.getenv(envname, '')
    if isdir(epath):
        confp = epath
    else:
        # environment variable <conf>_CONFIG_DIR is not set
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
    logger.debug('Configuration file %s/%s. absolute mod name %s' %
                 (confp, file_name, absolute_name))
    # if sys.path[0] != confp:
    #    sys.path.insert(0, confp)
    # print(sys.path)
    # for finder in sys.meta_path:
    #     spec = finder.find_spec(absolute_name, filep)
    #     print(spec)  # if spec is not None:

    try:
        # print('zz', spec)
        module = sys.modules.get(module_name, None)

        if module:
            # module has been imported. clear cache and re-read
            # importlib.invalidate_caches()
            module = importlib.reload(module)
            # c = getattr(nm, var_name)
            logger.debug(f'Module {module_name} to be reloaded.')
        spec = importlib.util.spec_from_file_location(absolute_name, filep)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        logger.debug('Loaded %s/%s.' % (confp, file_name))
        sys.modules[module_name] = module
        # the following suffers from non-updating loader
        # importlib.invalidate_caches()
        # module = importlib.import_module(module_name)
        # modul = __import__(module_name, globals(), locals(), [var_name], 0)

    except (ModuleNotFoundError, FileNotFoundError) as e:
        logger.warning(str(
            e) + '. Use default config in the package in fdi/pns/config.py. Copy it to ~/.config/%slocal.py and make persistent customization there.' % conf)
        return {}
    # return a copy so refs can be wiped out by deleting the dict variable.
    return copy.deepcopy(getattr(module, var_name))


def cget(name, conf='pns', builtin=None):
    osenviron = os.environ

    if builtin is None:
        builtin = builtin_conf
    config = copy.copy(builtin)
    config.update(get_file_conf(conf))

    if name is None:
        # name not given
        logger.debug(f'Dumping config {conf}.')
        res = {}
        for k, v in config.items():
            cn = '%s_%s' % (conf, k)
            env_var = cn.upper()
            res[k] = osenviron.get(env_var, v)
        return res
    if name not in config:
        raise KeyError(f'{name} is not found in config {conf}.')
    # chec env first
    cn = '%s_%s' % (conf, name)
    env_var = cn.upper()
    if env_var in osenviron:
        logger.debug(f'found value for {name} in Env.')
        return osenviron[env_var]
    var = config[name]
    logger.debug(f'Get  {name} : {var}.')
    return var


_url_mark = 'poolurl:'
_len_um = len(_url_mark)


def getConfig(name=None, conf='pns', builtin=builtin_conf, force=False):
    """Imports a dict named [conf]config.

    The contents of configuration are the key-value pairs of a
    `dict` variable :mod:`fdi.pns.config::<conf>config` by default.

    The configuration is updated by contents of a
    configuration file in the same format as `fdi/pns/config.py`.
    Name of the configuration file is in the form of `<conf>local.py`
    where `<conf>` is the value of the `conf` parameter of this
    function.

    The config file directory is the process owner's ``~/.config/``
    by default. It can be modified by the environment
    variable ``<uppercased conf>_CONF_DIR``, e.g. `PNS_CONF_DIR`..

    An exisiting configuration value can be overridden
    by that of an environment
    variable named `<uppercased <conf>_<name>`. For example configuration
    of `host` is overridden by the value of envirionment variable
    `PNS_HOST`.

    Parameters
    ----------
    name : str
        If found to be a key in ``poolurl_of`` in dict `<conf>config`,
        the value poolurl is returned, else construct a poolurl with
        ```scheme``` and ```node``` with ```/{name}``` at the end.
        Default ```None```, a mapping of all configured items 
        corrected with envirionment variables is returned..
    conf : str
         File `<conf>local.py`` defines configuration key-value
         pairs in `dict` named `<conf>config. Default 'pns', so the
         file is 'pnslocal.py', and the variable is `pnsconfig`.
    builtin : dict. To be updated by `<conf>local`. default is `fdi.pns.config`.
    force : bool
        reload from file instead of cache for all `conf`s cached.

    Returns
    -------
    obj
        configured value.

    """

    # default configuration is provided. Copy pns/config.py to ~/.config/pnslocal.py
    conflc = conf+'local'
    if force and conflc in sys.modules:
        logger.debug('Clearing config caches.')
        get_file_conf.cache_clear()
    if name:
        if name.startswith(_url_mark):
            # return poolurl if name startswith `poolurl`
            logger.debug('Getting poolurl by {name}.')
            return ''.join([cget('poolurl', conf=conf, builtin=builtin), '/', name[_len_um:]])

    return cget(name, conf=conf, builtin=builtin)


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
        auth = HTTPBasicAuth(pc['username'], pc['password'])
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

    logger = logging.getLogger()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("name1", metavar='NAME', nargs='?',
                        help="Value of the name parameter in the config file.")
    parser.add_argument("-n", "--name",
                        default=None, help="Value of the name parameter in the config file.")
    parser.add_argument("-c", "--conf",
                        default='pns', help="Configuration ID. default 'pns', so the file is 'pnslocal.py'.")
    parser.add_argument("-f", "--force",  action='store_true',
                        default=False, help="")
    parser.add_argument("-d", "--debug",  action='store_true',
                        default=False, help="")

    args, remainings = parser.parse_known_args(args=sys.argv[1:])

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    # logger.info
    print(logger.getEffectiveLevel(), f'args: {args}')
    name0 = args.name1 if args.name is None else args.name
    conf = getConfig(name0, conf=args.conf, force=args.force)
    if issubclass(conf.__class__, dict):
        # dictionart of all config items.
        print(json.dumps(conf, indent=4))
    else:
        print(conf)
    sys.exit(0)
