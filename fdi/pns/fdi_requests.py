# -*- coding: utf-8 -*-

from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..dataset.classes import Class_Look_Up, All_Exceptions
from ..pal.urn import parseUrn, parse_poolurl
from ..utils.getconfig import getConfig
from ..utils.common import trbk
from ..utils.tofits import is_Fits
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
from inspect import ismethod
from itertools import chain
from requests.auth import HTTPBasicAuth
import asyncio
import aiohttp
from aiohttp.client_reqrep import ClientResponse
from aiohttp import ClientTimeout
from aiohttp_retry import RetryClient
from aiohttp_retry import (
    ExponentialRetry,
    FibonacciRetry,
    JitterRetry,
    ListRetry,
    RandomRetry,
)

import functools
import logging
import sys
import json
from requests.auth import HTTPBasicAuth

from ..httppool.session import TIMEOUT, MAX_RETRIES, FORCED, \
    requests_retry_session

session = requests_retry_session()

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:  # indent
    PY3 = False
    # strset = (str, unicode)
    strset = str
    from urlparse import urlparse

logger = logging.getLogger(__name__)
# logger.debug('level %d' % (logger.getEffectiveLevel()))


POST_PRODUCT_TAG_NAME = 'FDI-Product-Tags'

SAFE_CLIENT_OUT = 0
""" logger.info all url going out."""

SHOW_REQ_SENT = 0

# all items
pcc = getConfig()
defaulturl = getConfig('poolurl:')

AIO_TIMEOUT = ClientTimeout(total=5*10, connect=3,
                                 sock_connect=5, sock_read=10)

pccnode = pcc

aio_session = None
""" the async io session for this app """


class ServerError(Exception):
    def __init__(self, r, *args, rsps=None, code=None, **kwds):
        """An Exception that carries response and code that are passed to it.

        Parameters
        ----------
        r : str
            Error message.
        rsps : Response
            The Response or equivalent object to be passed.
        code : int_info
            Error code to be passed.
        args: list
            To be passed to superclass `__init__`.
        kwds: dict
            To be passed to superclass `__init__`.
        
        Returns
        -------
        
        """

        self.response = rsps
        if code is None:
            self.code = rsps.getapis(
                'status_code', rsps.getattr('status', '')) if rsps else None
        else:
            self.code = code
        return super().__init__(r, *args, **kwds)


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
    'DELETE' compo for removing product or unregistering pool

    Example:
    IP=ip poolpath=/a poolname=b files=/a/b/classes.jsn | urns.jsn | t.. | urn...

    .. code-block::

        m.refs['myinput'] = special_ref
        ref=pstore.save(m)
        assert ref.urn == 'urn:b:fdi.dataset.MapContext:203'
        p=ref.product
        myref=p.refs['myinput']

        # with a pool:
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


def safe_client(method, api, *args, headers=None, no_retry_controls=False, **kwds):
    """ call Session/requests method with or without try controls.

    Parameters
    ----------
    method: function
         urllib3 Session or requests function such as `get`.
    no_retry_controls: bool
         without retry controls. Default `False`.

    Returns
    -------
    Response
       Of urllib3 Session or requests Response.
"""
    if SAFE_CLIENT_OUT:
        logger.info(
            lls(f'{method.__func__.__name__} {api} arg={args} kwds={kwds}', 200))

    if no_retry_controls or MAX_RETRIES == 0:
        return method(api, *args, headers=headers, **kwds)

    tries = int(MAX_RETRIES/ session.adapters['http://'].max_retries.total + 0.5)
    err = []
    res = None
    for n in range(tries):
        try:
            if SHOW_REQ_SENT:
                __import__("pdb").set_trace()
                api = 'https://httpbin.org/delete'

            res = method(api, *args, **kwds)
            if FORCED is None or res.status_code not in FORCED:
                break
        except ConnectionError as e:
            err.append(e)
            if isinstance(e.__context__, ProtocolError):
                pass
            else:
                cause = e.__context__.reason
                if isinstance(cause, NewConnectionError):
                    raise cause
            res = None
    # print(n, res)

    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(
            f'Resp {n} retries' +
            f', hist:{res.history}, {getattr(res.request,"path","")} {method.__func__.__qualname__}'
            if res else ' failed.')

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
        if client and getattr(client, 'auth', '') and client.auth:
            auth = client.auth
        else:
            auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session
    client.auth = auth

    api = urn2fdiurl(urn, poolurl, contents=contents, method='POST')

    # from fdi.utils.common import lls
    if logger.isEnabledFor(logging_DEBUG):
        print('POST API: ' + api + ' | ' + lls(data, 90))

    aheaders = auth_headers(auth.username, auth.password)
    if headers :
        aheaders.update(headers)
    headers = aheaders
        
    if 0:
        __import__("pdb").set_trace()
        api = 'https://httpbin.org/post'
        
    sd = data if no_serial else serialize(data)
    if isinstance(client, FlaskClient):
        res = safe_client(client.post, api, auth=auth, data=sd,
                          headers=headers)
    else:
        res = safe_client(client.post, api, auth=auth, data=sd,
                          headers=headers, timeout=TIMEOUT)

    if result_only:
        return res
    
    result = deserialize(res.text)
    if issubclass(result.__class__, dict):
        return res.status_code, result['result'], result['msg']
    else:
        return res.status_code, 'FAILED', result


def save_to_server(data, urn, poolurl, tag, headers=None, no_serial=False, auth=None, client=None):
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
    aheaders = {POST_PRODUCT_TAG_NAME: serialize(tag)}
    if headers :
        aheaders.update(headers)
    headers = aheaders
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


def read_from_server(urn, poolurl, contents='product', headers=None, result_only=False, auth=None, client=None):
    """Read product or hk data from server

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc.
    """

    if auth is None:
        if client and getattr(client, 'auth', '') and client.auth:
            auth = client.auth
        else:
            auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session
    client.auth = auth
    api = urn2fdiurl(urn, poolurl, contents=contents)
    if logger.isEnabledFor(logging_DEBUG):
        print("GET REQUEST API: " + api)

    aheaders = auth_headers(auth.username, auth.password)
    if headers :
        aheaders.update(headers)
    headers = aheaders

    if SHOW_REQ_SENT:
        __import__("pdb").set_trace()
        api = 'https://httpbin.org/get'
        
    if isinstance(client, FlaskClient):
        res = safe_client(client.get, api, headers=headers, auth=auth)
    else:
        res = safe_client(client.get, api, headers=headers, auth=auth, timeout=TIMEOUT)

    if result_only:
        return res
    result = deserialize(res.text if type(res) == requests.models.Response
                         else res.data)
    if issubclass(result.__class__, dict):
        return res.status_code, result['result'], result['msg']
    else:
        return res.status_code, 'FAILED', result


def put_on_server(urn, poolurl, contents='pool', headers=None, result_only=False, auth=None, client=None):
    """Register the pool on the server.

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc. Default None for `session`.
    """


    if auth is None:
        if client and getattr(client, 'auth', '') and client.auth:
            auth = client.auth
        else:
            auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session
    client.auth = auth

    api = urn2fdiurl(urn, poolurl, contents=contents, method='PUT')

    # client.auth = auth
    if logger.isEnabledFor(logging_DEBUG):
        print("PUT REQUEST API: " + api)
        if not issubclass(client.__class__, FlaskClient):
            print('client session cookies', list(client.cookies))

    aheaders = auth_headers(auth.username, auth.password)
    if headers :
        aheaders.update(headers)
    headers = aheaders

    if SHOW_REQ_SENT:
        __import__("pdb").set_trace()
        api = 'https://httpbin.org/put'
    # auth has priority over headers here
    # auth = getAuth(pccnode['username'], pccnode['password'])
    # headers = auth_headers(auth.username, auth.password)
    # client.headers.update(headers)
    if isinstance(client, FlaskClient):
        res = reqst(client.put, api, auth=auth)
    else:
        res = reqst(client.put, api, headers=headers, auth=auth, timeout=TIMEOUT)

    if result_only:
        return res
    result = deserialize(res.text if type(res) == requests.models.Response
                         else res.data)
    if 0 and logger.isEnabledFor(logging_DEBUG):
        if not issubclass(client.__class__, FlaskClient):
            print('@@@ session cookie', list(client.cookies))
        else:
            print('@@@ session cookie', list(res.request.cookies))

    try:
        return result['result'], result['msg']
    except (KeyError, TypeError):
        return 'FAILED', str(result)


def delete_from_server(urn, poolurl, contents='product', headers=None, result_only=False, auth=None, client=None, asyn=False):
    """Remove a product or pool from server

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    result_only: only return the reponse result. Default False.
    client: alternative client to answer API calls. For tests etc. Default None for `requests`.
    """

    if auth is None:
        if client and getattr(client, 'auth', '') and client.auth:
            auth = client.auth
        else:
            auth = getAuth(pccnode['username'], pccnode['password'])
    if client is None:
        client = session
    client.auth = auth

    _u = urn
    if isinstance(_u, list):
        urns = _u
        alist = True
    else:
        urns = [_u]
        alist = False

    aheaders = auth_headers(auth.username, auth.password)
    if headers :
        aheaders.update(headers)
    headers = aheaders

    if asyn:
        apis = [poolurl+'/'+u for u in urns]
        res = reqst('delete', apis=apis, **kwds)
    else:
        rs = []
        for u in urns:
            api = urn2fdiurl(u, poolurl, contents=contents, method='DELETE')
            if SHOW_REQ_SENT:
                __import__("pdb").set_trace()
                api = 'https://httpbin.org/delete'

            if logger.isEnabledFor(logging_DEBUG):
                print("DELETE REQUEST API: " + api)

            if issubclass(client.__class__, FlaskClient):
                r = reqst(client.delete, api, headers=headers, auth=auth)
            else:
                r = reqst(client.delete, api, headers=headers, auth=auth, timeout=TIMEOUT)
            if result_only:
                rs.append(r)
                continue

            result = deserialize(r.text if type(r) == requests.models.Response
                                 else r.data)
            if issubclass(result.__class__, dict):
                rs.append((result['result'], result['msg']))
            else:
                rs.append(('FAILED', result))
        res = rs if alist else rs[0]
        return res

# == == == = Async IO == == ==


def content2result_httppool(content):
    """Format aiohttp responses to httppool output.

    This is mainly used by `reqst` to adapt results to server API conventions.

    Parameters
    ----------
    content : list
        list of `aiohttp.ClientResponse` made by `aio_client`
    or of `urllib3.Session` (and `requests`) by `safe_client`.

    Returns
    -------
    list
        of values of the `result` key of dictionaries httppool
        returns.

    Raises
    ------
    ServerError
        Server error that returns non-json result or of un-understandable error messages.
    All_Exceptions[excpt]
        Exceptions that made understandable messages, named by variable 'excpt'.
    Examples
    --------
    FIXME: Add docs.


    """

    res = []
    if not isinstance(content, list):
        content = [content]
        alist = False
    else:
        alist = True

    for resp in content:
        is_aio = isinstance(resp, tuple)
        if is_aio:
            code, text, url = resp  # .status, resp.text(), resp.url.raw_path_qs
        else:
            code, text, url = resp.status_code, resp.text, resp.url
        obj = deserialize(text)
        ores = obj.get('result', '')
        if code != 200 or issubclass(obj.__class__, str) or issubclass(ores.__class__, str) and ores[:6] == 'FAILED':
            if not issubclass(obj.__class__, dict):
                # cannot deserialize
                raise ServerError(
                    f'AIO {resp.request.method} error {code} Message: '+lls(text, 200), resp, code=code)
            # deserializable
            msg = obj['msg']
            for line in chain(msg.split('.', 1)[:1], msg.split('\n')):
                excpt = line.split(':', 1)[0]
                if excpt in All_Exceptions:
                    # relay the exception from server
                    raise All_Exceptions[excpt](
                        f'Code {code} Message: {msg}')
            raise ServerError(
                f'AIO {method_name} error {ores}: '+lls(msg, 200), resp,
                code=code)
        if logger.isEnabledFor(logging_DEBUG):
            logger.debug(lls(text, 100))
        res.append(ores)

    # print('pppp', res[0])
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'AIO result size: {len(res)}.')
    return res if alist else res[0]


def content2result_csdb(content):
    """Format aiohttp responses to CSDB output.

    This is mainly used by `reqst` to adapt results to server API conventions.

    Parameters
    ----------
    content : list
        list of `aiohttp.ClientResponse` made by `aio_client`.
    or of `urllib3.Session` (and `requests`) by `safe_client`.

    Returns
    -------
    list
        of values of the `data` key of dictionaries httppool
        returns.

    Raises
    ------
    ServerError
        Server error that returns non-200 HTTP code, or non-0 `['code']`.

    Examples
    --------
    FIXME: Add docs.


    """

    res = []
    if not isinstance(content, list):
        content = [content]
        alist = False
    else:
        alist = True

    for resp in content:
        is_aio = isinstance(resp, tuple)
        if is_aio:
            # AIO
            code, text, url = resp  # .status, resp.text(), resp.url.raw_path_qs
            cont = text
        else:
            # requests
            if resp is None:
                #__import__("pdb").set_trace()
                return [None] * len(content) if alist else None
            code, cont, text, url = resp.status_code, resp.content, resp.text, resp.url
        if is_Fits(cont):
            res.append(cont)
            continue
        if text.startswith('<html>'):
            eo = text
            ocode = resp.status_code
            msg = resp.reason
            raise ServerError(
                f'REQ {resp.request.method} error: {ocode} Messag: {msg}', rsps=resp, code=code)

        obj = deserialize(text)
        if issubclass(obj.__class__, str):
            # cannot deserialize and/or bad code
            try:
                if code == 500:
                    eo = resp.json()
                    ocode = ['status']
                    msg = eo['message']
                elif code == 404:
                    eo = resp.text
                    ocode = ['status']
                    msg = eo['message']
                else:
                    eo = resp.json()
                    ocode = eo['code']
                    msg = eo['msg']
            except (TypeError, KeyError) as e:
                msg = lls(cont, 200)
                ocode = None
            if 'not exist' in msg:
                code = 404
            if code == 422:
                pass

            raise ServerError(
                f'REQ {resp.request.method} error: {ocode} Messag: {msg}', rsps=resp, code=code)

        # if deserializable
        if issubclass(obj.__class__, dict) and 'data' in obj:
            ores = obj['data']
            msg = obj.get('msg', '')
            ocode = obj.get('code', None)

            if 'not exist' in msg:
                code = 404
            if code != 200:
                raise ServerError(
                    f'Server Code {ocode} Message: {msg}', resp, code=code)
        else:
            # e.g. /get?urn=...
            ores = obj

        res.append(ores)

    # print('pppp', res[0])
    if logger.isEnabledFor(logging_DEBUG):
        logger.debug(f'{len(res)} {"asyn" if is_aio else ""} CSDB Results.')
    return res if alist else res[0]


def reqst(meth, apis, *args, server_type='httppool', auth=None, return_response=False, **kwds):
    """send session, requests, aiohttp requests.

    Parameters
    ----------
    meth : str, function
        If is a string, will be the method name of `aio_client`,
        `aio_client` is used so
        at least one of the `apis`, 'data' in `kwds`, and `headers`
        is expected to be a `list` or `tuple`.

        If is a function, the method functiono of
        session/request is used and apis is expected to be a string.
    apis : str, list, tuple
        The URL string if `meth` is a function. A list of URL strings
        if `meth` is a string. See `meth` docs above.
    server_type : string
        One of 'httppool' (default) and 'csdb', for HttpPool server
    and CSDB server, respectively.
    return_response: bool
        return a list of respons (always true to `safe_client` and unlisted ones. Default is `False`.
    *args : list

    **kwds : dict


    Returns
    -------
    list
        If `aio_client` is used, if 'httppool' is selected for 
    `server_type`, the result is that of `content2result_httppool`;
    if 'csdb', is that of `content2result_csdb`.

        If `safe_client` is used, a list if response object.

    Examples
    --------
    FIXME: Add docs.
    """
    if isinstance(meth, str):
        from aiohttp.helpers import BasicAuth
        ahb = BasicAuth(login=auth.username, password=auth.password)
        # use AIO
        content = aio_client(
            meth, apis, *args, auth=ahb, **kwds)
        if server_type == 'httppool':
            res = content2result_httppool(content)
        elif server_type == 'csdb':
            res = content2result_csdb(content)
        elif return_response:
            res = content
        else:
            raise ValueError('Unknown server type: {server_type}.')
    elif ismethod(meth):
        # use request, urllib3.Session
        if SHOW_REQ_SENT:
            __import__("pdb").set_trace()
            apis = f'https://httpbin.org/{meth.__func__.__name__}'

        content = safe_client(meth, apis, *args, auth=auth, **kwds)
        
        if server_type == 'httppool':
            res = content
        elif server_type == 'csdb':
            res = content2result_csdb(content)
        elif return_response:
            res = content
        else:
            raise ValueError('Unknown server type: {server_type}.')
    else:
        raise TypeError(
            'Unknown type for `reqst` arguement "meth": {method_name}.')
    return res


async def get_aio_result(method, *args, **kwds):
    async with method(*args, **kwds) as resp:
        # print(type(resp),dir(resp))
        con = await resp.text()
        return resp.status, con, resp.url.raw_path_qs


# async def get_aio_retry_result(method, *args, **kwds):
#     async with method(*args, **kwds) as resp:
#         # print(type(resp),dir(resp))
#         con = await resp.text()
#         return resp.status, con, resp.url.raw_path_qs


def aio_client(method_name, apis, data=None, headers=None,
               no_retry_controls=False,
               raise_for_status=False,
               **kwds):
    """
    Parameters
    ----------
    method: str
         name ofurllib3 Session or requests function such as `"get"`.
    no_retry_controls: bool
         without retry controls. Default `True`.
    raise_for_status: bool
         Defalut `False`.

    Returns
    -------
    tuple: 
       List of tuples, each tuple containing the three properties of 
    'ClientResponse`: `status`, text, `url.raw_path_qs`.
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
        # global aio_session
        aio_session = None
        if aio_session is None or aio_session._closed:
            tout = AIO_TIMEOUT
            client = aiohttp.ClientSession(timeout=tout, **kwds)
        if no_retry_controls:
            aio_session = client
        else:
            if aio_session is None or aio_session._closed or not issubclass(aio_session.__class__, RetryClient):
                if 0:
                    retry_options = ExponentialRetry(attempts=MAX_RETRIES)
                else:
                    retry_options = RandomRetry(attempts=MAX_RETRIES)
                # client = await aiohttp_client( app, raise_for_status=raise_for_status)
                retry_client = RetryClient(
                    client_session=client, retry_options=retry_options)
                aio_session = retry_client
        async with aio_session as session:
            tasks = []
            method = getattr(session, method_name)
            print('****', method)
            for n in range(cnt):
                a = apis[n] if alist else apis
                d = data[n] if dlist else data
                h = headers[n] if hlist else headers
                if method_name == 'post':
                    if no_retry_controls:
                        tasks.append(asyncio.ensure_future(
                            get_aio_result(method, a, data=d, headers=h, **kwds)))
                    else:
                        tasks.append(asyncio.ensure_future(
                            get_aio_result(method, a, data=d, headers=h, **kwds)))
                elif method_name in ('get', 'delete'):
                    if no_retry_controls:
                        tasks.append(asyncio.ensure_future(
                            get_aio_result(method, a, headers=h, **kwds)))
                    else:
                        tasks.append(asyncio.ensure_future(
                            get_aio_result(method, a, headers=h, **kwds)))
                else:
                    raise ValueError(f"Unknown AIO method {method_name}.")

                content = await asyncio.gather(*tasks)

            if logger.isEnabledFor(logging_DEBUG):
                logger.debug(f'AIO {method_name} return {len(content)} items')
            return content

    res = asyncio.run(multi())
    return res


async def get_retry_client(
    aiohttp_client,
    raise_for_status=False,
    retry_options=None,
):

    client = await aiohttp_client(app, raise_for_status=raise_for_status)

    retry_client = RetryClient(
        client_session=client, retry_options=retry_options)
    return retry_client, test_app

from fdi.dataset.serializable import serialize
@ functools.lru_cache(maxsize=256)
def cached_json_dumps(cls_full_name, ensure_ascii=True, indent=2,
                      des=False):
    # XXX add Model to Class
    obj = Class_Look_Up[cls_full_name.rsplit('.', 1)[-1]]()
    if des:
        return serialize(obj, ensure_ascii=ensure_ascii, indent=indent)
    else:
        return json.dumps(obj.zInfo, ensure_ascii=ensure_ascii, indent=indent)

def getCacheInfo():
    info = {}
    for i in ['getAuth', 'urn2fdiurl', 'cached_json_dumps']:
        info[i] = i.cache_info()

    return info
