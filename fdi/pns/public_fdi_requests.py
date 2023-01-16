import functools
import logging
import sys
import json
from requests.auth import HTTPBasicAuth

from ..dataset.serializable import serialize
from ..dataset.classes import Class_Look_Up
from ..dataset.deserialize import deserialize
from ..utils.getconfig import getConfig
from ..pal import webapi
from .fdi_requests import safe_client

from ..httppool.session import requests_retry_session

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


@functools.lru_cache(maxsize=256)
def cached_json_dumps(cls_full_name, ensure_ascii=True, indent=2):
    # XXX add Model to Class
    obj = Class_Look_Up[cls_full_name.rsplit('.', 1)[-1]]()
    return json.dumps(obj.zInfo, ensure_ascii=ensure_ascii, indent=indent)


def read_from_cloud(requestName, client=None, **kwargs):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    if requestName == 'getToken':
        requestAPI = defaulturl + '/user/auth/token'
        postData = {'username': AUTHUSER, 'password': AUTHPASS}
        res = safe_client(client.post, requestAPI, headers=header,
                          data=serialize(postData))
    elif requestName == 'verifyToken':
        requestAPI = defaulturl + '/user/auth/verify?token=' + kwargs['token']
        res = safe_client(client.get, requestAPI)
    elif requestName[0:4] == 'info':
        header['X-AUTH-TOKEN'] = kwargs['token']
        if requestName == 'infoUrn':
            requestAPI = default_base + \
                '/storage/info?urns=' + kwargs['urn']
        elif requestName == 'infoPool':
            requestAPI = default_base + \
                '/storage/info?pageIndex=1&pageSize=10000&pools=' + \
                kwargs['poolpath']
        elif requestName == 'infoPoolType':
            # use pools instead of paths -mh
            requestAPI = default_base + \
                '/storage/info?pageIndex=1&pageSize=10000&pools=' + \
                kwargs['pools']
        else:
            raise ValueError("Unknown request API: " + str(requestName))
        res = safe_client(client.get, requestAPI, headers=header)

    elif requestName == 'getMeta':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/storage/meta?urn=' + kwargs['urn']
        res = safe_client(client.get, requestAPI, headers=header)
        return deserialize(json.dumps(res.json()['data']['_ATTR_meta']))
    elif requestName == 'getDataType':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/datatype/list'
        res = safe_client(client.get, requestAPI, headers=header)
    elif requestName == 'uploadDataType':
        header['X-AUTH-TOKEN'] = kwargs['token']
        header["accept"] = "*/*"
        # somehow application/json will cause error "unsupported"
        del header['Content-Type']  # = 'application/json'  # ;charset=UTF-8'
        requestAPI = default_base + \
            '/datatype/upload'
        cls_full_name = kwargs['cls_full_name']
        jsn = cached_json_dumps(cls_full_name,
                                ensure_ascii=kwargs.get('ensure_ascii', True),
                                indent=kwargs.get('indent', 2))
        fdata = {"file": (cls_full_name, jsn)}
        data = {"metaPath": "/metadata",
                "productType": cls_full_name}
        res = safe_client(client.post, requestAPI,
                          files=fdata, data=data, headers=header)
    elif requestName == 'delDataType':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            f'/storage/delDatatype?path=' + kwargs['path']
        res = safe_client(client.delete, requestAPI, headers=header)
    elif requestName == 'remove':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/storage/delete?path=' + kwargs['path']
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'existPool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/pool/info?storagePoolName=' + kwargs['poolname']
        res = safe_client(client.get, requestAPI, headers=header)
    elif requestName == 'createPool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/pool/create?poolName=' + kwargs['poolname'] + '&read=0&write=0'
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'wipePool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/pool/delete?storagePoolName=' + kwargs['poolname']
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'restorePool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/pool/restore?storagePoolName=' + kwargs['poolname']
        res = safe_client(client.post, requestAPI, headers=header)
    elif requestName == 'addTag':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = default_base + \
            '/storage/addTags?tags=' + kwargs['tags'] + '&urn=' + kwargs['urn']
        res = safe_client(client.get, requestAPI, headers=header)
    else:
        raise ValueError("Unknown request API: " + str(requestName))
    # print("Read from API: " + requestAPI)
    # must remove csdb layer
    return deserialize(res.text)


def load_from_cloud(requestName, client=None, **kwargs):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = default_base
    try:
        if requestName == 'uploadProduct':
            header = {}
            header['X-AUTH-TOKEN'] = kwargs['token']
            header['X-CSDB-AUTOINDEX'] = '1'
            header['X-CSDB-METADATA'] = '/_ATTR_meta'
            header['X-CSDB-HASHCOMPARE'] = '0'

            requestAPI = requestAPI + '/storage/upload?path=' + kwargs['path']
            prd = kwargs['products']
            fileName = kwargs['resourcetype']
            if kwargs.get('tags'):
                if isinstance(kwargs['tags'], str):
                    tags = [kwargs['tags']]
                data = {'tags': ','.join(tags)}
            else:
                data = None
            res = safe_client(client.post, requestAPI, files={'file': (
                fileName, prd)}, data=data, headers=header)

        elif requestName == 'pullProduct':
            header['X-AUTH-TOKEN'] = kwargs['token']
            requestAPI = requestAPI + '/storage/get?urn=' + kwargs['urn']
            res = safe_client(client.get, requestAPI,
                              headers=header, stream=True)
            # TODO: save product to local
        else:
            raise ValueError("Unknown request API: " + str(requestName))
    except Exception as e:
        return 'Load File failed: ' + str(e)
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
