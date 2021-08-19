# -*- coding: utf-8 -*-

from httppool.schema.result import return_specs_dict, return_specs_dict2

# from .server_skeleton import init_conf_clas, User, checkpath, app, auth, pc
from fdi.utils.common import lls
from fdi.dataset.deserialize import deserialize
from fdi.dataset.serializable import serialize
from fdi.pal.urn import makeUrn
from fdi.pal.webapi import WebAPI
from fdi.dataset.classes import Classes
from fdi.utils.common import trbk, getUidGid
from fdi.utils.fetch import fetch
from fdi.pal.poolmanager import PoolManager as PM, DEFAULT_MEM_POOL
# from .db_utils import check_and_create_fdi_record_table, save_action

# import mysql.connector
# from mysql.connector import Error

from flasgger import swag_from

from flask import Flask, request, make_response, jsonify, Blueprint, current_app
from flask.wrappers import Response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import sys
import os
import copy
import json
import time
import shutil
import builtins
import functools
import datetime
import operator
from collections import ChainMap
from itertools import chain
from pathlib import Path
import importlib
from http import HTTPStatus

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    # strset = (str, unicode)
    strset = str
    from urlparse import urlparse


# ######################################
# #### Application Factory Function ####
# ######################################


# def create_app(config_object=None):
#     app = Flask(__name__, instance_relative_config=True)
#     config_object = config_object if config_object else getconfig.getConfig()
#     app.config['PC'] = config_object
#     import logging
#     import logging.config
#     from .logdict import logdict
#     logging.config.dictConfig(logdict)
#     # '/var/log/pns-server.log'
#     # logdict['handlers']['file']['filename'] = '/tmp/server.log'
#     app.logger = logging.getLogger(__name__)
#     # initialize_extensions(app)
#     # register_blueprints(app)
#     init_httppool_server(app)
#     return app


# Global variables set to temprary values before setGlabals() runs
auth = HTTPBasicAuth()
logger = __import__('logging').getLogger(__name__)

httppool_api = Blueprint('httppool', __name__)


def init_conf_classes(pc, lggr):

    from fdi.dataset.classes import Classes

    # setup user class mapping
    clp = pc['userclasses']
    lggr.debug('User class file '+clp)
    if clp == '':
        Classes.updateMapping()
    else:
        clpp, clpf = os.path.split(clp)
        sys.path.insert(0, os.path.abspath(clpp))
        # print(sys.path)
        pcs = __import__(clpf.rsplit('.py', 1)[
            0], globals(), locals(), ['PC'], 0)
        pcs.PC.updateMapping()
        Classes.updateMapping(pcs.PC.mapping)
        lggr.debug('User classes: %d found.' % len(pcs.PC.mapping))
    return Classes


class User():

    def __init__(self, name, passwd, role='read_only'):

        self.username = name
        self.password = passwd
        self.registered_on = datetime.datetime.now()
        self.hashed_password = generate_password_hash(passwd)
        self.role = role
        self.authenticated = False

    def is_correct_password(self, plaintext_password):

        return check_password_hash(plaintext_password, self.hashed_password)

    def __repr__(self):
        return f'<User: {self.username}, {self.password}>'


uspa = operator.attrgetter('username', 'password')


@functools.lru_cache(6)
def checkpath(path, un):
    """ Checks  the directories and creats if missing.

    path: str. can be resolved with Path.
    un: server user name
    """
    logger.debug('path %s user %s' % (path, un))

    p = Path(path).resolve()
    if p.exists():
        if not p.is_dir():
            msg = str(p) + ' is not a directory.'
            logger.error(msg)
            return None
        else:
            # if path exists and can be set owner and group
            if p.owner() != un or p.group() != un:
                msg = str(p) + ' owner %s group %s. Should be %s.' % \
                    (p.owner(), p.group(), un)
                logger.warning(msg)
    else:
        # path does not exist

        msg = str(p) + ' does not exist. Creating...'
        logger.debug(msg)
        p.mkdir(mode=0o775, parents=True, exist_ok=True)
        logger.info(str(p) + ' directory has been made.')

    # logger.info('Setting owner, group, and mode...')
    if not setOwnerMode(p, un):
        return None

    logger.debug('checked path at ' + str(p))
    return p


def init_httppool_server():
    """ Init a global HTTP POOL """
    app = current_app

    import logging
    app.logger = logging.getLogger(__name__)
    app.logger.setLevel(app.config['LOGGER_LEVEL'])

    # local.py config
    pc = app.config['PC']
    # class namespace
    Classes = init_conf_classes(pc, app.logger)
    lookup = ChainMap(Classes.mapping, globals(), vars(builtins))
    app.config['LOOKUP'] = lookup

    # auth
    app.config['AUTH'] = auth

    # users
    # effective group of current process
    uid, gid = getUidGid(pc['serveruser'])
    app.logger.info("Serveruser %s's uid %d and gid %d..." %
                    (pc['serveruser'], uid, gid))
    # os.setuid(uid)
    # os.setgid(gid)
    xusers = {
        "rw": generate_password_hash(pc['node']['username']),
        "ro": generate_password_hash(pc['node']['password'])
    }
    users = [
        User(pc['node']['username'], pc['node']['password'], 'read_write'),
        User(pc['node']['ro_username'], pc['node']
             ['ro_password'], 'read_only')
    ]
    app.config['USERS'] = users

    # PoolManager is a singleton
    if PM.isLoaded(DEFAULT_MEM_POOL):
        logger.debug('cleanup DEFAULT_MEM_POOL')
        PM.getPool(DEFAULT_MEM_POOL).removeAll()
    app.logger.debug('Done cleanup PoolManager.')
    app.logger.debug('ProcID %d. Got 1st request %s' % (os.getpid(),
                                                        str(app._got_first_request))
                     )
    PM.removeAll()

    # pool-related paths
    # the httppool that is local to the server
    scheme = 'server'
    _basepath = PM.PlacePaths[scheme]
    poolpath = os.path.join(_basepath, pc['api_version'])

    if checkpath(poolpath, pc['serveruser']) is None:
        app.logger.error('Store path %s unavailable.' % poolpath)
        sys.exit(-2)

    app.config['POOLSCHEME'] = scheme
    app.config['POOLPATH'] = poolpath

    set_globals(app)

# =============HTTP POOL=========================

# @httppool_api.before_app_first_request


def set_globals(app):
    global pc, poolpath, poolurl_base, auth, logger
    logger = app.logger
    pc = app.config['PC']
    poolpath = app.config['POOLPATH']
    poolurl_base = app.config['POOLSCHEME'] + '://' + poolpath + '/'
    auth = app.config['AUTH']


def get_name_all_pools(path):
    """ Returns names of all pools in the given directory.

    """
    alldirs = []
    allfilelist = os.listdir(path)
    for file in allfilelist:
        filepath = os.path.join(path, file)
        if os.path.isdir(filepath):
            alldirs.append(file)
    logger.debug(path + ' has ' + str(alldirs))
    return alldirs


def load_all_pools(poolnames=None):
    """
    Adding all pool to server pool storage.

    poolnames: if given as a list of poolnames, only the exisiting ones of the list will be loaded.
    """

    path = poolpath
    pmap = {}
    logger.debug('loading all from ' + path)
    alldirs = poolnames if poolnames else get_name_all_pools(path)
    for poolname in alldirs:
        poolurl = poolurl_base + poolname
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

    path = poolpath
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
            shutil.rmtree(os.path.join(poolpath, nm))
            PM.remove(nm)
            logger.info('Pool %s deleted.' % nm)
            good.append(nm)
        except Exception as e:
            notgood.append(nm+': '+str(e))
    return good, notgood


def get_prod_count(prod_type, pool_id):
    """ Return the total count for the given product type and pool_id in the directory.

    'prod_type': 'clsssname',
    'pool_id': 'pool name'

    """

    logger.debug('### method %s prod_type %s poolID %s***' %
                 (request.method, prod_type, pool_id))
    res = 0
    nm = []
    path = os.path.join(poolpath, pool_id)
    if os.path.exists(path):
        for i in os.listdir(path):
            if i[-1].isnumeric() and prod_type in i:
                res = res+1
                nm.append(i)
    s = str(nm)
    logger.debug('found '+s)
    return 200, str(res), 'Counting %s files OK'


def resp(code, result, msg, ts, serialize_out=False, ctype='application/json', length=70):
    """
    Make response.

    :ctype: Content-Type. Default is `application/json`
    :serialize_out: if True `result` is in serialized form.
    """
    # return if `result` is already a Response
    if issubclass(result.__class__, Response):
        return result
    if ctype == 'application/json':
        if serialize_out:
            # result is already in serialized form
            p = 'no-serialization-result-place-holder'
            t = serialize({"code": code, "result": p,
                           "msg": msg, "time": ts})
            w = t.replace('"'+p+'"', result)
        else:
            w = serialize({"code": code, "result": result,
                           "msg": msg, "time": ts})
    else:
        w = result

    logger.debug(lls(w, length))
    # logger.debug(pprint.pformat(w, depth=3, indent=4))
    resp = make_response(w)
    resp.headers['Content-Type'] = ctype
    return resp


def excp(e, code=400, msg='', serialize_out=True):
    result = '"FAILED"' if serialize_out else 'FAILED'
    msg = '%s\n%s: %s.\nTrace back: %s' % (
        msg, e.__class__.__name__, str(e), trbk(e))

    return code, result, msg


@ httppool_api.route('', methods=['GET'])
@ httppool_api.route('/pools', methods=['GET'])
@swag_from(return_specs_dict2)
def get_pools():
    if request.method in ['POST', 'PUT', 'DELETE'] and auth.current_user() == pc['node']['ro_username']:
        msg = 'User %s us Read-Only, not allowed to %s.' % \
            (auth.current_user(), request.method)
        logger.debug(msg)
        return unauthorized(msg)

    ts = time.time()
    path = poolpath
    logger.debug('Listing all directories from ' + path)

    result = get_name_all_pools(path)
    msg = 'pools found.'
    code = 200
    return resp(code, result, msg, ts)


@ httppool_api.route('/', methods=['GET'])
@swag_from(return_specs_dict2)
def get_poolmanager():
    """ Returns a list of Pool IDs (pool names) of all poolson registered with the Global PoolManager.
    """
    ts = time.time()
    path = poolpath
    logger.debug('Listing all registered pools.')

    result = [str(p) for p in PM.getMap().values()]
    msg = 'There is/are %d pools registered to the PoolManager.' % len(result)
    code = 200
    return resp(code, result, msg, ts)


@ httppool_api.route('/wipe_all_pools', methods=['PUT'])
def wipe_all_pools():

    ts = time.time()
    good, bad = wipe_pools()
    code = 200 if not bad else 416
    result = good
    msg = 'pools wiped' + ('except %s.' % str(bad) if len(bad) else '.')
    return resp(code, result, msg, ts)


def getinfo(poolname, serialize_out=True):
    ''' returns information of the pool.
    '''
    msg = ''
    ts = time.time()
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    allpools = get_name_all_pools(poolpath)
    if poolname in allpools:
        code, result, mes = load_single_HKdata(
            [poolname, 'hk', 'classes'],
            serialize_out=serialize_out)
        msg = 'Getting pool %s info.. %s.' % (poolname, mes)
    else:
        code, result, msg = 404, FAILED, poolname + ' is not an exisiting Pool ID.'
    return 0, resp(code, result, msg, ts, serialize_out), 0


def parseApiArgs(all_args, serialize_out=False):
    """ parse the command path to get positional and keywords arguments.

    all_args: a list of path segments for the args list.
    """
    lp = len(all_args)
    args, kwds = [], {}
    if lp % 2 == 1:
        # there are odd number of args+key+val
        # the first seg after ind_meth must be all the positional args
        try:
            tyargs = all_args[0].split('|')
            for a in tyargs:
                print(a)
                v, c, t = a.rpartition(':')
                args.append(mkv(v, t))
        except IndexError as e:
            code, result, msg = excp(
                e,
                msg='Bad arguement format ' + all_args[0],
                serialize_out=serialize_out)
            logger.error(msg)
            return code, result, msg
        kwstart = 1
    else:
        kwstart = 0
    # starting from kwstart are the keyword arges k1|v1 / k2|v2 / ...

    try:
        while kwstart < lp:
            v, t = all_args[kwstart].rsplit(':', 1)
            kwds[all_args[kwstart]] = mkv(v, t)
            kwstart += 2
    except IndexError as e:
        code, result, msg = excp(
            e,
            msg='Bad arguement format ' + str(all_args[kwstart:]),
            serialize_out=serialize_out)
        logger.error(msg)
        return code, result, msg

    return 200, args, kwds


def call_pool_Api(paths, serialize_out=False):
    """ run api calls on the running pool.

    return
    """

    FAILED = '"FAILED"' if serialize_out else 'FAILED'
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
    poolurl = poolurl_base + poolname
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


# @ httppool_api.route('/sn' + '/<string:prod_type>' + '/<string:pool_id>', methods=['GET'])


@ httppool_api.route('/<path:pool>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@ auth.login_required
def httppool(pool):
    """
    APIs for CRUD products, according to path and methods and return results.

    - GET:
                 /pool_id/product_class/index ==> return product
                 /pool_id/hk ===> return pool_id Housekeeping data; urns, classes, and tags
                 /pool_id/hk/{urns, classes, tags} ===> return pool_id urns or classes or tags
                 /pool_id/count/product_class ===> return the number of products in the pool

    - POST: /pool_id ==> Save product in requests.data in server

    - PUT: /pool_id ==> register pool

    - DELETE: /pool_id ==> unregister pool_id
                         /pool_id/product_class/index ==> remove specified products in pool_id

    'pool':'url'
    """
    if request.method in ['POST', 'PUT', 'DELETE'] and auth.current_user() == pc['node']['ro_username']:
        msg = 'User %s us Read-Only, not allowed to %s.' % \
            (auth.current_user(), request.method)
        logger.debug(msg)
        return unauthorized(msg)

    username = request.authorization.username
    paths = pool.split('/')
    if 0:
        import pdb
        pdb.set_trace()

    lp0 = len(paths)
    if lp0 == 0:
        code, result, msg = getinfo()

    # if paths[-1] == '':
    #    del paths[-1]

    # paths[0] is A URN
    if paths[0].lower().startswith('urn+'):
        p = paths[0].split('+')
        # example ['urn', 'test', 'fdi.dataset.product.Product', '0']
        paths = p[1:] + paths[1:] if lp0 > 1 else []

    # paths[1] is A URN
    if lp0 > 1 and paths[1].lower().startswith('urn+'):
        p = paths[1].split('+')
        # example ['urn', 'test', 'fdi.dataset.product.Product', '0']
        paths = p[1:] + paths[2:] if lp0 > 2 else []
    # paths is normalized to [poolname, ... ]
    lp = len(paths)
    ts = time.time()
    # do not deserialize if set True. save directly to disk
    serial_through = True
    logger.debug('*** method %s paths %s ***' % (request.method, paths))

    if request.method == 'GET':
        # TODO modify client loading pool , prefer use load_HKdata rather than load_single_HKdata, because this will generate enormal sql transaction
        if lp == 1:
            code, result, msg = getinfo(paths[0])
        elif lp == 2:
            p1 = paths[1]
            if p1 == 'hk':  # Load all HKdata
                code, result, msg = load_HKdata(
                    paths, serialize_out=serial_through)
                return resp(code, result, msg, ts, serialize_out=serial_through)
            elif p1 == 'api':
                code, result, msg = call_pool_Api(paths, serialize_out=False)
            elif p1 == '':
                code, result, msg = getinfo(paths[0])
            else:
                code, result, msg = getProduct_Or_Component(
                    paths, serialize_out=serial_through)
        elif lp == 3:
            p1 = paths[1]
            if p1 == 'hk' and paths[2] in ['classes', 'urns', 'tags']:
                # Retrieve single HKdata
                code, result, msg = load_single_HKdata(
                    paths, serialize_out=serial_through)
                return resp(code, result, msg, ts, serialize_out=serial_through)
            elif p1 == 'count':  # prod count
                code, result, msg = get_prod_count(paths[2], paths[0])
            elif p1 == 'api':
                code, result, msg = call_pool_Api(paths, serialize_out=False)
            else:
                code, result, msg = getProduct_Or_Component(
                    paths, serialize_out=serial_through)
        elif lp > 3:
            p1 = paths[1]
            if p1 == 'api':
                code, result, msg = call_pool_Api(paths, serialize_out=False)
            else:
                code, result, msg = getProduct_Or_Component(
                    paths, serialize_out=serial_through)
        else:
            code = 400
            result = '"FAILED"'
            msg = 'Unknown request: ' + pool

    elif request.method == 'POST' and paths[-1].isnumeric() and request.data != None:
        # save product
        if request.headers.get('tag') is not None:
            tag = request.headers.get('tag')
        else:
            tag = None

        if serial_through:
            data = str(request.data, encoding='ascii')

            code, result, msg = save_product(
                data, paths, tag, serialize_in=not serial_through, serialize_out=serial_through)
        else:
            try:
                data = deserialize(request.data)
            except ValueError as e:
                code, result, msg = excp(
                    e,
                    msg='Class needs to be included in pool configuration.',
                    serialize_out=serialize_out)
            else:
                code, result, msg = save_product(
                    data, paths, tag, serialize_in=not serial_through)
                # save_action(username=username, action='SAVE', pool=paths[0])
    elif request.method == 'PUT':
        code, result, msg = register_pool(paths)
        return resp(code, result, msg, ts, serialize_out=True)

    elif request.method == 'DELETE':
        if paths[-1].isnumeric():
            code, result, msg = delete_product(paths)
            # save_action(username=username, action='DELETE', pool=paths[0] +  '/' + paths[-2] + ':' + paths[-1])
        else:
            code, result, msg = unregister_pool(paths)
            # save_action(username=username, action='DELETE', pool=paths[0])
        return resp(code, result, msg, ts, serialize_out=True)
    else:
        result, msg = '"FAILED"', 'UNknown command '+request.method
        code = 400
        return resp(code, result, msg, ts, serialize_out=True)

    return resp(code, result, msg, ts, serialize_out=serial_through)


Builtins = vars(builtins)


def mkv(v, t):
    """
    return v with a tyoe specified by t.

    t: 'NoneType' or any name in ``Builtins``.
    """

    m = v if t == 'str' else None if t == 'NoneType' else Builtins[t](
        v) if t in Builtins else deserialize(v)
    return m


def delete_product(paths):
    """ removes specified product from pool
    """

    typename = paths[-2]
    indexstr = paths[-1]
    poolname = '/'.join(paths[0: -2])
    poolurl = poolurl_base + poolname
    urn = makeUrn(poolname=poolname, typename=typename, index=indexstr)
    # resourcetype = fullname(data)

    if not PM.isLoaded(poolname):
        result = '"FAILED"'
        msg = 'Pool not found: ' + poolname
        code = 400
        logger.error(msg)
        return code, result, msg
    logger.debug('DELETE product urn: ' + urn)
    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        poolobj.remove(urn)
        result = '"0"'
        msg = 'remove product ' + urn + ' OK.'
        code = 200
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to remove product: ' + urn)
        logger.error(msg)
    return code, result, msg


def register_pool(paths):
    """ Register this pool to PoolManager.
    """
    poolname = '/'.join(paths)
    fullpoolpath = os.path.join(poolpath, poolname)
    poolurl = poolurl_base + poolname
    try:
        po = PM.getPool(poolname=poolname, poolurl=poolurl)
        return 200, '"'+po._poolurl+'"', 'register pool ' + poolname + ' OK.'
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to register pool: ' + poolname)
        logger.error(msg)
    return code, result, msg


def unregister_pool(paths):
    """ Unregister this pool from PoolManager.

    Checking if the pool exists in server, and unregister or raise exception message to client.
    """

    poolname = '/'.join(paths)
    logger.debug('UNREGISTER (DELETE) POOL' + poolname)
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


def save_product(data, paths, tag=None, serialize_in=True, serialize_out=False):
    """Save products and returns URNs.

    Saving Products to HTTPpool will have data stored on the server side. The server only returns URN strings as a response. ProductRefs will be generated by the associated httpclient pool which is the front-end on the user side.


    Returns a URN object or a list of URN objects.
    """

    typename = paths[-2]
    index = str(paths[-1])
    poolname = '/'.join(paths[0: -2])
    fullpoolpath = os.path.join(poolpath, poolname)
    poolurl = poolurl_base + poolname
    # resourcetype = fullname(data)

    if checkpath(fullpoolpath, pc['serveruser']) is None:
        result = '"FAILED"'
        msg = 'Pool directory error: ' + fullpoolpath
        return result, msg

    logger.debug('SAVE product to: ' + poolurl)
    # logger.debug(str(id(PM._GlobalPoolList)) + ' ' + str(PM._GlobalPoolList))

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.saveProduct(
            product=data, tag=tag, geturnobjs=True, serialize_in=serialize_in, serialize_out=serialize_out)
        msg = 'Save data to ' + poolurl + ' OK.'
        code = 200
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
    return code, result, msg


def getProduct_Or_Component(paths, serialize_out=False):
    """
    :serialize_out: see :meth:`ProductPool.saveProduct`
    """

    lp = len(paths)
    # now paths = poolname, prod_type , ...

    ts = time.time()
    mInfo = 0
    if lp == 2:
        # ex: test/fdi.dataset.Product
        # return classes[class]
        pp = paths[1]
        mp = pp.rsplit('.', 1)
        modname, ptype = mp[0], mp[1]
        cls = Classes.mapping[ptype]
        mod = importlib.import_module(modname)  # TODO
        mInfo = getattr(mod, 'Model')
        # non-serialized
        return 0, resp(200, mInfo,
                       'Getting API info for %s OK' % paths[1],
                       ts, serialize_out=False), 0
    elif lp >= 3:
        return compo_cmds(paths, mInfo, serialize_out=serialize_out)

    else:
        return 400, '"FAILED"', 'Unknown path %s' % str(paths)


def compo_cmds(paths, mInfo, serialize_out=False):
    """ Get the component and the associated command and return

    Except for full products, most components  are not in serialized form.
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'
    ts = time.time()

    lp = len(paths)

    for cmd_ind in range(1, lp):
        cmd = paths[cmd_ind]
        if cmd.startswith('$'):
            cmd = cmd.lstrip('$')
            paths[cmd_ind] = cmd
            break
    else:
        cmd = ''

    # args if found command and there is something after it
    cmd_args = paths[cmd_ind+1:] if cmd and (lp - cmd_ind > 1)else ['']
    # prod type
    pt = paths[1]
    # index
    pi = paths[2]
    # path of prod or component
    compo_path = paths[1:cmd_ind] if cmd else paths[1:]

    if cmd == 'string':
        if cmd_args[0].isnumeric() or ',' in cmd_args[0]:
            # list of arguments to be passed to :meth:`toString`
            tsargs = cmd_args[0].split(',')
            tsargs[0] = int(tsargs[0]) if tsargs[0] else 0
        else:
            tsargs = []
        # get the component

        compo, path_str, prod = load_compo_at(1, paths[:-1], mInfo)
        if compo is not None:
            result = compo.toString(*tsargs)
            msg = 'Getting toString(%s) OK' % (str(tsargs))
            code = 200
            if 'html' in cmd_args:
                ct = 'text/html'
            elif 'fancy_grid' in cmd_args:
                ct = 'text/plain;charset=utf-8'
            else:
                ct = 'text/plain'
            return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
        else:
            return 400, FAILED, '%s: %s' % (cmd, path_str)
    elif cmd == '' and paths[-1] == '':
        # command is '' and url endswith a'/'
        compo, path_str, prod = load_compo_at(1, paths[:-1], mInfo)
        if compo:
            ls = [m for m in dir(compo) if not m.startswith('_')]
            return 0, resp(200, ls,
                           'Getting %s members OK' % (cmd + ':' + path_str),
                           ts, serialize_out=False), 0
        else:
            return 400, FAILED, '%s: %s' % (cmd, path_str)
    elif lp == 3:
        # url ends with index
        # no cmd, ex: test/fdi.dataset.Product/4
        # send json of the prod

        code, result, msg = load_product(1, paths, serialize_out=serialize_out)
        return 0, resp(code, result, msg, ts, serialize_out=serialize_out), 0
    elif 1:
        # no cmd, ex: test/fdi.dataset.Product/4
        # send json of the prod component
        compo, path_str, prod = load_compo_at(1, paths, mInfo)
        # see :func:`fetch`
        if compo or ' non ' not in path_str:
            return 0, resp(
                200, compo,
                'Getting %s OK' % (cmd + ':' + paths[2] + '/' + path_str),
                ts, serialize_out=False), 0
        else:
            return 400, FAILED, '%s : %s' % ('/'.join(paths[:3]), path_str)
    else:
        return 400, FAILED, 'Need index number %s' % str(paths)


def load_compo_at(pos, paths, mInfo):
    """ paths[pos] is cls; paths[pos+2] is 'description','meta' ...

    Components fetched are not in serialized form.
    """
    # component = fetch(paths[pos+2:], mInfo)
    # if component:

    # get the product live
    code, prod, msg=load_product(pos, paths, serialize_out = False)
    if code != 200:
        return None, '%s. Unable to load %s.' % (msg, str(paths)), None
    compo, path_str=fetch(paths[pos+2:], prod, exe=['*','is', 'get'])
    
    return compo, path_str, prod


def load_product(p, paths, serialize_out = False):
    """Load product paths[p]:paths[p+1] from paths[0]
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    typename=paths[p]
    indexstr=paths[p+1]
    poolname=paths[0]
    poolurl=poolurl_base + poolname
    urn=makeUrn(poolname = poolname, typename = typename, index = indexstr)
    # resourcetype = fullname(data)


    logger.debug('LOAD product: ' + urn)
    try:
        poolobj=PM.getPool(poolname = poolname, poolurl = poolurl)
        result=poolobj.loadProduct(urn = urn, serialize_out = serialize_out)
        msg=''
        code=200
    except Exception as e:
        if issubclass(e.__class__, NameError):
            msg = 'Not found: ' + poolname
            code = 404
        else:
            msg,code = '',400
        code, result, msg=excp(e, code=code,msg=msg,serialize_out = serialize_out)
    return code, result, msg


def load_HKdata(paths, serialize_out = True):
    """Load HKdata of a pool
    """

    hkname=paths[-1]
    poolname='/'.join(paths[0: -1])
    poolurl=poolurl_base + poolname
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
    poolurl = poolurl_base + poolname
    # resourcetype = fullname(data)

    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.readHK(hkname, serialize_out=serialize_out)
        code, msg = 200, 'OK'
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
    return code, result, msg


def setOwnerMode(p, username):
    """ makes UID and GID set to those of serveruser given in the config file. This function is usually done by the initPTS script.
    """

    logger.debug('set owner, group to %s, mode to 0o775' % username)

    uid, gid = getUidGid(username)
    if uid == -1 or gid == -1:
        return None
    try:
        os.chown(str(p), uid, gid)
        os.chmod(str(p), mode=0o775)
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='cannot set input/output dirs owner to ' +
            username + ' or mode. check config. ')
        logger.error(msg)
        return None

    return username


@auth.verify_password
def verify_password(username, password):
    logger.debug('verify user/pass %s %s vs. %s' % (
        username, password,
        str(current_app.config['USERS'])))
    if (username, password) in map(uspa, current_app.config['USERS']):
        return username

# import requests
# from http.client import HTTPConnection
# HTTPConnection.debuglevel = 1


# @auth.verify_password
# def verify(username, password):
#     """This function is called to check if a username /
#     password combination is valid.
#     """
#     if not (username and password):
#         return False
#     return username == pc['node']['username'] and password == pc['node']['password']
if 0:
    pass
    # elif username == pc['auth_user'] and password == pc['auth_pass']:

    # else:
    #     password = str2md5(password)
    #     try:
    #         conn = mysql.connector.connect(host = pc['mysql']['host'], port=pc['mysql']['port'], user =pc['mysql']['user'], password = pc['mysql']['password'], database = pc['mysql']['database'])
    #         if conn.is_connected():
    #             logger.info("connect to db successfully")
    #             cursor = conn.cursor()
    #             cursor.execute("SELECT * FROM userinfo WHERE userName = '" + username + "' AND password = '" + password + "';" )
    #             record = cursor.fetchall()
    #             if len(record) != 1:
    #                 logger.info("User : " + username + " auth failed")
    #                 conn.close()
    #                 return False
    #             else:
    #                 conn.close()
    #                 return True
    #         else:
    #             return False
    #     except Error as e:
    #         logger.error("Connect to database failed: " +str(e))


# API specification for this module
APIs = {
    'GET': {'func': 'get_pool_sn',
            'cmds': {'sn': ('Return the total count for the given product type and pool_id.', {
                'prod_type': 'clsssname',
                'pool_id': 'pool name'
            })},
            },
    'PUT': {'func': 'httppool',
            'cmds': {'pool': 'url'
                     }
            },
    'POST': {'func': 'httppool',
             'cmds': {'pool': 'url'
                      }
             },
    'DELETE': {'func': 'httppool',
               'cmds': {'pool': 'url'
                        }
               }


}

# @ app.route('/', methods=['GET'])
# @ httppool_api.route('/api', methods=['GET'])
# def get_apis():
#     """ Makes a page for APIs described in module variable APIs. """

#     logger.debug('APIs %s' % (APIs.keys()))
#     ts = time.time()
#     l = [(a, makepublicAPI(o)) for a, o in APIs.items()]
#     w = {'APIs': dict(l), 'timestamp': ts}
#     logger.debug('ret %s' % (str(w)[:100] + ' ...'))
#     return jsonify(w)


@httppool_api.errorhandler(400)
def bad_request(error):
    ts = time.time()
    w = {'error': 'Bad request.', 'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 400)


@httppool_api.errorhandler(401)
def unauthorized(error):
    ts = time.time()
    w = {'error': 'Unauthorized. Authentication needed to modify.',
         'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 401)


@httppool_api.errorhandler(404)
def not_found(error):
    ts = time.time()
    w = {'error': 'Not found.', 'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 404)


@httppool_api.errorhandler(409)
def conflict(error):
    ts = time.time()
    w = {'error': 'Conflict. Updating.',
         'message': str(error), 'timestamp': ts}
    return make_response(jsonify(w), 409)
