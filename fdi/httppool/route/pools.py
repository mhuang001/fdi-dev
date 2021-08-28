# -*- coding: utf-8 -*-

from .getswag import swag
from .httppool_server import resp, excp, checkpath, parseApiArgs, unauthorized
from ..model.user import auth
from ...dataset.serializable import serialize
from ...pal.poolmanager import PoolManager as PM, DEFAULT_MEM_POOL
from ...pal.webapi import WebAPI

from flask import Blueprint, jsonify, request, current_app
from flasgger import swag_from

import shutil
import time
import copy
import json
import os
from itertools import chain
from http import HTTPStatus


endp = swag['paths']

pools_api = Blueprint('pools', __name__)

######################################
#### /  get_registered_pools   ####
######################################


@ pools_api.route('/', methods=['GET'])
# @ swag_from(endp['/']['get'])
def get_registered_pools():
    """ Returns a list of Pool IDs (pool names) of all pools registered with the Global PoolManager.
    ---
    """
    ts = time.time()
    path = current_app.config['POOLPATH_BASE']
    current_app.logger.debug('Listing all registered pools.')

    result = [p.getPoolurl() for p in PM.getMap().values()]
    msg = 'There is/are %d pools registered to the PoolManager.' % len(result)
    code = 200
    return resp(code, result, msg, ts)


######################################
#### /pools  get_pools/  reg/unreg ####
######################################


# @ pools_api.route('', methods=['GET'])
@ pools_api.route('/pools', methods=['GET'])
# #@ swag_from(endp['/pools']['get'])
def get_pools():
    logger = current_app.logger
    if request.method in ['POST', 'PUT', 'DELETE'] and auth.current_user() == current_app.config['PC']['node']['ro_username']:
        msg = 'User %s us Read-Only, not allowed to %s.' % \
            (auth.current_user(), request.method)
        logger.debug(msg)
        return unauthorized(msg)

    ts = time.time()
    path = current_app.config['POOLPATH_BASE']
    logger.debug('Listing all directories from ' + path)

    result = get_name_all_pools(path)
    msg = '%d pools found.' % len(result)
    code = 200
    return resp(code, result, msg, ts)


def get_name_all_pools(path):
    """ Returns names of all pools in the given directory.

    """

    alldirs = []
    allfilelist = os.listdir(path)
    for file in allfilelist:
        filepath = os.path.join(path, file)
        if os.path.isdir(filepath):
            alldirs.append(file)
    current_app.logger.debug(path + ' has ' + str(alldirs))
    return alldirs

######################################
#### /pools/register_all pools/register_all/  ####
######################################


@ pools_api.route('/pools/register_all', methods=['PUT'])
# #@ swag_from(endp['/pools/register_all']['put'])
def register_all():
    """ Register (Load) all pools on tme server.


    """
    ts = time.time()
    pmap, bad = load_pools()
    code = 400 if len(bad) else 200
    result = ', '.join(pmap.keys())
    msg = '%d pools successfully loaded. Troubled: %s' % (len(pmap), str(bad))
    return resp(code, result, msg, ts)


def load_pools(poolnames=None):
    """
    Adding all pool to server pool storage.

    poolnames: if given as a list of poolnames, only the exisiting ones of the list will be loaded.
    """

    logger = current_app.logger
    path = current_app.config['POOLPATH_BASE']
    pmap = {}
    bad = {}
    logger.debug('loading all from ' + path)
    alldirs = poolnames if poolnames else get_name_all_pools(path)
    for nm in alldirs:
        # must save the link or PM._GLOBALPOOLLIST will remove as dead weakref
        code, res, msg = register_pool(nm)
        if code == 200:
            pmap[nm] = res
        else:
            bad[nm] = nm+': '+msg

    logger.debug("Registered pools: %s in %s" % (str(list(pmap.keys())), path))
    return pmap, bad

######################################
#### /pools/unregister_all  pools/unregister_all/  ####
######################################


@ pools_api.route('/pools/unregister_all', methods=['PUT'])
# @ swag_from(endp['/pools/unregister_all']['delete'])
def unregister_all():

    ts = time.time()
    good, bad = unregister_pools()
    code = 200 if not bad else 416
    result = good
    msg = '%d pools unregistered%s' % (len(good),
                                       (' except %s.' % str(bad) if len(bad) else '.'))
    return resp(code, result, msg, ts)


def unregister_pools(poolnames=None):
    """
    Removing all pools from the PoolManager.
`w
    poolnames: if given as a list of poolnames, only the ones in the list will be unregistered.

    Returns: a list of successfully unregistered pools names in `good`, and troubled ones in `bad` with associated exception info.
    """
    logger = current_app.logger

    good = []
    notgood = []
    all_pools = poolnames if poolnames else copy.copy(list(PM.getMap().keys()))
    logger.debug('unregister pools ' + str(all_pools))

    for nm in all_pools:
        code, res, msg = unregister_pool(nm)
        if res == 'FAILED':
            notgood.append(nm+': '+msg)
        else:
            good.append(nm)
    return good, notgood

######################################
#### /pools/wipe_all  pools/wipe_all/  ####
######################################


@ pools_api.route('/pools/wipe_all', methods=['DELETE'])
# @ swag_from(endp['/pools/wipe_all']['delete'])
def wipe_all():

    ts = time.time()
    good, bad = wipe_pools()
    code = 200 if not bad else 416
    result = good
    msg = '%d pools wiped%s' % (len(good),
                                (' except %s.' % str(bad) if len(bad) else '.'))
    return resp(code, result, msg, ts)


def wipe_pools(poolnames=None):
    """
    Deleting all pools using pool api so locking is properly used.

    poolnames: if given as a list of poolnames, only the  ones in the list will be deleted.

    Returns: a list of successfully removed pools names in `good`, and troubled ones in `bad` with associated exception info.
    """
    logger = current_app.logger
    path = current_app.config['POOLPATH_BASE']
    logger.debug('DELETING pools from ' + path)

    # alldirs = poolnames if poolnames else get_name_all_pools(path)

    good = []
    notgood = []
    all_pools = load_pools(poolnames)
    names = list(all_pools.keys())
    for nm in copy.copy(names):
        pool = all_pools[nm]
        try:
            pool.removeAll()
            shutil.rmtree(os.path.join(path, nm))
            PM.remove(nm)
            logger.info('Pool %s deleted.' % nm)
            good.append(nm)
        except Exception as e:
            notgood.append(nm+': '+str(e))
    return good, notgood

######################################
#### /{poolid}  get_pool/  reg/unreg ####
######################################


@ pools_api.route('/<path:poolid>', methods=['GET'])
# @ swag_from(endp['/{poolid}']['get'])
def get_pool(poolid):
    """ Get information of the given pool.

    Returns the state of the pool of given Pool IDs.
    """

    logger = current_app.logger

    ts = time.time()
    logger.debug('Get pool info of ' + poolid)

    _, result, _ = get_pool_info(poolid)
    return result


def get_pool_info(poolname, serialize_out=True):
    ''' returns information of the pool.
    '''
    msg = ''
    ts = time.time()
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    allpools = get_name_all_pools(current_app.config['POOLPATH_BASE'])
    if poolname in allpools:
        code, result, mes = load_single_HKdata(
            [poolname, 'hk', 'classes'],
            serialize_out=serialize_out)
        msg = 'Getting pool %s info.. %s.' % (poolname, mes)
    else:
        code, result, msg = 404, FAILED, poolname +\
            ' is not an exisiting Pool ID.'
    return 0, resp(code, result, msg, ts, serialize_out), 0

######################################
####  reg/unreg ####
######################################


@ pools_api.route('/<path:poolid>', methods=['PUT'])
# @ swag_from(endp['/{poolid}']['put'])
def register(poolid):
    """ Register the given pool.

    Register the pool of given Pool IDs to the global PoolManager.
    """

    logger = current_app.logger
    if auth.current_user() == current_app.config['PC']['node']['ro_username']:
        msg = 'User %s us Read-Only, not allowed to %s.' % \
            (auth.current_user(), request.method)
        logger.debug(msg)
        return unauthorized(msg)

    ts = time.time()
    logger.debug('register pool ' + poolid)

    code, result, msg = register_pool(poolid)

    return resp(code, result, msg, ts)


def register_pool(poolid):
    """ Register this pool to PoolManager.
    """
    poolname = poolid
    fullpoolpath = os.path.join(current_app.config['POOLPATH_BASE'], poolname)
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    try:
        po = PM.getPool(poolname=poolname, poolurl=poolurl)
        return 200, po._poolurl, 'register pool ' + poolname + ' OK.'
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to register pool: ' + poolname)
        current_app.logger.error(msg)
    return code, result, msg


@ pools_api.route('/<path:poolid>', methods=['DELETE'])
# @ swag_from(endp['/{poolid}']['delete'])
def unregister(poolid):
    """ Unregister this pool from PoolManager.

        Check if the pool exists in server, and unregister or raise exception message to client.

    """
    logger = current_app.logger
    if auth.current_user() == current_app.config['PC']['node']['ro_username']:
        msg = 'User %s us Read-Only, not allowed to %s.' % \
            (auth.current_user(), request.method)
        logger.debug(msg)
        return unauthorized(msg)

    ts = time.time()
    logger.debug('Unregister pool ' + poolid)

    code, result, msg = unregister_pool(poolid)
    return resp(code, result, msg, ts)


def unregister_pool(poolid):
    """ Unregister this pool from PoolManager.

    Check if the pool exists in server, and unregister or raise exception message.
    """

    poolname = poolid
    current_app.logger.debug('UNREGISTER (DELETE) POOL' + poolname)
    try:
        result = PM.remove(poolname)
        if result == 1:
            result = '1'
            msg = 'Pool not registered or referenced: ' + poolname
            code = 200
        elif result == 0:
            result = '0'
            msg = 'Unregister pool ' + poolname + ' OK.'
            code = 200
        else:
            result = 'FAILED'
            msg = 'Unable to unregister pool: ' + poolname
            code = 400
        #current_app.logger.debug(f'{code}; {result}; {msg}')
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to unregister pool: ' + poolname)
        current_app.logger.error(msg)
    checkpath.cache_clear()
    return code, result, msg


def call_pool_Api(paths, serialize_out=False):
    """ run api calls on the running pool.

    return
    """

    FAILED = '"FAILED"' if serialize_out else 'FAILED'
    logger = current_app.logger
    ts = time.time()

    # index of method name
    ind_meth = 2
    # remove empty trailing strings
    for o in range(len(paths), 1, -1):
        if paths[o-1]:
            break

    paths = paths[:o]
    lp = len(paths)
    method = paths[ind_meth]
    if method not in WebAPI:
        return 0, resp(400, FAILED,
                       'Unknown web API method: %s.' % method,
                       ts, serialize_out=False), 0
    args, kwds = [], {}

    all_args = paths[ind_meth+1:]
    if lp > ind_meth:
        # get command positional arguments and keyword arguments
        code, args, kwds = parseApiArgs(all_args, serialize_out=serialize_out)
        if code != 200:
            result, msg = args, kwds
            return 0, resp(422, result, msg, ts, serialize_out=False), 0
        else:
            kwdsexpr = [str(k)+'='+str(v) for k, v in kwds.items()]
            msg = '%s(%s)' % (method, ', '.join(
                chain(map(str, args), kwdsexpr)))
            logger.debug('WebAPI ' + msg)

    poolname = paths[0]
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    if not PM.isLoaded(poolname):
        result = FAILED
        msg = 'Pool not found: ' + poolname
        logger.error(msg)
        return 0, resp(404, result, msg, ts, serialize_out=False), 0

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        res = getattr(poolobj, method)(*args, **kwds)
        result = res
        msg = msg + ' OK.'
        code = 200
    except Exception as e:
        code, result, msg = excp(e, 422, serialize_out=serialize_out)
        logger.error(msg)

    return 0, resp(code, result, msg, ts, serialize_out=False), 0


def load_HKdata(paths, serialize_out=True):
    """Load HKdata of a pool
    """

    hkname = paths[-1]
    poolname = '/'.join(paths[0: -1])
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    # resourcetype = fullname(data)

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.readHK(serialize_out=serialize_out)
        msg = ''
        code = 200
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
        raise e
    return code, result, msg


def load_single_HKdata(paths, serialize_out=True):
    """ Returns pool housekeeping data of the specified type: classes or urns or tags.
    """

    hkname = paths[-1]
    # paths[-2] is 'hk'
    poolname = '/'.join(paths[: -2])
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    # resourcetype = fullname(data)

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.readHK(hkname, serialize_out=serialize_out)
        code, msg = 200, 'OK'
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
    return code, result, msg
