# -*- coding: utf-8 -*-

from ..utils.common import lls
from ..dataset.deserialize import deserialize
from ..dataset.serializable import serialize
from ..pal.productstorage import ProductStorage
from ..pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from ..pal.query import MetaQuery, AbstractQuery
from ..pal.urn import makeUrn, parseUrn
from ..dataset.product import Product
from ..utils.common import fullname, trbk

# from .db_utils import check_and_create_fdi_record_table, save_action

# import mysql.connector
# from mysql.connector import Error

import sys
import os
import json
import time
import pprint
from flask import request, make_response

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    # strset = (str, unicode)
    strset = str
    from urlparse import urlparse

# from .logdict import logdict
# '/var/log/pns-server.log'
# logdict['handlers']['file']['filename'] = '/tmp/server.log'

from .server_skeleton import logging, checkpath, pc, Classes, app, auth, APIs

logger = logging.getLogger(__name__)


# =============HTTP POOL=========================

# the httppool that is local to the server
schm = 'server'
basepath = PoolManager.PlacePaths[schm]
poolpath = os.path.join(basepath, pc['api_version'])


@app.before_first_request
def init_httppool_server():
    """ Init a global HTTP POOL """
    global PM

    logger.setLevel(pc['logginglevel'])
    logging.getLogger("filelock").setLevel(logging.INFO)
    logger.debug('logging level %d' % (logger.getEffectiveLevel()))

    PM = PoolManager
    if PM.isLoaded(DEFAULT_MEM_POOL):
        logger.debug('cleanup DEFAULT_MEM_POOL')
        PM.getPool(DEFAULT_MEM_POOL).removeAll()
    logger.debug('Done cleanup PoolManager.')
    logger.debug('ProcID %d 1st reg %s' % (os.getpid(),
                                           str(app._got_first_request))
                 )
    PM.removeAll()
    if checkpath(poolpath) is None:
        logger.error('Store path %s unavailable.' % poolpath)
        sys.exit(-2)

    load_all_pools()


def load_all_pools():
    """
    Adding all pool to server pool storage.
    """
    alldirs = set()

    def getallpools(path):
        allfilelist = os.listdir(path)
        for file in allfilelist:
            filepath = os.path.join(path, file)
            if os.path.isdir(filepath):
                alldirs.add(file)
        return alldirs
    path = poolpath
    logger.debug('loading all from ' + path)

    alldirs = getallpools(path)
    for poolname in alldirs:
        poolurl = schm + '://' + os.path.join(poolpath, poolname)
        PM.getPool(poolname=poolname, poolurl=poolurl)
        logger.info("Registered pool: %s in %s" % (poolname, poolpath))


# Check database
# check_and_create_fdi_record_table()


@ app.route(pc['baseurl'])
def get_pools():
    return str(pstore.getPools())


@ app.route(pc['baseurl'] + '/sn' + '/<string:prod_type>' + '/<string:pool_id>', methods=['GET'])
def get_pool_sn(prod_type, pool_id):
    """ Return the total count for the given product type and pool_id."""
    logger.debug('### method %s prod_type %s poolID %s***' %
                 (request.method, prod_type, pool_id))
    res = 0
    path = os.path.join(poolpath, pool_id)
    if os.path.exists(path):
        for i in os.listdir(path):
            if i[-1].isnumeric() and prod_type in i:
                res = res+1
    return str(res)


@ app.route(pc['baseurl'] + '/<path:pool>', methods=['GET', 'POST', 'DELETE'])
@ auth.login_required
def httppool(pool):
    """
    APIs for CRUD products, according to path and methods and return results.

    - GET: /pool_id/hk ==> return pool_id housekeeping
                 /pool_id/product_class/index ==> return product
                 /pool_id/hk ===> return pool_id Housekeeping data; urns, classes, and tags
                 /pool_id/hk/{urns, classes, tags} ===> return pool_id urns or classes or tags

    - POST: /pool_id ==> Save product in requests.data in server

    - DELETE: /pool_id ==> Wipe all contents in pool_id
                         /pool_id/product_class/index ==> remove specified products in pool_id
    """
    username = request.authorization.username
    paths = pool.split('/')
    ts = time.time()
    logger.debug('*** method %s paths %s ***' % (request.method, paths))
    if request.method == 'GET':
        # TODO modify client loading pool , prefer use load_HKdata rather than load_single_HKdata, because this will generate enormal sql transaction
        if paths[-2] == 'hk' and paths[-1] in ['classes', 'urns', 'tags']:  # Retrieve single HKdata
            result, msg = load_single_HKdata(paths)
            # save_action(username=username, action='READ', pool=paths[0])
        elif paths[-1] == 'hk':  # Load all HKdata
            result, msg = load_HKdata(paths)
            # save_action(username=username, action='READ', pool=paths[0])
        elif paths[-1].isnumeric():  # Retrieve product
            result, msg = load_product(paths)
            # save_action(username=username, action='READ', pool=paths[0])
        else:
            result = None
            msg = 'Unknow request: ' + pool

    if request.method == 'POST' and paths[-1].isnumeric() and request.data != None:
        data = deserialize(request.data)
        if request.headers.get('tag') is not None:
            tag = request.headers.get('tag')
        else:
            tag = None
        result, msg = save_product(data, paths, tag)
        # save_action(username=username, action='SAVE', pool=paths[0])

    if request.method == 'DELETE':
        if paths[-1].isnumeric():
            result, msg = delete_product(paths)
            # save_action(username=username, action='DELETE', pool=paths[0] +  '/' + paths[-2] + ':' + paths[-1])
        else:
            result, msg = delete_pool(paths)
            # save_action(username=username, action='DELETE', pool=paths[0])

    #w = {'result': result, 'msg': msg, 'timestamp': ts}
    # make a json string
    r = '"null"' if result is None else str(result)
    w = '{"result": %s, "msg": %s, "timestamp": %f}' % (
        r, json.dumps(msg), ts)
    # logger.debug(pprint.pformat(w, depth=3, indent=4))
    s = w  # serialize(w)
    logger.debug(lls(s, 120))
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def delete_product(paths):
    """ removes specified product from pool
    """

    typename = paths[-2]
    indexstr = paths[-1]
    poolname = '/'.join(paths[0: -2])
    poolurl = schm + '://' + os.path.join(poolpath, poolname)
    urn = makeUrn(poolname=poolname, typename=typename, index=indexstr)
    # resourcetype = fullname(data)

    if not PM.isLoaded(poolname):
        result = '"FAILED"'
        msg = 'Pool not found: ' + poolname
        return result, msg
    logger.debug('DELETE product urn: ' + urn)
    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.remove(urn)
        msg = 'remove product ' + urn + ' OK.'
    except Exception as e:
        result = '"FAILED"'
        msg = 'Unable to remove product: ' + urn + \
            ' caused by ' + str(e) + ' ' + trbk(e)
    return result, msg


def delete_pool(paths):
    """ Removes all contents of the pool.
    Checking if the pool exists in server, and removing or returning exception message to client.
    """

    poolname = '/'.join(paths)
    poolurl = schm + '://' + os.path.join(poolpath, poolname)
    # resourcetype = fullname(data)

    if not PM.isLoaded(poolname):
        result = '"FAILED"'
        msg = 'Pool not found: ' + poolname
        return result, msg
    logger.debug('DELETE POOL' + poolname)
    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.removeAll()
        msg = 'Wipe pool ' + poolname + ' OK.'
    except Exception as e:
        result = '"FAILED"'
        msg = 'Unable to wipe pool: ' + poolname + \
            ' caused by ' + str(e) + ' ' + trbk(e)
    return result, msg


def save_product(data, paths, tag=None):
    """Save products and returns URNs.

    Saving Products to HTTPpool will have data stored on the server side. The server only returns URN strings as a response. ProductRefs will be generated by the associated httpclient pool which is the front-end on the user side.


    Returns a URN object or a list of URN objects. 
    """

    typename = paths[-2]
    index = str(paths[-1])
    poolname = '/'.join(paths[0: -2])
    fullpoolpath = os.path.join(poolpath, poolname)
    poolurl = schm + '://' + fullpoolpath
    # resourcetype = fullname(data)

    if checkpath(fullpoolpath) is None:
        result = '"FAILED"'
        msg = 'Pool directory error: ' + fullpoolpath
        return result, msg

    logger.debug('SAVE product to: ' + poolurl)
    logger.debug(str(id(PM._GlobalPoolList)) + ' ' + str(PM._GlobalPoolList))

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.saveProduct(
            product=data, tag=tag, geturnobjs=True, serialized=True)
        msg = 'Save data to ' + poolurl + ' OK.'
    except Exception as e:
        result = '"FAILED"'
        msg = 'Exception : ' + str(e) + ' ' + trbk(e)
    return result, msg


def load_product(paths):
    """Load product
    """

    typename = paths[-2]
    indexstr = paths[-1]
    poolname = '/'.join(paths[0: -2])
    poolurl = schm + '://' + os.path.join(poolpath, poolname)
    urn = makeUrn(poolname=poolname, typename=typename, index=indexstr)
    # resourcetype = fullname(data)

    if not PM.isLoaded(poolname):
        result = '"FAILED"'
        msg = 'Pool not found: ' + poolname
        return result, msg

    logger.debug('LOAD product: ' + urn)
    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.loadProduct(urn=urn, serialized=True)
        msg = ''
    except Exception as e:
        result = '"FAILED"'
        msg = 'Exception : ' + str(e) + ' ' + trbk(e)
    return result, msg


def load_HKdata(paths):
    """Load HKdata of a pool
    """

    hkname = paths[-1]
    poolname = '/'.join(paths[0: -1])
    poolurl = schm + '://' + os.path.join(poolpath, poolname)
    # resourcetype = fullname(data)

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        c, t, u = poolobj.readHK(serialized=True)
        # make a json string
        result = '{"classes": %s, "tags": %s, "urns": %s}' % (c, t, u)
        msg = ''
    except Exception as e:
        result = '"FAILED"'
        msg = 'Exception : ' + str(e) + ' ' + trbk(e)
        raise e
    return result, msg


def load_single_HKdata(paths):
    """ Returns pool housekeeping data of the specified type: classes or urns or tags.
    """

    hkname = paths[-1]
    # paths[-2] is 'hk'
    poolname = '/'.join(paths[: -2])
    poolurl = schm + '://' + os.path.join(poolpath, poolname)
    # resourcetype = fullname(data)

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.readHK(hkname, serialized=True)
        msg = ''
    except Exception as e:
        result = '"FAILED"'
        msg = 'Exception : ' + str(e) + ' ' + trbk(e)
    return result, msg


@ app.route(pc['baseurl'] + '/<string:cmd>', methods=['GET'])
def getinfo(cmd):
    ''' returns init, config, run input, run output.
    '''
    logger.debug('getr %s' % (cmd))

    msg = ''
    ts = time.time()
    try:
        if cmd == 'pnsconfig':
            result, msg = pc, ''
        else:
            result, msg = -1, cmd + ' is not valid.'
    except Exception as e:
        result, msg = -1, str(e) + trbk(e)
    w = {'result': result, 'message': msg, 'timestamp': ts}

    s = serialize(w)
    logger.debug(s[:] + ' ...')
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


# API specification for this module
ModAPIs = {'GET':
           {'func': 'get_pool_sn',
            'cmds': {'sn': 'the Serial Number'}
            },
           'PUT':
           {
           },
           'POST':
           {'func': 'httppool',
            'cmds': {}
            },
           'DELETE':
           {'func':  'httppool',
               'cmds': {}
            }}


# Use ModAPIs contents for server_skeleton.get_apis()
APIs.update(ModAPIs)
logger.debug('END OF '+__file__)
