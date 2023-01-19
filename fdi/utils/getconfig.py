#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..dataset.namespace import NameSpace_meta, Load_Failed
from ..dataset.readonlydict import ReadOnlyDict
from ..pns.config import pnsconfig as builtin_conf
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

Config_NameSpace = {}
""" `NameSpace` managers for configuration key-value pairs."""

Config_Look_Up = {}
""" `Lazy_Loading_ChainMap`s for getting value with a key from Configuration dictionaries in files and in OS Environment.. """


@functools.lru_cache(8)
def get_file_conf(conf_name):
    """ figure iut config file name and returns the contents.

    :conf_name: str, 'pns' etc.

    Returns: dict for pre-fixed variables and for not prefixed variables.
    """

    CU = conf_name.upper() + '_'
    envname = CU + 'CONF_DIR'
    epath = os.getenv(envname, '')
    if isdir(epath):
        confp = epath
    else:
        # environment variable <conf_name>_CONFIG_DIR is not set
        env = expanduser(expandvars('$HOME'))
        # apache wsgi will return '$HOME' with no expansion
        if env == '$HOME':
            env = '/root'
        confp = join(env, '.config')
    # this is the var_name part of filename and the name of the returned dict
    var_name = conf_name+'config'
    module_name = conf_name+'local'
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

        if 0 and module:
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
            e) + '. Use default config in the package in fdi/pns/config.py. Copy it to ~/.config/%slocal.py and make persistent customization there.' % conf_name)
        return {}, {}
    # return a copy so refs can be wiped out by deleting the dict variable.
    return copy.deepcopy(getattr(module, var_name, {})), copy.deepcopy(getattr(module, 'config', {}))


def getMappings(conf_name, builtin):
    """return dictionaries of variable name in Environment or configure file.

    The look-up order is:

        1. with prefix in the Environment, e.g. `PNS_HOST`.
        2. in `prefixed_config`, e.g. `prefixed_config['host']`.
        3. without prefix in the Environment, e.g. `HOST`.
        4. in `config`, e.g. `config['host']`.

    Parameters
    ----------
    prefixed_config : dict
        configuration map of variables with prefix in Environment.
    config : dict
        configuration map of variables without prefix in Environment.
    conf_name : str
        The prefix. e.g. 'pns'.
    osenviron : dict
        Environment variables.
    name : str
        Variable name.

    Returns
    -------
    str
        Variable value.

    Exception
    ---------
    LookupError
        Variable not found.
    """

    # 'pns' etc
    skip = len(conf_name) + 1
    cnu = conf_name.upper()

    prefixed, not_prefixed = get_file_conf(conf_name)

    if 0:
        prefixed_osenv = dict((k[skip:].lower(), v)
                              for k, v in os.environ.items() if k[:skip-1] == cnu and k[skip:].lower() in prefixed)
    else:
        # prefixed names in ENV but not in config files allowed
        prefixed_osenv = dict((k[skip:].lower(), v)
                              for k, v in os.environ.items() if k[:skip-1] == cnu)

    not_prefixed_osenv = dict((k, os.environ[k.upper()])
                              for k, v in not_prefixed.items() if k.upper() in os.environ)

    if builtin is None:
        builtin = {}

    # higher proority is on the left
    return prefixed_osenv, prefixed, not_prefixed_osenv, not_prefixed, builtin


def loader(key, mapping, remove=True, exclude=None, ignore_error=False):

    if key in exclude:
        res = Load_Failed
    else:
        res = mapping.get(key, Load_Failed)
    if remove and res is not Load_Failed:
        del mapping[key]
    # return key in the mapping and the load result.
    return {key: res}


@functools.lru_cache(8)
def getConfClass(conf_name, builtin):
    if issubclass(builtin.__class__, ReadOnlyDict):
        builtin = dict(builtin)
    maps = getMappings(conf_name, builtin)

    class Conf(metaclass=NameSpace_meta,
               sources=maps,
               load=loader
               ):
        pass
    return Conf


_url_mark = 'poolurl:'
_len_um = len(_url_mark)


def cget(name, conf_name='pns', builtin=None, force=False):
    """Find value for configured variables.

    Look up in various places and check if `poolurl` is needed.
    The look-up order is:

        1. with prefix in the Environment, e.g. `PNS_HOST`.
        2. in `prefixed_config`, e.g. `prefixed_config['host']`.
        3. without prefix in the Environment, e.g. `HOST`.
        4. in `config`, e.g. `config['host']`.


    Parameters
    ----------
    name : str
        variable name. If starting with 'poolurl:' the rest of the
        name is used as the poolname part of a default-spec poolurl.
    conf_name : str
        name of configuration. Default 'pns'.
    builtin : dict
        a built-in dict given as the basis.
    force : bool
        Re-make the `Config_NameSpace` entry named `conf_name`, no matter what other parameters are.

    Returns
    -------
    str
        value of the variable.

    """

    global Config_NameSpace
    global Config_Look_Up

    if builtin is None:
        builtin = {}

    if force:
        getConfClass.cache_clear()

    conf_class = getConfClass(conf_name, ReadOnlyDict(builtin))
    Config_NameSpace[conf_name] = conf_class
    clu = conf_class.mapping
    Config_Look_Up[conf_name] = clu

    if not name:
        # name not given
        logger.debug(f'Dumping config {conf_name}.')
        return clu

    # check if request poolurn
    for_poolurl = name.startswith(_url_mark)

    if for_poolurl:
        name = name[_len_um:]
        # return poolurl if name startswith `poolurl`
        logger.debug(f'Getting poolurl by {name}.')
        purl = ''.join((clu['scheme'], '://',
                        clu['host'], ':',
                        str(clu['port']),
                        clu['baseurl']
                        ))
        # with the name
        return '%s/%s' % (purl, name)

    var = conf_class.mapping[name]
    logger.debug(f'Got config for {name} : {var}.')

    return var


def getConfig(name=None, conf='pns', builtin=builtin_conf, force=False):
    """Imports a dict named [conf]config.

    The contents of configuration are the key-value pairs of a
    `dict` variable :mod:`fdi.pns.config::<conf>config` by default.

    The configuration is updated by contents of a
    configuration file in the same format as `fdi.pns.config:pnsconfig`.
    Name of the configuration file is in the form of `<conf>local.py`
    where `<conf>` is the value of the `conf` parameter of this
    function, 'pns' by default.

    The config file directory is the process owner's ``~/.config/``
    by default. It can be modified by the environment
    variable ``<uppercased conf>_CONF_DIR``, e.g. `PNS_CONF_DIR`..

    An exisiting configuration value can be overridden
    by that of an environment variable. The env var is named
    `<uppercased <name>` for name variables in the `config` dict;
    but named `<uppercased <conf>_<name>` for name variables in
    the pre-fixed dict.
    For example configuration of `host` in `pnsconfig` dict is
    overridden by the value of envirionment variable
    `PNS_HOST`. `kc_type` in `config` dict is overridden by `KC_TYPE`.

    Parameters
    ----------
    name : str
        Identifier of the configured item whose value will be returned.
        If started with ```poolurl:```, construct a poolurl with
        ```scheme``` and ```node``` with ```/{name}``` at the end.
        Default ```None```, a mapping of all configured items
        corrected with envirionment variables is returned. 
        Prefixed names in ENV but not in config files are allowed.
    conf : str
         File `<conf>local.py`` defines configuration key-value
         pairs in `dict` named `<conf>config. Default 'pns', so the
         file is 'pnslocal.py', and the variable is `pnsconfig`.
    builtin : dict. To be updated by `<conf>local`. default is `fdi.pns.config`.
    force : bool
        Always 'False'
        reload from file instead of cache for all `conf`s cached.

    Returns
    -------
    obj
        configured value.

    """

    # default configuration is provided. Copy pns/config.py to ~/.config/pnslocal.py
    conflc = conf+'local'
    # this will cause 'spec not found
    # if force and conflc in sys.modules:
    #     logger.debug('Clearing config caches.')
    #     get_file_conf.cache_clear()

    if name:
        name = name.strip()

    return cget(name, conf_name=conf, builtin=builtin, force=force)


# Init Config_NameSpace and Config_Look_Up

cget('')


def make_pool(pool, conf='pns', auth=None, wipe=False):
    """ Return a ProductStorage with given pool name or poolURL.

    :name: PoolURL, or pool name (has no "://"), in which case a pool URL is made based on the result of `getConfig(name=pool, conf=conf)`. Default is ''.
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
        poolurl = getConfig(_url_mark+pool)

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
    Note that there is a 'PNS_' in the beginning environment variable
    name, e.g. ```PNS_MQ_HOST``` for ```pc['mq_host']```
    ref `fdi.utils.getConfig` and your local ```~/.config/pnslocal.py```
    """
    pc = getConfig()
    # default mqtt settings
    mqttargs = dict(
        mq_host=pc['mq_host'],
        mq_port=int(pc['mq_port']),
        mq_user=pc['mq_user'],
        mq_pass=pc['mq_pass'],
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

    parser.add_argument("name_pos", metavar='NAME', nargs='?',
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

    if args.debug:
        print(f'args: {args}')
    name0 = args.name_pos if args.name is None else args.name
    conf = getConfig(name0, conf=args.conf, force=args.force)
    if issubclass(conf.__class__, dict):
        # dictionart of all config items.
        print(json.dumps(conf, indent=4))
    else:
        print(conf)
    sys.exit(0)

#########


def XXXcheck_env(prefixed_config, config, conf_name, osenviron, name):
    """look up variable name in Environment or configure file.

    Parameters
    ----------
    prefixed_config : dict
        configuration map of variables with prefix in Environment.
    config : dict
        configuration map of variables without prefix in Environment.
    conf_name : str
        The prefix. e.g. 'pns'.
    osenviron : dict
        Environment variables.
    name : str
        Variable name.

    Returns
    -------
    str
        Variable value.

    Exception
    ---------
    LookupError
        Variable not found.
    """

    pcn = '%s_%s' % (conf_name, name)
    for cn, conf in [(pcn, prefixed_config), (name, config)]:
        env_var = cn.upper()
        if env_var in osenviron:
            logger.debug(f'found value for {name} in Env.')
            return osenviron[env_var]
        else:
            if name in conf:
                return conf[name]
            else:
                pass
    raise LookupError(f'{name} not found in config or Environment')


def XXXcget(name, conf_name='pns', builtin=None, force=False):
    """Find value for configured variables.

    Look up in various places and check if `poolurl` is needed. For
    order of places to look-up see :func:`check_env`.

    Parameters
    ----------
    name : str
        variable name. If starting with 'poolurl:' the rest of the
        name is used as the poolname part of a default-spec poolurl.
    conf_name : str
        name of configuration. Default 'pns'.
    builtin : dict
        a built-in dict given as the basis.
    force : bool
        updating source maps, no matter what other parameters are.

    Returns
    -------
    str
        value of the variable.

    """

    osenviron = os.environ

    if builtin is None:
        builtin = {}

    prefixed, not_prefixed = get_file_conf(conf_name)
    config = copy.copy(builtin)
    config.update(not_prefixed)

    if name is None:
        # name not given
        logger.debug(f'Dumping config {conf_name}.')
        res = config
        for k, v in prefixed.items():
            cn = '%s_%s' % (conf_name, k)
            env_var = cn.upper()
            res[k] = osenviron.get(env_var, v)
        return res
    withEnv = functools.partial(check_env, prefixed, not_prefixed,
                                conf_name, osenviron)
    # check if request poolurn
    for_poolurl = name.startswith(_url_mark)

    if for_poolurl:
        name = name[_len_um:]
        # return poolurl if name startswith `poolurl`
        logger.debug(f'Getting poolurl by {name}.')
        purl = ''.join((withEnv('scheme'), '://',
                        withEnv('host'), ':',
                        str(withEnv('port')),
                        withEnv('baseurl')
                        ))
        # with the name
        return '%s/%s' % (purl, name)

    # check env first, then prefixed, then not prefixed env, then not prefixed
    var = withEnv(name)

    return var
