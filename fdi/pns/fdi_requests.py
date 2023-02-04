# -*- coding: utf-8 -*-

from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..dataset.classes import Class_Look_Up, All_Exceptions
from ..pal.urn import parseUrn, parse_poolurl
from ..utils.getconfig import getConfig
from ..utils.common import trbk
from ..pal.webapi import WebAPI
from .jsonio import auth_headers
from ..utils.common import (lls,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG
                            )

from urllib3.exceptions import NewConnectionError, ProtocolError
from requests.exceptions import ConnectionError
from flask import Flask
from flask.testing import FlaskClient

import requests
from itertools import chain
from requests.auth import HTTPBasicAuth
import asyncio
import aiohttp
from aiohttp.client_reqrep import ClientResponse

import functools
import logging
import sys
import json
from requests.auth import HTTPBasicAuth

from ..httppool.session import TIMEOUT, MAX_RETRY, FORCED, \
    requests_retry_session

session = requests_retry_session()

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    # strset = (str, unicode)
    strset = str
    from urlparse import urlparse

logger = logging.getLogger(__name__)
# logger.debug('level %d' % (logger.getEffectiveLevel()))


POST_PRODUCT_TAG_NAME = 'FDI-Product-Tags'

# all items
pcc = getConfig()
defaulturl = getConfig('poolurl:')

pccnode = pcc


@ functools.lru_cache(maxsize=16)
def getAuth(user, password):
    return HTTPBasicAuth(user, password)


@ functools.lru_cache(maxsize=64)
def urn2fdiurl(urn, poolurl, contents='product', method='GET'):
    """ Returns URL for accessing pools with a URN.

    See up-to-date HttpPool API UI at `http://<ip>:<port>/apidocs`.

    This is done by using the PoolURL.

    contents:
    'product' for returning a product from the pool.
    'hk' for returning the housekeeping data of the pool.
    'classes' for returning the class housekeeping data of the pool.
    'urns' for returning the URN housekeeping data of the pool.
    'tags' for returning the tag housekeeping data of the pool.

    method:
    'GET' compo for retrieving product or hk or classes, urns, tags,
    'POST' compo for uploading  product
    'PUT' for registering pool
    'DELETE' compo for removing product or removing pool

    Example:
    IP=ip poolpath=/a poolname=b files=/a/b/classes.jsn | urns.jsn | t.. | urn...

    with python:
    m.refs['myinput'] = special_ref
    ref=pstore.save(m)
    assert ref.urn == 'urn:b:fdi.dataset.MapContext:203'
    p=ref.product
    myref=p.refs['myinput']

    with a pool:
    myref=pool.load('http://ip:port/v0.6/b/fdi.dataset.MapContext/203/refs/myinput')

    """

    poolname, resourcecn, index = parseUrn(
        urn) if urn and (len(urn) > 7) else ('', '', '0')
    indexs = str(index)
    poolpath, scheme, place, pn, un, pw = parse_poolurl(
        poolurl, poolhint=poolname)

    if not poolname:
        poolname = pn
    # with a trailing '/'
    baseurl = poolurl[:-len(poolname)]
    if method == 'GET':
        if contents == 'product':
            ret = poolurl + '/' + resourcecn + '/' + indexs
        elif contents == 'registered_pools':
            ret = baseurl
        elif contents == 'pools_info':
            ret = baseurl + 'pools/'
        elif contents == 'pool_info':
            ret = poolurl + '/'
        elif contents == 'count':
            ret = poolurl + '/count/' + resourcecn
        elif contents == 'pool_api':
            ret = poolurl + '/api/'
        elif contents == 'housekeeping':
            ret = poolurl + '/hk/'
        elif contents in ['classes', 'urns', 'tags']:
            ret = poolurl + '/hk/' + contents
        elif contents.split('__', 1)[0] in WebAPI:
            # append a '/' for flask
            ret = poolurl + '/api/' + contents + '/'
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    elif method == 'POST':
        if contents == 'product':
            ret = baseurl + poolname + '/'
        elif contents.split('__', 1)[0] in WebAPI:
            # append a '/' for flask
            ret = poolurl + '/api/' + contents.split('__', 1)[0] + '/'
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    elif method == 'PUT':
        if contents == 'register_pool':
            ret = poolurl
        elif contents == 'register_all_pool':
            ret = baseurl + 'pools/register_all'
        elif contents == 'unregister_all_pool':
            ret = baseurl + 'pools/unregister_all'
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    elif method == 'DELETE':
        if contents == 'wipe_pool':
            ret = poolurl + '/wipe'
        elif contents == 'wipe_all_pools':
            ret = baseurl + 'wipe_all'
        elif contents == 'unregister_pool':
            ret = poolurl
        elif contents == 'product':
            ret = baseurl + 'urn' + urn
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    else:
        raise ValueError(method)
    return ret

# Store tag in headers, maybe that's  not a good idea


def safe_client(method, api, *args, no_retry_controls=True, **kwds):
    """ call Session/requests method with or without try controls.

    Parameters
    ----------
    method: function
         urllib3 Session or requests function such as `get`.
    no_retry_controls: bool
         without retry controls. Default `True`.

    Returns
    -------
    Response
       Of urllib3 Session or requests Response.
"""
    if no_retry_controls:
        return method(api, *args, **kwds)

    for n in range(MAX_RETRY):
        try:
            res = method(api, *args, **kwds)
            if res.status_code not in FORCED:
                break
        except ConnectionError as e:
            if isinstance(e.__context__, ProtocolError):
                pass
            else:
                cause = e.__context__.reason
                if isinstance(cause, NewConnectionError):
                    raise cause
    # print(n, res)
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(
            f'Resp {n} retries, hist:{res.history}, {getattr(res.request,"path","")} {method.__func__.__qualname__}')

    return res


def post_to_server(data, urn, poolurl, contents='product', headers=None,
                   no_serial=False, result_only=False, auth=None, client=None):
    """Post data to server with  tag in headers

    data: goes to the request body
    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter that must be provided
    contents: type of request. Default 'api'.
    headers: request header dictionary. Default `None` using `jsonio.auth_headers()`.
    no_serial: do not serialize the data.
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc.
    """

    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    api = urn2fdiurl(urn, poolurl, contents=contents, method='POST')
    if client is None:
        client = session
    # from fdi.utils.common import lls
    # print('POST API: ' + api + ' | ' + lls(data, 900))
    if headers is None:
        headers = auth_headers(auth.username, auth.password)
    sd = data if no_serial else serialize(data)
    res = safe_client(client.post, api, auth=auth, data=sd,
                      headers=headers, timeout=TIMEOUT)

    if result_only:
        return res
    result = deserialize(res.text)
    if issubclass(result.__class__, dict):
        return res.status_code, result['result'], result['msg']
    else:
        return res.status_code, 'FAILED', result


def save_to_server(data, urn, poolurl, tag, no_serial=False, auth=None, client=None):
    """Save product to server with putting tag in headers

    data: goes to the request body
    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    tag: go with the products into the pool
    no_serial: do not serialize the data.
    client: alternative client to answer API calls. For tests etc.

    Return
    The `Response` result.
    """
    headers = {POST_PRODUCT_TAG_NAME: serialize(tag)}
    res = post_to_server(data, urn, poolurl, contents='product',
                         headers=headers, no_serial=no_serial,
                         result_only=True,
                         auth=auth, client=client)
    return res
    # auth = getAuth(pccnode['username'], pccnode['password'])
    # api = urn2fdiurl(urn, poolurl, contents='product', method='POST')
    # # print('POST API: ' + api)
    # headers = {'tags': tag}
    # sd = data if no_serial else serialize(data)
    # res = client.post(
    #     api, auth=auth, data=sd, headers=headers)
    # # print(res)
    # return res


def read_from_server(urn, poolurl, contents='product', result_only=False, auth=None, client=None):
    """Read product or hk data from server

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc.
    """

    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session
    api = urn2fdiurl(urn, poolurl, contents=contents)
    # print("GET REQUEST API: " + api)
    res = safe_client(client.get, api, auth=auth, timeout=TIMEOUT)

    if result_only:
        return res
    result = deserialize(res.text if type(res) == requests.models.Response
                         else res.data)
    if issubclass(result.__class__, dict):
        return res.status_code, result['result'], result['msg']
    else:
        return res.status_code, 'FAILED', result


def put_on_server(urn, poolurl, contents='pool', result_only=False, auth=None, client=None):
    """Register the pool on the server.

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc. Default None for `requests`.
    """

    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session
    api = urn2fdiurl(urn, poolurl, contents=contents, method='PUT')
    # print("PUT REQUEST API: " + api)
    if 0 and not issubclass(client.__class__, FlaskClient):
        print('######', client.cookies.get('session', None))
    res = reqst(client.put, api, auth=auth, timeout=TIMEOUT)
    if result_only:
        return res
    result = deserialize(res.text if type(res) == requests.models.Response
                         else res.data)
    if 0:
        if not issubclass(client.__class__, FlaskClient):
            print('@@@@@@', client.cookies['session'])
        else:
            print('@@@@@@', res.request.cookies.get('session', None))

    if issubclass(result.__class__, dict):
        return result['result'], result['msg']
    else:
        return 'FAILED', result


def delete_from_server(urn, poolurl, contents='product', result_only=False, auth=None, client=None, asyn=False):
    """Remove a product or pool from server

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc. Default None for `requests`.
    """

    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session

    if asyn:
        apis = [poolurl+'/'+u for u in urn]
        res = reqst('delete', apis=apis, **kwds)
    else:
        api = urn2fdiurl(urn, poolurl, contents=contents, method='DELETE')
        # print("DELETE REQUEST API: " + api)
        res = reqst(client.delete, api, auth=auth, timeout=TIMEOUT)

    if result_only:
        return res
    result = deserialize(res.text if type(res) == requests.models.Response
                         else res.data)
    if issubclass(result.__class__, dict):
        return result['result'], result['msg']
    else:
        return 'FAILED', result


# == == == = Async IO == == ==
def content2result_httppool(content):
    res = []
    for resp in content:
        if isinstance(resp, tuple):
            code, text, url = resp  # .status, resp.text(), resp.url.raw_path_qs
        else:
            code, text, url = resp.status_code, resp.text, resp.url
        obj = deserialize(text)
        ores = obj['result']
        if code != 200 or issubclass(ores.__class__, str) and ores[:6] == 'FAILED':
            if not issubclass(obj.__class__, dict):
                # cannot deserialize
                raise RuntimeError(
                    f'AIO {method_name} error SERVER: {code} Message: '+lls(text, 200))
            # deserializable
            msg = obj['msg']
            for line in chain(msg.split('.', 1)[:1], msg.split('\n')):
                excpt = line.split(':', 1)[0]
                if excpt in All_Exceptions:
                    # relay the exception from server
                    raise All_Exceptions[excpt](
                        f'SERVER: Code {code} Message: {msg}***{res}={len(res)}')
            raise RuntimeError(
                f'AIO {method_name} error SERVER: {ores}: '+lls(msg, 200))
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(lls(text, 100))
        res.append(ores)

    # print('pppp', res[0])
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'AIO result size: {len(res)}.')
    return res


def content2result_csdb(content):
    res = []
    for resp in content:
        if isinstance(resp, tuple):
            code, text, url = resp  # .status, resp.text(), resp.url.raw_path_qs
        else:
            code, text, url = resp.status_code, resp.text, resp.url
        obj = deserialize(text)
        if code != 200 or not issubclass(obj.__class__, dict):
            # cannot deserialize
            raise RuntimeError(
                f'AIO {method_name} error: {code} Message: '+lls(text, 200))
        # deserializable
        msg = obj['msg']
        ores = obj['data']
        code = obj['code']
        if code:
            raise RuntimeError(
                f'Code {code} Message: {msg}***{lls(text, 200)}={len(text)}')
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(lls(text, 100))
        res.append(ores)

    # print('pppp', res[0])
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'AIO result size: {len(res)}.')
    return res


async def get_aio_result(method, *args, **kwds):
    async with method(*args, **kwds) as resp:
        # print(type(resp),dir(resp))
        con = await resp.text()
        return resp.status, con, resp.url.raw_path_qs


def reqst(method, apis, *args, server_type='httppool', **kwds):
    """send session, requests, aiohttp requests.

    Parameters
    ----------
    method : str, function
        If is a string, will be the method name of `aio_client`,
        `aio_client` is used so
        at least one of the `apis`, 'data' in `kwds`, and `headers`
        is expected to be a `list` or `tuple`.

        If is a function, the method functiono of
        session/request is used and apis is expected to be a string.
    apis : str, list, tuple
        The URL string if `method` is a function. A list of URL strings
        if `method` is a string. See `method` docs above.
    *args : list

    **kwds : dict


    Returns
    -------
    list
        list of deserialized response.text if `aio_client` is used,
        a response object or error message if `safe_client` is used.

    Examples
    --------
    FIXME: Add docs.
    """

    if isinstance(method, str):
        content = aio_client(method, apis, *args, **kwds)
        if server_type == 'httppool':
            res = content2result_httppool(content)
        elif server_type == 'csdb':
            res = content2result_csdb(content)
        else:
            raise ValueError('Unknown server type: {server_type}.')
    else:
        content = safe_client(method, apis, *args, **kwds)
        res = content

    return res


def aio_client(method_name, apis, data=None, headers=None):
    """
    Parameters
    ----------
    method: str
         name ofurllib3 Session or requests function such as `"get"`.
    no_retry_controls: bool
         without retry controls. Default `True`.

    Returns
    -------
    list
       List if urllib3 Session or requests Response.
    """

    cnt = 0
    method_name = method_name.lower()
    alist = issubclass(apis.__class__, (list, tuple))
    dlist = issubclass(data.__class__, (list, tuple))
    hlist = issubclass(headers.__class__, (list, tuple))
    if alist:
        cnt = len(apis)
    elif dlist:
        cnt = len(data)
    elif hlist:
        cnt = len(headers)
    else:
        raise TypeError('None of the parameters is a list or a tuple.')

    async def multi():
        aio_session = aiohttp.ClientSession()
        async with aio_session as session:
            tasks = []
            method = getattr(session, method_name)
            for n in range(cnt):
                a = apis[n] if alist else apis
                d = data[n] if dlist else data
                h = headers[n] if hlist else headers
                if method_name == 'post':
                    tasks.append(asyncio.ensure_future(
                        get_aio_result(method, a, data=d, headers=h)))
                elif method_name in ('get', 'delete'):
                    tasks.append(asyncio.ensure_future(
                        get_aio_result(method, a, headers=h)))
                else:
                    raise ValueError(f"Unknown AIO method {method_name}.")
            content = await asyncio.gather(*tasks)

            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(f'AIO {method_name} return {len(content)} items')

            return content

    res = asyncio.run(multi())
    return res


@ functools.lru_cache(maxsize=256)
def cached_json_dumps(cls_full_name, ensure_ascii=True, indent=2):
    # XXX add Model to Class
    obj = Class_Look_Up[cls_full_name.rsplit('.', 1)[-1]]()
    return json.dumps(obj.zInfo, ensure_ascii=ensure_ascii, indent=indent)


def getCacheInfo():
    info = {}
    for i in ['getAuth', 'urn2fdiurl']:
        info[i] = i.cache_info()

    return info
