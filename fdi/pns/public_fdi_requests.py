
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..utils.getconfig import getConfig
from ..utils.common import trbk
from ..pal import webapi
from .fdi_requests import safe_client, cached_json_dumps

from ..httppool.session import requests_retry_session

import functools
import logging
import sys
import json

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

session = requests_retry_session()

pcc = getConfig()
defaulturl = 'http://' + pcc['cloud_host'] + \
             ':' + str(pcc['cloud_port'])
default_base = defaulturl + pcc['cloud_api_base'] + \
    '/' + pcc['cloud_api_version']
AUTHUSER = pcc['cloud_username']
AUTHPASS = pcc['cloud_password']


@functools.lru_cache(maxsize=16)
def getAuth(user=AUTHUSER, password=AUTHPASS):
    return HTTPBasicAuth(user, password)


def read_from_cloud(requestName, client=None, asyn=False, **kwds):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    if requestName == 'getToken':
        requestAPI = defaulturl + '/user/auth/token'
        postData = {'username': AUTHUSER, 'password': AUTHPASS}
        res = safe_client(client.post, requestAPI, headers=header,
                          data=serialize(postData))
    elif requestName == 'verifyToken':
        requestAPI = defaulturl + '/user/auth/verify?token=' + kwds['token']
        res = safe_client(client.get, requestAPI)
    elif requestName[0:4] == 'info':
        header['X-AUTH-TOKEN'] = kwds['token']
        if requestName == 'infoUrn':
            requestAPI = default_base + \
                '/storage/info?urns=' + kwds['urn']
        elif requestName == 'infoPool':
            limit = kwds.get('limit', 10000)
            requestAPI = default_base + \
                f'/storage/info?pageIndex=1&pageSize={limit}&pools=' + \
                kwds['paths']
        elif requestName == 'infoPoolType':
            limit = kwds.get('limit', 10000)
            # use pools instead of paths -mh
            requestAPI = default_base + \
                f'/storage/info?pageIndex=1&pageSize={limit}&&pools=' + \
                kwds['pools']
        else:
            raise ValueError("Unknown request API: " + str(requestName))
        res = safe_client(client.get, requestAPI, headers=header)

    elif requestName == 'getMeta':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            '/storage/meta?urn=' + kwds['urn']
        res = safe_client(client.get, requestAPI, headers=header)
        return deserialize(json.dumps(res.json()['data']['_ATTR_meta']))
    elif requestName == 'getDataInfo':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI0 = default_base + \
            '/storage/searchByPoolOrPath?limitCount=%d&path='
        res = []
        urns = kwds.get('urn', [])
        # max length with one extra
        requestAPI1 = requestAPI0 % (len(urns) + 1)
        for u in urns:
            requestAPI = requestAPI1 + u[3:].replace(':', '/')
            d = safe_client(client.get, requestAPI,
                            headers=header).json()['data']
            # if not found: r['data']==[]
            res.append(d[0] if d else None)
        return res

    elif requestName == 'getDataType':
        header['X-AUTH-TOKEN'] = kwds['token']

        requestAPI = default_base + \
            '/datatype/list'
        res = safe_client(client.get, requestAPI, headers=header)

    elif requestName == 'uploadDataType':
        header['X-AUTH-TOKEN'] = kwds['token']
        header["accept"] = "*/*"
        # somehow application/json will cause error "unsupported"
        del header['Content-Type']  # = 'application/json'  # ;charset=UTF-8'
        requestAPI = default_base + \
            '/datatype/upload'
        cls_full_name = kwds['cls_full_name']
        jsn = cached_json_dumps(cls_full_name,
                                ensure_ascii=kwds.get('ensure_ascii', True),
                                indent=kwds.get('indent', 2))
        fdata = {"file": (cls_full_name, jsn)}
        data = {"metaPath": "/metadata",
                "productType": cls_full_name}
        res = safe_client(client.post, requestAPI,
                          files=fdata, data=data, headers=header)
    elif requestName == 'delDataType':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            f'/storage/delDatatype?path=' + kwds['path']
        res = safe_client(client.delete, requestAPI, headers=header)
    elif requestName == 'remove':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI0 = default_base + \
            '/storage/delete?path='
        path = kwds['path']
        if asyn:
            apis = [requestAPI0+p for p in path]
            res = aio_client('post', apis, headers=header)
        else:
            res = safe_client(client.post, requestAPI0 +
                              path, headers=header)
    elif requestName == 'existPool':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            '/pool/info?storagePoolName=' + kwds['poolname']
        res = safe_client(client.get, requestAPI, headers=header)
    elif requestName == 'createPool':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            '/pool/create?poolName=' + kwds['poolname'] + '&read=0&write=0'
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'wipePool':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            '/pool/delete?storagePoolName=' + kwds['poolname']
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'restorePool':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            '/pool/restore?storagePoolName=' + kwds['poolname']
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'addTag':
        header['X-AUTH-TOKEN'] = kwds['token']
        requestAPI = default_base + \
            '/storage/addTags?tags=' + kwds['tags'] + '&urn=' + kwds['urn']
        res = safe_client(client.get, requestAPI, headers=header)
    else:
        raise ValueError("Unknown request API: " + str(requestName))
    # print("Read from API: " + requestAPI)
    # must remove csdb layer
    return deserialize(res.text)


def load_from_cloud(requestName, client=None, **kwds):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = default_base
    try:
        if requestName == 'uploadProduct':
            header = {}
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            header['X-CSDB-AUTOINDEX'] = '1'
            header['X-CSDB-METADATA'] = '/_ATTR_meta'
            header['X-CSDB-HASHCOMPARE'] = '0'

            requestAPI = requestAPI + \
                '/storage/upload?path=' + kwds.pop('path', '')
            prd = kwds.pop('products', None)
            fileName = kwds.pop('resourcetype', '')
            if not fileName:
                __import__("pdb").set_trace()

            if 'tags' in kwds:
                t = kwds.pop('tags')
                tags = [t] if isinstance(t, str) else t if t else ''
                data = {'tags': ','.join(tags)}
            else:
                data = None
            kwds.pop('serialize_out', '')
            res = safe_client(client.post, requestAPI, files={'file': (
                fileName, prd)}, data=data, headers=header, **kwds)

        elif requestName == 'pullProduct':
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = requestAPI + '/storage/get?urn=' + kwds.pop('urn', '')
            res = safe_client(client.get, requestAPI,
                              headers=header, stream=True)
            # TODO: save product to local
        else:
            raise ValueError("Unknown request API: " + str(requestName))
    except Exception as e:
        return 'Load File failed: ' + str(e) + trbk(e)
    # print("Load from API: " + requestAPI)
    return deserialize(res.text)


def delete_from_server(requestName, client=None, **kwargs):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = default_base
    try:
        if requestName == 'delTag':
            header['X-AUTH-TOKEN'] = kwargs['token']
            requestAPI = requestAPI + '/storage/delTag?tag=' + kwargs['tag']
            res = safe_client(client.delete, requestAPI, headers=header)
        else:
            raise ValueError("Unknown request API: " + str(requestName))
        # print("Read from API: " + requestAPI)
        return deserialize(res.text)
    except Exception as e:
        err = {'msg': str(e)}
        return err


def get_service_method(method):
    service = method.split('_')[0]
    serviceName = method.split('_')[1]
    if service not in webapi.PublicServices:
        return 'home', None
    return service, serviceName
