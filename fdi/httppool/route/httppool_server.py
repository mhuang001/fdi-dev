# -*- coding: utf-8 -*-

from .. import checkpath, PM_S
from ..model.user import auth

from ...dataset.deserialize import deserialize
from ...dataset.serializable import serialize
from ...dataset.mediawrapper import MediaWrapper
from ...pal.urn import makeUrn
from ...pal.poolmanager import PoolManager
from ...dataset.classes import Classes
from ...utils.common import (trbk,
                             getUidGid,
                             lls,
                             logging_ERROR,
                             logging_WARNING,
                             logging_INFO,
                             logging_DEBUG
                             )

from ...utils.fetch import fetch
from ...pns.fdi_requests import POST_PRODUCT_TAG_NAME

# from .db_utils import check_and_create_fdi_record_table, save_action

# import mysql.connector
# from mysql.connector import Error


from flask import request, make_response, Blueprint, current_app
from flask.wrappers import Response


import sys
import os
import time
import builtins
import importlib
import logging

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


# =============HTTP POOL=========================


def resp(code, result, msg, ts, serialize_out=False, ctype='application/json', length=80, req_auth=False):
    """
    Make response.

    :result: if is `Response`, this is returned req_auth applied.
    :ctype: Content-Type. Default is `application/json`
    :serialize_out: if True `result` is in already in serialized form.
    """

    # return if `result` is already a Response
    if issubclass(result.__class__, Response):
        resp = result
    else:
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

        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(lls(w, length))
            # logger.debug(pprint.pformat(w, depth=3, indent=4))

        resp = make_response(w, code)
        resp.headers['Content-Type'] = ctype

    if req_auth:
        resp.headers['WWW-Authenticate'] = 'Basic'
    return resp


def excp(e, code=400, msg='', serialize_out=True):
    # if current_app.config['DEBUG']:
    #    raise e
    result = '"FAILED"' if serialize_out else 'FAILED'
    msg = '%s\n%s: %s.\nTrace back: %s' % (
        msg, e.__class__.__name__, str(e), trbk(e))

    return code, result, msg


def check_readonly(usr, meth, logger):
    """ If both 'read_write' and 'read_only' present, 'read_write' has precedence.
    """
    return None
    if usr is None:
        msg = 'Unknown user %s.' % usr
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(msg)
        return msg, 401

    if meth in WRITE_LIST and ('read_only' in usr.roles) and ('read_write' not in usr.roles):
        msg = 'User %s is Read-Only, not allowed to %s.' % (usr.name, meth)
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(msg)
        return msg, 401

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


@ data_api.route('/urn<path:parts>/', methods=['DELETE'])
@ data_api.route('/urn<path:parts>', methods=['DELETE'])
@ auth.login_required(role='read_write')
def delete_urn(parts):
    """ Remove data item with the given URN (or URN parts).

    :parts: parts of a URN, consists of the pool ID, a data class type, and a serial number (a.k.a index number). e.g. ``urn:pool:fdi.dataset.baseproduct.BaseProduct:0``, ``/pool/fdi.dataset.baseproduct.BaseProduct/0``. Also possible URL: ``http.../urn:pool/fdi.dataset.product.Product/0``".
    """

    serial_through = True
    logger = current_app.logger

    ts = time.time()
    logger.info('delete data for URN parts ' + parts)

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

    if not PM_S.isLoaded(poolname):
        result = FAILED
        msg = 'Pool not found or not registered: ' + poolname
        code = 404
        logger.error(msg)
        return code, result, msg
    logger.debug('DELETE product urn: ' + urn)
    try:
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
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


@ data_api.route('/<string:pool>/', methods=['POST'])
@ data_api.route('/<string:pool>', methods=['POST'])
@ auth.login_required(role='read_write')
def save_data(pool):
    """
    Save data to the pool with a list of tags and receive URNs.

    Save product data item(s) to the pool with an optional set of tags (The same tags are given to every data item) and receive a URN for each of the saved items.
    """

    ts = time.time()
    logger = current_app.logger
    # logger.debug(f'save to ' + pool)

    # do not deserialize if set True. save directly to disk
    serial_through = True

    if not request.data:
        result, msg = '"FAILED"', 'No Request data for command '+request.method
        code = 400
        logger.warning(f'SAVE product to {pool} {msg}.')
        return resp(code, result, msg, ts, serialize_out=True)

    # save product
    if request.headers.get(POST_PRODUCT_TAG_NAME) is not None:
        tags = deserialize(request.headers.get(POST_PRODUCT_TAG_NAME))
    else:
        tags = None

    paths = [pool]
    # logger.debug('*** method:%s pool:%s tags:%s' %
    #             (request.method, pool, str(tags)))

    if serial_through:
        data = str(request.data, encoding='ascii')

        code, result, msg = save_product(
            data, paths, tags, serialize_in=not serial_through, serialize_out=serial_through, logger=logger)
    else:
        try:
            data = deserialize(request.data)
        except ValueError as e:
            code, result, msg = excp(
                e,
                msg='Class needs to be included in pool configuration.',
                serialize_out=serial_through)
            logger.info(f'SAVE product to {poolurl} {msg}.')
        else:
            code, result, msg = save_product(
                data, paths, tags, serialize_in=not serial_through, logger=logger)
            # save_action(username=username, action='SAVE', pool=paths[0])

    return resp(code, result, msg, ts, serialize_out=serial_through)


def save_product(data, paths, tags=None, serialize_in=True, serialize_out=False, logger=logger):
    """Save products and returns URNs.

    Saving Products to HTTPpool will have data stored on the server side. The server only returns URN strings as a response. ProductRefs will be generated by the associated httpclient pool which is the front-end on the user side.

    :tags: a list of tag strings. default is None meaning no tag.
    Returns a URN object or a list of URN objects.
    """
    FAILED = '"FAILED"' if serialize_out else 'FAILED'

    poolname = paths[0]
    fullpoolpath = os.path.join(
        current_app.config['FULL_BASE_LOCAL_POOLPATH'], poolname)
    poolurl = current_app.config['POOLURL_BASE'] + poolname
    # resourcetype = fullname(data)

    if checkpath(fullpoolpath, current_app.config['PC']['self_username']) is None:
        result = FAILED
        msg = 'Pool directory error: ' + fullpoolpath
        logger.info(f'SAVE product to {poolurl} {msg}.')
        return 400, result, msg

    # logger.debug(str(id(PM_S._GlobalPoolList)) + ' ' + str(PM_S._GlobalPoolList))

    try:
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.saveProduct(
            product=data, tag=tags, geturnobjs=True, serialize_in=serialize_in, serialize_out=serialize_out)
        # seriaized:'"urn:test_remote_pool:fdi.dataset.product.Product:0"'
        urn = result.split(poolname, 1)[1][1:-1] if serialize_out else result
        msg = f'Save {urn} to {poolurl} OK.'
        code = 200
        logger.info(msg)
    except Exception as e:
        code, result, msg = excp(e, serialize_out=serialize_out)
        logger.info(f'SAVE product to {poolurl} {msg}.')
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
    serial_through = True

    # do not deserialize if set True. save directly to disk

    paths = [pool] + parts2paths(data_paths)

    logger.debug('>>>[%4s] %s data_paths= %s paths= %s' %
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
            msg = 'Need a dot-separated full type name, not %s.' % pp
            code = 422
            logger.info(f'{code} {msg}')
            return code, '"FAILED"', msg
        modname, ptype = mp[0], mp[1]
        cls = Classes.mapping[ptype]
        mod = importlib.import_module(modname)  # TODO
        try:
            mInfo = getattr(mod, 'Model')
        except AttributeError:
            mInfo = cls().zInfo
        # non-serialized
        code = 200
        msg = 'Getting API info for %s OK' % paths[1]
        logger.info(f'{code} {msg}')
        return 0, resp(code, mInfo,  msg, ts, serialize_out=False), 0
    # elif lp == 3 and paths[-1]=='':

    #     try:
    #         poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
    #         result = poolobj.readHK(hkname, serialize_out=serialize_out)
    #         code, msg = 200, hkname + ' HK data returned OK'
    #     except Exception as e:
    #         code, result, msg = excp(e, serialize_out=serialize_out)
    elif lp >= 3:
        return get_component_or_method(paths, mInfo, serialize_out=serialize_out)

    else:
        __import__("pdb").set_trace()

        code = 400
        msg = 'Unknown path %s' % str(paths)
        logger.info(f'{code} {msg}')
        return code, '"FAILED"', msg


HTML_STYLE = """
<style>
table,th,td {
    border: 1px solid black;
    border-collapse: collapse;
}
tr:nth-child(even){
    background-color: #DFDFDF;
    color: black;
}
</style>
"""


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
        compo, path_str, prod = load_component_at(1, paths[:], mInfo)
        if compo is not None:
            ls = [m for m in dir(compo) if not m.startswith('_')]
            return 0, resp(200, ls, 'Getting %s members/attrbutes OK' % (path_str),
                           ts, serialize_out=False), 0
        else:
            return 400, FAILED, 'Cannot get %s for "%s".' % ('/'.join(paths[:-1]), path_str)
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
        # e.g. path_str is like '.string()' '["text"]'  '.meta["speed"].isValid()'
        if compo or 'has no' not in path_str:
            code = 200
            msg = f'Getting {path_str} OK'
            compo_meth_name = path_str.split('.')[-1]
            if compo_meth_name[:8] == 'toString' or \
               compo_meth_name[:6] == 'string' or \
               compo_meth_name[:3] == 'txt':
                if 'html' in compo_meth_name:
                    ct = 'text/html'
                    result = HTML_STYLE + compo
                elif 'rst' in compo_meth_name:
                    ct = 'text/plain;charset=utf-8'
                    result = compo
                elif 'fancy_grid' in compo_meth_name:
                    ct = 'text/plain;charset=utf-8'
                    result = compo
                else:
                    ct = 'text/plain'
                    result = compo
                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif compo_meth_name[:4] == 'html':
                ct = 'text/html'
                result = HTML_STYLE + compo
                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif compo_meth_name.startswith('yaml(') or compo_meth_name.startswith('tree('):
                ct = 'text/plain;charset=utf-8'
                # 'font-family: "Courier New",monospace;\n'
                result = compo
                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif compo_meth_name.startswith('fits('):
                ct = 'application/fits'
                result = compo
                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif issubclass(compo.__class__, MediaWrapper):
                ct = compo.type
                result = compo.data

                return 0, resp(code, result, msg, ts, ctype=ct, serialize_out=False), 0
            elif compo_meth_name.startswith('graph(') or \
                    compo_meth_name.startswith('getTaskHistory('):
                ct = 'image/png'
                result = compo
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
    """ paths[pos] is data_type; paths[pos+2] is 'description', 'meta' ...

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
    """Load product paths[p]: paths[p+1] from paths[0]
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
        poolobj = PM_S.getPool(poolname=poolname, poolurl=poolurl)
        result = poolobj.loadProduct(urn=urn, serialize_out=serialize_out)
        msg = ''
        code = 200
    except Exception as e:
        if issubclass(e.__class__, NameError):
            msg = 'Not found: ' + poolname
            code = 404
        else:
            __import__("pdb").set_trace()

            msg, code = '', 400
        code, result, msg = excp(
            e, code=code, msg=msg, serialize_out=serialize_out)
    return code, result, msg


Builtins = vars(builtins)


def mkv(v, t):
    """
    return v with a tyoe specified by t.

    t: 'NoneType' or any name in ``Builtins``.
    """

    m = v if t == 'str' else None if t == 'NoneType' else Builtins[t](
        v) if t in Builtins else deserialize(v)
    return m
