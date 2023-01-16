# -*- coding: utf-8 -*-

from urllib3.exceptions import NewConnectionError, ProtocolError
from requests.exceptions import ConnectionError
from flask import Flask
from flask.testing import FlaskClient

import requests
import functools
import logging
import sys
from requests.auth import HTTPBasicAuth

from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..pal.urn import parseUrn, parse_poolurl
from ..utils.getconfig import getConfig
from ..utils.common import trbk
from ..pal.webapi import WebAPI
from .jsonio import auth_headers

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


def safe_client(method, api, *args, **kwds):
    # return method(api, *args, **kwds)
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
    logger.debug(
        f'resp {n} retry.{res.history}, {getattr(res.request,"path","")} {method.__func__.__qualname__}')

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
    res = safe_client(client.put, api, auth=auth, timeout=TIMEOUT)
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


def delete_from_server(urn, poolurl, contents='product', result_only=False, auth=None, client=None):
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
    api = urn2fdiurl(urn, poolurl, contents=contents, method='DELETE')
    # print("DELETE REQUEST API: " + api)
    res = safe_client(client.delete, api, auth=auth, timeout=TIMEOUT)

    if result_only:
        return res
    result = deserialize(res.text if type(res) == requests.models.Response
                         else res.data)
    if issubclass(result.__class__, dict):
        return result['result'], result['msg']
    else:
        return 'FAILED', result


def getCacheInfo():
    info = {}
    for i in ['getAuth', 'urn2fdiurl']:
        info[i] = i.cache_info()

    return info
