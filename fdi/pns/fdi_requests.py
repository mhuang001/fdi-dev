import requests
import logging
import json
import sys
from requests.auth import HTTPBasicAuth

from fdi.dataset.serializable import serializeClassID
from fdi.dataset.deserialize import deserializeClassID
from fdi.pal.urn import parseUrn
from .pnsconfig import pnsconfig as pcc

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
logger.debug('level %d' % (logger.getEffectiveLevel()))


common_header = {
    'Accept': 'application/json',
    'Accept-Charset': 'utf-8',
    'Accept-Encoding': 'identity',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    "Content-type": 'application/json'
}

defaulturl = 'http://' + pcc['node']['host'] + ':' + str(pcc['node']['port']) + pcc['baseurl']

def urn2fdiurl(urn, contents='product', method='GET'):
    if urn.startswith('urn', 0, 3):
        poolname, resourcecn, indexs, scheme, place, poolpath = parseUrn(urn)
        url = urlparse(poolname)
        base = scheme + '://' + place + pcc['baseurl']
    elif urn.startswith('http', 0, 4):
        url = urlparse(urn)
        base = url.scheme + '://' + url.netloc + pcc['baseurl']

    if method == 'GET':
        if contents == 'product':
            ret = base + url.path + '/' + resourcecn + '/' + indexs
        elif contents == 'housekeeping':
            ret = base + url.path + '/hk'
        elif contents in ['classes', 'urns', 'tags']:
            ret = base + url.path + '/hk/'  + contents
        else:
            raise(ValueError(contents))
    elif method == 'POST':
        if contents == 'product':
            ret = base + url.path + '/' + resourcecn + '/' + indexs
        else:
            raise ValueError('No such method and contents composition: ' + method + ' / ' + contents)
    else:
        raise ValueError(method)
    return ret


def save_to_server(data, urn):
    user = pcc['auth_user']
    password = pcc['auth_pass']
    auth = HTTPBasicAuth(user, password)
    api = urn2fdiurl(urn, contents='product', method='POST')
    print('POST API: ' + api)
    res = requests.post(api, auth=auth, data=serializeClassID(data))
    return res


def read_from_server(poolurn, contents='product'):
    user = pcc['auth_user']
    password = pcc['auth_pass']
    auth = HTTPBasicAuth(user, password)
    api = urn2fdiurl(poolurn, contents)
    print("GET REQUEST API: " + api)
    x = requests.get(api, auth=auth)
    result = deserializeClassID(x.text)
    return result['result']
