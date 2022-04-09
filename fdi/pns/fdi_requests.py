# -*- coding: utf-8 -*-

import requests
import functools
import logging
import sys
from requests.auth import HTTPBasicAuth

from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..pal.urn import parseUrn, parse_poolurl
from ..utils.getconfig import getConfig
from ..pal.webapi import WebAPI

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
#logger.debug('level %d' % (logger.getEffectiveLevel()))

POST_PRODUCT_TAG_NAME = 'FDI-Product-Tags'

pcc = getConfig()
defaulturl = 'http://' + pcc['node']['host'] + \
    ':' + str(pcc['node']['port']) + pcc['baseurl']

pccnode = pcc['node']


@functools.lru_cache(maxsize=16)
def getAuth(user, password):
    return HTTPBasicAuth(user, password)


@functools.lru_cache(maxsize=64)
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


def post_to_server(data, urn, poolurl, contents='product', headers=None,
                   no_serial=False, result_only=False, auth=None):
    """Post data to server with  tag in headers

    data: goes to the request body
    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    contents: type of request. Default 'api'.
    headers: request header dictionary. Default None.
    no_serial: do not serialize the data.
    result_only: only return requests result, no code and msg. Default False.

    """
    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    api = urn2fdiurl(urn, poolurl, contents=contents, method='POST')
    # print('POST API: ' + api)
    if headers is None:
        headers = {}
    sd = data if no_serial else serialize(data)
    res = requests.post(api, auth=auth, data=sd, headers=headers)
    # print(res)
    if result_only:
        return res
    result = deserialize(res.text)
    if issubclass(result.__class__, dict):
        return res.status_code, result['result'], result['msg']
    else:
        return res.status_code, 'FAILED', result


def save_to_server(data, urn, poolurl, tag, no_serial=False, auth=None):
    """Save product to server with putting tag in headers

    data: goes to the request body
    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    tag: go with the products into the pool
    no_serial: do not serialize the data.
    """
    headers = {POST_PRODUCT_TAG_NAME: serialize(tag)}
    res = post_to_server(data, urn, poolurl, contents='product',
                         headers=headers, no_serial=no_serial, result_only=True, auth=auth)
    return res
    # auth = getAuth(pccnode['username'], pccnode['password'])
    # api = urn2fdiurl(urn, poolurl, contents='product', method='POST')
    # # print('POST API: ' + api)
    # headers = {'tags': tag}
    # sd = data if no_serial else serialize(data)
    # res = requests.post(
    #     api, auth=auth, data=sd, headers=headers)
    # # print(res)
    # return res


def read_from_server(urn, poolurl, contents='product', auth=None):
    """Read product or hk data from server

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    """
    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    api = urn2fdiurl(urn, poolurl, contents=contents)
    # print("GET REQUEST API: " + api)
    res = requests.get(api, auth=auth)
    result = deserialize(res.text)
    if issubclass(result.__class__, dict):
        return res.status_code, result['result'], result['msg']
    else:
        return res.status_code, 'FAILED', result


def put_on_server(urn, poolurl, contents='pool', auth=None):
    """Register the pool on the server.

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    """
    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    api = urn2fdiurl(urn, poolurl, contents=contents, method='PUT')
    # print("DELETE REQUEST API: " + api)
    res = requests.put(api, auth=auth)
    result = deserialize(res.text)
    if issubclass(result.__class__, dict):
        return result['result'], result['msg']
    else:
        return 'FAILED', result


def delete_from_server(urn, poolurl, contents='product', auth=None):
    """Remove a product or pool from server

    urn: to extract poolname, product type, and index if any of these are needed
    poolurl: the only parameter must be provided
    """
    if auth is None:
        auth = getAuth(pccnode['username'], pccnode['password'])
    api = urn2fdiurl(urn, poolurl, contents=contents, method='DELETE')
    # print("DELETE REQUEST API: " + api)
    res = requests.delete(api, auth=auth)
    result = deserialize(res.text)
    if issubclass(result.__class__, dict):
        return result['result'], result['msg']
    else:
        return 'FAILED', result


def getCacheInfo():
    info = {}
    for i in ['getAuth', 'urn2fdiurl']:
        info[i] = i.cache_info()

    return info
