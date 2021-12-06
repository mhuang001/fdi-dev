# -*- coding: utf-8 -*-

from ..model.user import getUsers, auth

from ...utils.common import lls
from ...dataset.deserialize import deserialize, deserialize_args
from ...dataset.serializable import serialize
from ...dataset.mediawrapper import MediaWrapper
from ...pal.urn import makeUrn
from ...dataset.classes import Classes
from ...utils.common import trbk, getUidGid
from ...utils.fetch import fetch
from ...pal.poolmanager import PoolManager as PM, DEFAULT_MEM_POOL

# from .db_utils import check_and_create_fdi_record_table, save_action

# import mysql.connector
# from mysql.connector import Error

from flasgger import swag_from

from flask import request, make_response, jsonify, Blueprint, current_app
from flask.wrappers import Response


import sys
import os
import time
import builtins
import functools
from pathlib import Path
import importlib

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    # strset = (str, unicode)
    strset = str
    from urlparse import urlparse


# Global variables set to temprary values before setGlabals() runs
logger = __import__('logging').getLogger(__name__)

data_api = Blueprint('httppool_server', __name__)

WRITE_LIST = ['POST', 'PUT', 'DELETE', 'PATCH']


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
        logger.info('Cannot set owner %s to %s.' % (un, str(p)))
        return None

    logger.debug('checked path at ' + str(p))
    return p


# =============HTTP POOL=========================

# @data_api.before_app_first_request


def resp(code, result, msg, ts, serialize_out=False, ctype='application/json', length=80, req_auth=False):
    """
    Make response.

    :ctype: Content-Type. Default is `application/json`
    :serialize_out: if True `result` is in already in serialized form.
    """
    # return if `result` is already a Response
    if issubclass(result.__class__, Response):
        return result
    if ctype == 'application/json':
        if serialize_out:
            # result is already in serialized form
            p = 'no-serialization-result-place-holder'
            t = serialize({"result": p, "msg": msg, "time": ts})
            w = t.replace('"'+p+'"', result)
        else:
            w = serialize({"result": result, "msg": msg, "time": ts})
    else:
        w = result

    logger.debug(lls(w, length))
    # logger.debug(pprint.pformat(w, depth=3, indent=4))
    resp = make_response(w, code)
    resp.headers['Content-Type'] = ctype

    if req_auth:
        resp.headers['WWW-Authenticate'] = 'Basic'
    return resp


def excp(e, code=400, msg='', serialize_out=True):
    result = '"FAILED"' if serialize_out else 'FAILED'
    msg = '%s\n%s: %s.\nTrace back: %s' % (
        msg, e.__class__.__name__, str(e), trbk(e))

    return code, result, msg


def check_readonly(usr, meth, logger):
    return None
    if usr is None:
        msg = 'Unknown user %s.' % usr
        logger.debug(msg)
        return unauthorized(msg)

    if meth in WRITE_LIST and usr.role == 'read_only':
        msg = 'User %s is Read-Only, not allowed to %s.' % (usr.name, meth)
        logger.debug(msg)
        return unauthorized(msg)

    return None


######################################
####  /urn{parts} get data ####
######################################


@ data_api.route('/urn<path:parts>', methods=['GET'])
@ auth.login_required
def urn(parts):
    """ Return data item from the given URN.

    :parts: parts of a URN, consists of the pool ID, a data class type, and a serial number (a.k.a index number). e.g. ``urn:pool:fdi.dataset.baseproduct.BaseProduct:0``, ``/pool/fdi.dataset.baseproduct.BaseProduct/0``. Also possible URL: ``http.../urn:pool/fdi.dataset.product.Product/0``".
    """

    serial_through = True
    logger = current_app.logger

    ts = time.time()
    logger.debug('get data for URN parts ' + parts)

    paths = parts2paths(parts)
    # if paths[-1] == '':
    #    del paths[-1]

    code, result, msg = getProduct_Or_Component(
        paths, serialize_out=serial_through)
    return resp(code, result, msg, ts, serialize_out=serial_through)

######################################
####  /urn{parts} remove data ####
######################################


@ data_api.route('/urn<path:parts>', methods=['DELETE'])
@ auth.login_required(role='read_write')
def delete_urn(parts):
    """ Remove data item with the given URN (or URN parts).

    :parts: parts of a URN, consists of the pool ID, a data class type, and a serial number (a.k.a index number). e.g. ``urn:pool:fdi.dataset.baseproduct.BaseProduct:0``, ``/pool/fdi.dataset.baseproduct.BaseProduct/0``. Also possible URL: ``http.../urn:pool/fdi.dataset.product.Product/0``".
    """

    serial_through = True
    logger = current_app.logger

    ts = time.time()
    logger.debug('get data for URN parts ' + parts)

    paths = parts2paths(parts)
    # if paths[-1] == '':
    #    del paths[-1]

    code, result, msg = delete_product(paths, serialize_out=False)
    return resp(code, result, msg, ts, serialize_out=False)


def parts2paths(parts):
    # parts == urn:{type}:{index}/...
    # parts == /urn:{type}:{index}/...
    # parts == :{type}:{index}/...
    # parts == /{type}:{index}/...
    # parts == /{type}/{index}/...
    if parts[:4].lower() == 'urn:':
        parts = parts[4:]
    elif parts[:5].lower() == '/urn:':
        parts = parts[5:]
    elif parts[0] == '/' or parts[0] == ':':
        parts = parts[1:]
    # deal with the possible ':' before index
    sp1 = parts.split('/')
    if ':' in sp1[0]:
        paths = sp1[0].split(':') + sp1[1:]
    else:
        paths = sp1
    return paths


def delete_product(paths, serialize_out=False):
    """ removes specified product from pool
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    typename = paths[1]
    indexstr = paths[2]
    poolname = paths[0]
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    urn = makeUrn(poolname=poolname, typename=typename, index=indexstr)
    # resourcetype = fullname(data)

    if not PM.isLoaded(poolname):
        result = FAILED
        msg = 'Pool not found or not registered: ' + poolname
        code = 400
        logger.error(msg)
        return code, result, msg
    logger.debug('DELETE product urn: ' + urn)
    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        poolobj.remove(urn)
        result = 0
        msg = 'remove product ' + urn + ' OK.'
        code = 200
    except Exception as e:
        code, result, msg = excp(
            e,
            msg='Unable to remove product: ' + urn)
        logger.error(msg)
    return code, result, msg

######################################
####  {pool}/ POST   ####
######################################


# @ data_api.route('/<string:pool>', methods=['POST'])
@ data_api.route('/<string:pool>/', methods=['POST'])
@ auth.login_required(role='read_write')
def save_data(pool):
    """
    Save data to the pool with a list of tags and receive URNs.

    Save product data item(s) to the pool with an optional set of tags (The same tags are given to every data item) and receive a URN for each of the saved items.
    """

    ts = time.time()
    logger = current_app.logger
    logger.debug(f'save to ' + pool)

    # do not deserialize if set True. save directly to disk
    serial_through = True

    if request.data is None:
        result, msg = '"FAILED"', 'No REquest data for command '+request.method
        code = 404
        return resp(code, result, msg, ts, serialize_out=True)

    # save product
    if request.headers.get('tags') is not None:
        tags = request.headers.get('tags').split(',')
    else:
        tags = None

    paths = [pool]
    logger.debug('*** method %s pool %s tags %s' %
                 (request.method, pool, str(tags)))

    if serial_through:
        data = str(request.data, encoding='ascii')

        code, result, msg = save_product(
            data, paths, tags, serialize_in=not serial_through, serialize_out=serial_through)
    else:
        try:
            data = deserialize(request.data)
        except ValueError as e:
            code, result, msg = excp(
                e,
                msg='Class needs to be included in pool configuration.',
                serialize_out=serial_through)
        else:
            code, result, msg = save_product(
                data, paths, tags, serialize_in=not serial_through)
            # save_action(username=username, action='SAVE', pool=paths[0])

    return resp(code, result, msg, ts, serialize_out=serial_through)


def save_product(data, paths, tags=None, serialize_in=True, serialize_out=False):
    """Save products and returns URNs.

    Saving Products to HTTPpool will have data stored on the server side. The server only returns URN strings as a response. ProductRefs will be generated by the associated httpclient pool which is the front-end on the user side.

    :tags: a list off tag strings. default is None meaning no tag.
    Returns a URN object or a list of URN objects.
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    poolname = paths[0]
    fullpoolpath = os.path.join(current_app.config['POOLPATH_BASE'], poolname)
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    # resourcetype = fullname(data)
    tag = tags[0] if tags else None  # TODO: accept all tags

    if checkpath(fullpoolpath, current_app.config['PC']['serveruser']) is None:
        result = FAILED
        msg = 'Pool directory error: ' + fullpoolpath
        return 400, result, msg

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

######################################
####  {pool}/{data_paths}  GET  ####
######################################


@ data_api.route('/<string:pool>/<path:data_paths>', methods=['GET'])
@ auth.login_required(role='read_write')
def data_paths(pool, data_paths):
    """
    Returns magics of given type/data in the given pool.


    """

    ts = time.time()
    logger = current_app.logger
    logger.debug(f'datapath of ' + pool)

    logger = current_app.logger

    # do not deserialize if set True. save directly to disk
    serial_through = True

    paths = [pool] + parts2paths(data_paths)

    logger.debug('*** method= %s pool= %s data_paths= %s paths= %s' %
                 (request.method, pool, str(data_paths), str(paths)))

    code, result, msg = getProduct_Or_Component(
        paths, serialize_out=serial_through)
    return resp(code, result, msg, ts, serialize_out=serial_through)


def getProduct_Or_Component(paths, serialize_out=False):
    """
    :serialize_out: see :meth:`ProductPool.saveProduct`
    """

    lp = len(paths)
    # now paths = poolname, prod_type , ...
    logger.debug('get prod or compo: ' + str(paths))

    ts = time.time()
    mInfo = 0
    if lp == 2:
        # ex: pool/fdi.dataset.Product
        # return classes[class]
        pp = paths[1]
        mp = pp.rsplit('.', 1)
        if len(mp) < 2:
            return 422, '"FAILED"', 'Need a dot-separated full type name, not %s.' % pp
        modname, ptype = mp[0], mp[1]
        cls = Classes.mapping[ptype]
        mod = importlib.import_module(modname)  # TODO
        try:
            mInfo = getattr(mod, 'Model')
        except AttributeError:
            mInfo = cls().zInfo
        # non-serialized
        return 0, resp(200, mInfo,
                       'Getting API info for %s OK' % paths[1],
                       ts, serialize_out=False), 0
    # elif lp == 3 and paths[-1]=='':

    #     try:
    #         poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
    #         result = poolobj.readHK(hkname, serialize_out=serialize_out)
    #         code, msg = 200, hkname + ' HK data returned OK'
    #     except Exception as e:
    #         code, result, msg = excp(e, serialize_out=serialize_out)
    elif lp >= 3:
        return get_component_or_method(paths, mInfo, serialize_out=serialize_out)

    else:
        return 400, '"FAILED"', 'Unknown path %s' % str(paths)


def get_component_or_method(paths, mInfo, serialize_out=False):
    """ Get the component and the associated command and return

    Except for full products, most components  are not in serialized form.
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'
    ts = time.time()
    logger.debug('get compo or meth: ' + str(paths))
    lp = len(paths)
    # if paths[-1] in ('toString', 'string'):
    #    __import__('pdb').set_trace()

    if paths[-1] == '':
        # command is '' and url endswith a'/'
        compo, path_str, prod = load_component_at(1, paths[:-1], mInfo)
        if compo:
            ls = [m for m in dir(compo) if not m.startswith('_')]
            return 0, resp(200, ls, 'Getting %s members/attrbutes OK' % (path_str),
                           ts, serialize_out=False), 0
        else:
            return 400, FAILED, '%s' % (path_str)
    elif lp == 3:
        # url ends with index
        # no cmd, ex: test/fdi.dataset.Product/4
        # send json of the prod

        code, result, msg = load_product(1, paths, serialize_out=serialize_out)
        return 0, resp(code, result, msg, ts, serialize_out=serialize_out), 0
    elif paths[2].isnumeric():
        # grand tour
        compo, path_str, prod = load_component_at(1, paths, mInfo)
        # see :func:`fetch`
        if compo or 'has no' not in path_str:
            code = 200
            msg = f'Getting {path_str} OK'
            compo_meth_name = path_str.split('.')[-1]
            if compo_meth_name[:8] == 'toString' or \
               compo_meth_name[:6] == 'string':
                if 'html' in compo_meth_name:
                    ct = 'text/html'
                elif 'fancy_grid' in compo_meth_name:
                    ct = 'text/plain;charset=utf-8'
                else:
                    ct = 'text/plain'
                result = compo
                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif compo_meth_name == 'yaml()':
                ct = 'text/plain;charset=utf-8'
                result = compo
                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif issubclass(compo.__class__, MediaWrapper):
                ct = compo.type
                result = compo.data

                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            else:
                return 0, resp(code, compo, msg, ts, serialize_out=False), 0

        else:
            return 400, FAILED, '%s: %s' % (str(paths), path_str)

    elif 0:
        # no cmd, ex: test/fdi.dataset.Product/4
        # send json of the prod component
        compo, path_str, prod = load_component_at(1, paths, mInfo)
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


def load_component_at(pos, paths, mInfo):
    """ paths[pos] is data_type; paths[pos+2] is 'description','meta' ...

    Components fetched are not in serialized form.
    """
    # component = fetch(paths[pos+2:], mInfo)
    # if component:

    # get the product live
    code, live_prod, msg = load_product(pos, paths, serialize_out=False)
    if code != 200:
        return None, '%s. Unable to load %s.' % (msg, str(paths)), None
    compo, path_str = fetch(paths[pos+2:], live_prod,
                            exe=['*', 'is', 'get'], not_quoted=False)

    return compo, path_str, live_prod


def load_product(p, paths, serialize_out=False):
    """Load product paths[p]:paths[p+1] from paths[0]
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    typename = paths[p]
    indexstr = paths[p+1]
    poolname = paths[0]
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    urn = makeUrn(poolname=poolname, typename=typename, index=indexstr)
    # resourcetype = fullname(data)

    logger.debug('LOAD product: ' + urn)
    try:
        poolobj = PM.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.loadProduct(urn=urn, serialize_out=serialize_out)
        msg = ''
        code = 200
    except Exception as e:
        if issubclass(e.__class__, NameError):
            msg = 'Not found: ' + poolname
            code = 404
        else:
            msg, code = '', 400
        code, result, msg = excp(
            e, code=code, msg=msg, serialize_out=serialize_out)
    return code, result, msg


def setOwnerMode(p, username):
    """ makes UID and GID set to those of serveruser given in the config file. This function is usually done by the initPTS script.
    """

    logger.debug('set owner, group to %s, mode to 0o775' % username)

    uid, gid = getUidGid(username)
    if uid == -1 or gid == -1:
        logger.debug(f'user {username} uid={uid} gid{gid}')
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


Builtins = vars(builtins)


def mkv(v, t):
    """
    return v with a tyoe specified by t.

    t: 'NoneType' or any name in ``Builtins``.
    """

    m = v if t == 'str' else None if t == 'NoneType' else Builtins[t](
        v) if t in Builtins else deserialize(v)
    return m
