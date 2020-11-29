# -*- coding: utf-8 -*-

import requests
import logging
import sys
from requests.auth import HTTPBasicAuth

from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize
from fdi.pal.urn import parseUrn, parse_poolurl
from .pnsconfig import pnsconfig as pcc
from fdi.utils.getconfig import getConfig

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


common_header = {
    'Accept': 'application/json',
    'Accept-Charset': 'utf-8',
    'Accept-Encoding': 'identity',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    "Content-type": 'application/json'
}


pcc.update(getConfig())
defaulturl = 'http://' + pcc['node']['host'] + \
    ':' + str(pcc['node']['port']) + pcc['baseurl']


def urn2fdiurl(urn, poolurl, contents='product', method='GET'):
    """ Returns URL for accessing pools with a URN.

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
    DELETE compo for removing product or pool

    Example:
    IP=ip poolpath=/a poolname=b/c files=/a/b/c/classes.jsn | urns.jsn | t.. | urn...

    with python:
    m.refs['myinput'] = special_ref
    ref=pstore.save(m)
    assert ref.urn == 'urn:c:fdi.dataset.MapContext:203'
    p=ref.product
    myref=p.refs['myinput']

    with a pool:
    myref=pool.load('http://ip:port/v0.6/a/b/c/fdi.dataset.MapContext/203/refs/myinput')

    At the same time this is not allowed due to overlapping after 'c'

    urn:http://ip:port/a/b/d/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/a/b/c/d/

    This is also overlapping starting from '/'

    urn:http://ip:port/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/

    but for example this is allowed:
    urn:http://ip:port/a/k/fdi.dataset.Product:203    ==>
    http://ip:port/v0.6/a/k/
    """

    poolname, resourcecn, index = parseUrn(urn)
    indexs = str(index)
    poolpath, scheme, place, pn = parse_poolurl(poolurl, poolhint=poolname)
    if poolname is None:
        poolname = pn
    if method == 'GET':
        if contents == 'product':
            ret = poolurl + '/' + resourcecn + '/' + indexs
        elif contents == 'housekeeping':
            ret = poolurl + '/hk'
        elif contents in ['classes', 'urns', 'tags']:
            ret = poolurl + '/hk/' + contents
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    elif method == 'POST':
        if contents == 'product':
            ret = poolurl + '/' + resourcecn + '/' + indexs
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    elif method == 'DELETE':
        if contents == 'pool':
            ret = poolurl
        elif contents == 'product':
            ret = poolurl + '/' + resourcecn + '/' + indexs
        else:
            raise ValueError(
                'No such method and contents composition: ' + method + ' / ' + contents)
    else:
        raise ValueError(method)
    return ret

# Store tag in headers, maybe that's  not a good idea


def save_to_server(data, urn, poolurl, tag):
    """Save product to server with putting tag in headers
    """
    user = pcc['auth_user']
    password = pcc['auth_pass']
    auth = HTTPBasicAuth(user, password)
    api = urn2fdiurl(urn, poolurl, contents='product', method='POST')
    # print('POST API: ' + api)
    headers = {'tag': tag}
    res = requests.post(
        api, auth=auth, data=serialize(data), headers=headers)
    result = deserialize(res.text)
    # print(result)
    return result


def read_from_server(urn, poolurl, contents='product'):
    """Read product or hk data from server
    """
    user = pcc['auth_user']
    password = pcc['auth_pass']
    auth = HTTPBasicAuth(user, password)
    api = urn2fdiurl(urn, poolurl, contents=contents)
    # print("GET REQUEST API: " + api)
    res = requests.get(api, auth=auth)
    result = deserialize(res.text)
    return result['result'], result['msg']


def delete_from_server(urn, poolurl, contents='product'):
    """Remove a product or pool from server
    """
    user = pcc['auth_user']
    password = pcc['auth_pass']
    auth = HTTPBasicAuth(user, password)
    api = urn2fdiurl(urn, poolurl, contents=contents, method='DELETE')
    # print("DELETE REQUEST API: " + api)
    res = requests.delete(api, auth=auth)
    result = deserialize(res.text)
    return result['result'], result['msg']
