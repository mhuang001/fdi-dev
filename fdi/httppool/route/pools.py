# -*- coding: utf-8 -*-

from .httppool_server import resp, excp, checkpath, parseApiArgs
from ..model.user import auth
from ..model.welcome import WelcomeModel, returnSomething
from ..schema.result import return_specs_dict, return_specs_dict2
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


pools_api = Blueprint('/', __name__)


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


def getinfo(poolname, serialize_out=True):
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
        code, result, msg = 404, FAILED, poolname + ' is not an exisiting Pool ID.'
    return 0, resp(code, result, msg, ts, serialize_out), 0


@ pools_api.route('', methods=['GET'])
@ pools_api.route('/pools', methods=['GET'])
@swag_from(return_specs_dict2)
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
    msg = 'pools found.'
    code = 200
    return resp(code, result, msg, ts)


def load_all_pools(poolnames=None):
    """
    Adding all pool to server pool storage.

    poolnames: if given as a list of poolnames, only the exisiting ones of the list will be loaded.
    """

    logger = current_app.logger
    path = current_app.config['POOLPATH_BASE']
    pmap = {}
    logger.debug('loading all from ' + path)
    alldirs = poolnames if poolnames else get_name_all_pools(path)
    for poolname in alldirs:
        poolurl = current_app.config['POOLURL_BASE'] + poolname
        # must save the link or PM._GLOBALPOOLLIST will remove as dead weakref
        pmap[poolname] = PM.getPool(poolname=poolname, poolurl=poolurl)

    logger.debug("Registered pools: %s in %s" % (str(list(pmap.keys())), path))
    return pmap


def wipe_pools(poolnames=None):
    """
    Deleting all pools using pool api so locking is properly used.

    poolnames: if given as a list of poolnames, only the exisiting ones of the list will be deleted.

    Returns: a list of successfully removed pools names in `good`, and troubled ones in `bad` with associated exception info.
    """
    logger = current_app.logger
    path = current_app.config['POOLPATH_BASE']
    logger.debug('DELETING pools from ' + path)

    # alldirs = poolnames if poolnames else get_name_all_pools(path)

    good = []
    notgood = []
    all_pools = load_all_pools(poolnames)
    names = list(all_pools.keys())
    for nm in names:
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


@ pools_api.route('/', methods=['GET'])
@swag_from(return_specs_dict2)
def get_poolmanager():
    """ Returns a list of Pool IDs (pool names) of all poolson registered with the Global PoolManager.
    """
    ts = time.time()
    path = current_app.config['POOLPATH_BASE']
    current_app.logger.debug('Listing all registered pools.')

    result = [str(p) for p in PM.getMap().values()]
    msg = 'There is/are %d pools registered to the PoolManager.' % len(result)
    code = 200
    return resp(code, result, msg, ts)


@ pools_api.route('/wipe_all_pools', methods=['PUT'])
def wipe_all_pools():

    ts = time.time()
    good, bad = wipe_pools()
    code = 200 if not bad else 416
    result = good
    msg = 'pools wiped' + ('except %s.' % str(bad) if len(bad) else '.')
    return resp(code, result, msg, ts)


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


def register_pool(paths):
    """ Register this pool to PoolManager.
    """
    poolname = '/'.join(paths)
    fullpoolpath = os.path.join(current_app.config['POOLPATH_BASE'], poolname)
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    try:
        po = PM.getPool(poolname=poolname, poolurl=poolurl)
        return 200, '"'+po._poolurl+'"', 'register pool ' + poolname + ' OK.'
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to register pool: ' + poolname)
        current_app.logger.error(msg)
    return code, result, msg


def unregister_pool(paths):
    """ Unregister this pool from PoolManager.

    Checking if the pool exists in server, and unregister or raise exception message to client.
    """

    poolname = '/'.join(paths)
    current_app.logger.debug('UNREGISTER (DELETE) POOL' + poolname)
    try:
        result = PM.remove(poolname)
        if result == 1:
            result = '"1"'
            msg = 'Pool not registered or referenced: ' + poolname
            code = 200
        elif result == '"0"':
            msg = 'Unregister pool ' + poolname + ' OK.'
            code = 200
        else:
            result = '"FAILED"'
            msg = 'Unable to unregister pool: ' + poolname
            code = 400
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to unregister pool: ' + poolname)
    checkpath.cache_clear()
    return code, result, msg


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


@pools_api.route('/w1')
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'Welcome to the Flask Starter Kit',
            'schema': return_specs_dict2
        }
    }
})
def welcome():
    """
    1 liner about the route
    A more detailed description of the endpoint
    ---
    """
    #result = WelcomeModel()
    # return serialize(result), 200

    result = returnSomething()
    return jsonify(result), 200


httppool_api2 = Blueprint('hp2', __name__)


@httppool_api2.route('/w2')
@swag_from('swagger.yml')
def welcome2():
    """
    1 liner about the route
    A more detailed description of the endpoint
    ---
    """
    #result = WelcomeModel()
    # return serialize(result), 200

    result = returnSomething()
    return jsonify(result), 200
