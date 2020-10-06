# -*- coding: utf-8 -*-


from ..utils.common import lls
from fdi.dataset.deserialize import deserializeClassID
from fdi.dataset.serializable import serializeClassID
from ..pal.productstorage import ProductStorage
from ..pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from ..pal.query import MetaQuery, AbstractQuery
from ..pal.urn import makeUrn, parseUrn
from ..dataset.product import Product
# from .db_utils import check_and_create_fdi_record_table, save_action

# import mysql.connector
# from mysql.connector import Error

import sys
import os
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


from .server_skeleton import setuplogging, getUidGid, checkpath, pc, Classes, app, auth, APIs

logging = setuplogging()
logger = logging.getLogger(__name__)

logger.setLevel(pc['logginglevel'])
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

# =============HTTP POOL=========================

basepath = pc['server_poolpath']


def init_httppool_server():
    """ Init a global HTTP POOL """
    if PoolManager.isLoaded(DEFAULT_MEM_POOL):
        logger.debug('cleanup DEFAULT_MEM_POOL')
        PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
    logger.debug('cleanup PoolManager')
    PoolManager.removeAll()

    spd = os.path.join(basepath, pc['defaultpool'])
    checkpath(spd)
    ppd = os.path.join(pc['poolprefix'], pc['defaultpool'])

    pstore = ProductStorage(pool=ppd, isServer=True)

    # print('poolprefix-defaultpool ' + ppd)

    return pstore


def load_all_pools():
    """
    Adding all pool to server pool storage.
    """
    alldirs = []

    def getfiledir(filepath):
        paths = filepath.split('/')
        dirpath = ''
        for i in paths[2:-1]:
            dirpath = dirpath + i + '/'
        return dirpath[0:-1]

    def getallpools(path):
        allfilelist = os.listdir(path)
        for file in allfilelist:
            filepath = os.path.join(path, file)
            if os.path.isdir(filepath):
                getallpools(filepath)
            else:
                dirpath = getfiledir(filepath)
                if dirpath not in alldirs:
                    alldirs.append(dirpath)
        return alldirs
    path = basepath
    logger.debug('loading all from ' + path)

    alldirs = getallpools(path)
    for pool in alldirs:
        if pool == pc['defaultpool']:
            continue
        pp = os.path.join(pc['poolprefix'], pool)
        pstore.register(pp)
        logger.info("Registered pool: %s in %s" % (pp, path))


pstore = init_httppool_server()

load_all_pools()

# Check database
# check_and_create_fdi_record_table()


@app.route(pc['baseurl'])
def get_pools():
    return str(pstore.getPools())


@app.route(pc['baseurl'] + '/sn' + '/<string:prod_type>' + '/<string:pool_id>', methods=['GET'])
def get_pool_sn(prod_type, pool_id):
    """ Return the Serial Number for the given product type and pool_id."""
    logger.debug('### method %s prod_type %s poolID %s***' %
                 (request.method, prod_type, pool_id))
    res = 0
    path = os.path.join(basepath, pool_id)
    if os.path.exists(path):
        for i in os.listdir(path):
            if i[-1].isnumeric() and prod_type in i:
                res = res+1
    return str(res)


@app.route(pc['baseurl'] + '/<path:pool>', methods=['GET', 'POST', 'DELETE'])
@auth.login_required
def httppool(pool):
    """
    APIs for CRUD products, according to path and methods and return results.

    - GET: /pool_id/hk ==> return pool_id housekeeping
                 /pool_id/product_class/index ==> return product
                 /pool_id/{urns, classes, tags} ===> return pool_id urns or classes or tags

    - POST: /pool_id ==> Save product in requests.data in server

    - DELETE: /pool_id ==> Wipe all contents in pool_id
                         /pool_id/product_class/index ==> remove specified products in pool_id
    """
    username = request.authorization.username
    paths = pool.split('/')
    ts = time.time()
    logger.debug('*** method %s paths %s ***' % (request.method, paths))
    if request.method == 'GET':
        # TODO modify client loading pool , prefer use load_metadata rather than load_singer_metadata, because this will generate enormal sql transaction
        if paths[-1] in ['classes', 'urns', 'tags']:  # Retrieve single metadata
            result, msg = load_singer_metadata(paths)
            # save_action(username=username, action='READ', pool=paths[0])
        elif paths[-1] == 'hk':  # Load all metadata
            result, msg = load_metadata(paths)
            # save_action(username=username, action='READ', pool=paths[0])
        elif paths[-1].isnumeric():  # Retrieve product
            result, msg = load_product(paths)
            # save_action(username=username, action='READ', pool=paths[0])
        else:
            result = ''
            msg = 'Unknow request: ' + pool

    if request.method == 'POST' and paths[-1].isnumeric() and request.data != None:
        data = deserializeClassID(request.data)
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

    w = {'result': result, 'msg': msg, 'timestamp': ts}
    # logger.debug(pprint.pformat(w, depth=3, indent=4))
    s = serializeClassID(w)
    logger.debug(lls(s, 120))
    resp = make_response(s)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def delete_product(paths):
    pool = ''
    typename = paths[-2]
    index = str(paths[-1])
    for i in paths[0: -2]:
        pool = pool + i + '/'
    pool = pool[0:-1]
    poolurn = pc['poolprefix'] + '/' + pool
    urn = makeUrn(poolurn, paths[-2], paths[-1])
    logger.debug('DELETE product urn: ' + urn)
    try:
        if os.path.exists(os.path.join(basepath, pool)):
            if poolurn in pstore.getPools():
                pstore.getPool(poolurn).remove(urn)
                result = ''
                msg = 'remove product ' + urn + ' OK.'
            else:
                pstore.register(poolurn)
                pstore.getPool(poolurn).remove(urn)
                result = str(urn)
                msg = 'remove product ' + urn + ' OK.'
        else:
            result = 'FAILED'
            msg = 'No such pool: ' + poolurn
    except Exception as e:
        result = 'FAILED'
        msg = 'Unable to remove product: ' + urn + ' caused by ' + str(e)
    return result, msg


def delete_pool(paths):
    """ Remove contents of a pool
    Checking if the pool exists in server, and removing or returning exception message to client.
    """
    pool = ''
    for i in paths:
        pool = pool + i + '/'
    pool = pool[0:-1]
    poolurn = pc['poolprefix'] + '/' + pool
    logger.debug('DELETE POOLURN' + poolurn)
    try:
        if os.path.exists(os.path.join(basepath, pool)):
            if poolurn in pstore.getPools():
                pstore.getPool(poolurn).schematicWipe()
                result = ''
                msg = 'Wipe pool ' + poolurn + ' OK.'
            else:
                pstore.register(poolurn)
                pstore.getPool(poolurn).schematicWipe()
                result = ''
                msg = 'Wipe pool ' + poolurn + ' OK XXXXXX.'
        else:
            result = 'FAILED'
            msg = 'No such pool : ' + poolurn
    except Exception as e:
        result = 'FAILED'
        msg = 'Unable to wipe pool: ' + poolurn + ' caused by ' + str(e)
    return result, msg


def save_product(data,  paths, tag=None):
    """Save products
    """
    # poolname, resourcecn, indexs, scheme, place, poolpath = parseUrn(urn)
    pool = ''
    typename = paths[-2]
    index = str(paths[-1])
    for i in paths[0: -2]:
        pool = pool + i + '/'
    pool = pool[0:-1]
    poolurn = pc['poolprefix'] + '/' + pool
    logger.debug('SAVE product to: ' + poolurn)
    try:
        # if PoolManager.isLoaded(DEFAULT_MEM_POOL):
        #    PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
        # PoolManager.removeAll()
        pstore_tmp = ProductStorage(pool=poolurn, isServer=True)
        result = pstore_tmp.save(product=data, tag=tag, poolurn=poolurn)
        msg = 'Save data to ' + poolurn + ' OK.'
    except Exception as e:
        result = 'FAILED'
        msg = 'Exception : ' + str(e)
    return result, msg


def load_product(paths):
    """Load product
    """
    pool = ''
    for i in paths[0: -2]:
        pool = pool + i + '/'
    pool = pool[0:-1]
    poolurn = pc['poolprefix'] + '/' + pool
    logger.debug('LOAD product: ' + poolurn +
                 ':' + paths[-2] + ':' + paths[-1])
    try:
        if os.path.exists(os.path.join(basepath, pool)):
            if poolurn in pstore.getPools():
                result = pstore.getPool(poolurn).schematicLoadProduct(
                    paths[-2], paths[-1])
                msg = ''
            else:
                pstore.register(poolurn)
                result = pstore.getPool(poolurn).schematicLoadProduct(
                    paths[-2], paths[-1])
                msg = ''
        else:
            result = 'FAILED'
            msg = 'Pool not found: ' + poolurn
    except Exception as e:
        result = 'FAILED'
        msg = 'Exception : ' + str(e)
    return result, msg


def load_metadata(paths):
    """Load metadata of a pool
    """
    pool = ''
    for i in paths[0:-1]:
        pool = pool + i + '/'
    pool = pool[0:-1]
    poolurn = pc['poolprefix'] + '/' + pool
    try:
        if poolurn not in pstore.getPools():
            pstore.register(poolurn)
        c, t, u = pstore.getPool(poolurn).readHK()
        result = {'classes': c, 'tags': t, 'urns': u}
        msg = ''
        # else:
        #     result = 'FAILED'
        #     msg = 'No such pool: ' + poolurn
    except Exception as e:
        result = 'FAILED'
        msg = 'Exception : ' + str(e)
        raise e
    return result, msg


def load_singer_metadata(paths):
    """Load classes or urns or tags of a pool
    """
    pool = ''
    for i in paths[0: -2]:
        pool = pool + i + '/'
    pool = pool[0:-1]
    poolurn = pc['poolprefix'] + '/' + pool
    try:
        if poolurn not in pstore.getPools():
            pstore.register(poolurn)
        result = pstore.getPool(poolurn).readHKObj(paths[-1])
        msg = ''
    except Exception as e:
        result = 'FAILED'
        msg = 'Exception : ' + str(e)
    return result, msg


@app.route(pc['baseurl'] + '/<string:cmd>', methods=['GET'])
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

    s = serializeClassID(w)
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
