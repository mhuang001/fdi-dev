import requests
import functools
import logging
import sys
import json
from requests.auth import HTTPBasicAuth

from fdi.dataset.serializable import serialize
from fdi.dataset.deserialize import deserialize
from fdi.pal.urn import parseUrn, parse_poolurl
from fdi.utils.getconfig import getConfig
from ..pal import webapi

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
AUTHUSER = pcc['cloud_username']
AUTHPASS = pcc['cloud_password']


@functools.lru_cache(maxsize=16)
def getAuth(user=AUTHUSER, password=AUTHPASS):
    return HTTPBasicAuth(user, password)


def read_from_cloud(requestName, **kwargs):
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    if requestName == 'getToken':
        requestAPI = defaulturl + '/user/auth/token'
        postData = {'username': AUTHUSER, 'password': AUTHPASS}
        res = requests.post(requestAPI, headers=header,
                            data=serialize(postData))
    elif requestName == 'verifyToken':
        requestAPI = defaulturl + '/user/auth/verify?token=' + kwargs['token']
        res = requests.get(requestAPI)
    elif requestName[0:4] == 'info':
        header['X-AUTH-TOKEN'] = kwargs['token']
        if requestName == 'infoUrn':
            requestAPI = defaulturl + pcc['cloud_baseurl'] + \
                '/storage/info?urns=' + kwargs['urn']
        elif requestName == 'infoPool':
            requestAPI = defaulturl + pcc['cloud_baseurl'] + \
                '/storage/info?pageIndex=1&pageSize=10000&pools=' + \
                kwargs['poolpath']
        elif requestName == 'infoPoolType':
            requestAPI = defaulturl + pcc['cloud_baseurl'] + \
                '/storage/info?pageIndex=1&pageSize=10000&paths=' + \
                kwargs['poolpath']
        else:
            raise ValueError("Unknown request API: " + str(requestName))
        res = requests.get(requestAPI, headers=header)

    elif requestName == 'getMeta':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/storage/meta?urn=' + kwargs['urn']
        res = requests.get(requestAPI, headers=header)
        return deserialize(json.dumps(res.json()['data']['_ATTR_meta']))
    elif requestName == 'getDataType':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/datatype/list'
        res = requests.get(requestAPI, headers=header)
    elif requestName == 'remove':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/storage/delete?path=' + kwargs['path']
        res = requests.post(requestAPI, headers=header)
    elif requestName == 'existPool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/pool/info?storagePoolName=' + kwargs['poolname']
        res = requests.get(requestAPI, headers=header)
    elif requestName == 'createPool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/pool/create?poolName=' + kwargs['poolname'] + '&read=0&write=0'
        res = requests.post(requestAPI, headers=header)
    elif requestName == 'wipePool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/pool/delete?storagePoolName=' + kwargs['poolname']
        res = requests.post(requestAPI, headers=header)
    elif requestName == 'restorePool':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/pool/restore?storagePoolName=' + kwargs['poolname']
        res = requests.post(requestAPI, headers=header)
    elif requestName == 'addTag':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + pcc['cloud_baseurl'] + \
            '/storage/addTags?tags=' + kwargs['tags'] + '&urn=' + kwargs['urn']
        res = requests.get(requestAPI, headers=header)
    else:
        raise ValueError("Unknown request API: " + str(requestName))
    # print("Read from API: " + requestAPI)
    # must remove csdb layer
    return deserialize(res.text)


def load_from_cloud(requestName, **kwargs):
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = defaulturl + pcc['cloud_baseurl']
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
                tags = ''
                if isinstance(kwargs['tags'], list):
                    for ele in kwargs['tags']:
                        tags = tags + ele + ','
                elif isinstance(kwargs['tags'], str):
                    tags = kwargs['tags']
                data = {'tags': tags}
            else:
                data = None
            res = requests.post(requestAPI, files={'file': (
                fileName, prd)}, data=data, headers=header)

        elif requestName == 'pullProduct':
            header['X-AUTH-TOKEN'] = kwargs['token']
            requestAPI = requestAPI + '/storage/get?urn=' + kwargs['urn']
            res = requests.get(requestAPI, headers=header, stream=True)
            # TODO: save product to local
        else:
            raise ValueError("Unknown request API: " + str(requestName))
    except Exception as e:
        return 'Load File failed: ' + str(e)
    # print("Load from API: " + requestAPI)
    return deserialize(res.text)


def delete_from_server(requestName, **kwargs):
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = defaulturl + pcc['cloud_baseurl']
    try:
        if requestName == 'delTag':
            header['X-AUTH-TOKEN'] = kwargs['token']
            requestAPI = requestAPI + '/storage/delTag?tag=' + kwargs['tag']
            res = requests.delete(requestAPI, headers=header)
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
