import requests
import functools
import logging
import sys
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
defaulturl = 'http://' + pcc['node']['host'] + \
             ':' + str(pcc['node']['port'])
AUTHUSER = pcc['node']['username']
AUTHPASS = pcc['node']['password']


@functools.lru_cache(maxsize=16)
def getAuth(user=AUTHUSER, password=AUTHPASS):
    return HTTPBasicAuth(user, password)


def read_from_cloud(requestName, **kwargs):
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    if requestName == 'getToken':
        requestAPI = defaulturl + '/user/auth/token'
        postData = {'username': AUTHUSER, 'password': AUTHPASS}
        res = requests.post(requestAPI, headers=header, data=serialize(postData))
    elif requestName == 'verifyToken':
        requestAPI = defaulturl + '/user/auth/verify?token=' + kwargs['token']
        res = requests.get(requestAPI)
    elif requestName[0:4] == 'info':
        header['X-AUTH-TOKEN'] = kwargs['token']
        if requestName == 'infoUrn':
            requestAPI = defaulturl + webapi.publicRoute + webapi.publicVersion + \
                         '/storage/info?urns=' + kwargs['urn']
        elif requestName == 'infoPool':
            requestAPI = defaulturl + webapi.publicRoute + webapi.publicVersion + \
                         '/storage/info?paths=' + kwargs['poolpath']
        else:
            raise ValueError("Unknown request API: " + str(requestName))
        res = requests.get(requestAPI, headers=header)

    elif requestName == 'getMeta':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + webapi.publicRoute + webapi.publicVersion + \
                     '/storage/meta?urn=' + kwargs['urn']
        res = requests.get(requestAPI, headers=header)

    elif requestName == 'getDataType':
        header['X-AUTH-TOKEN'] = kwargs['token']
        requestAPI = defaulturl + webapi.publicRoute + webapi.publicVersion + \
                     '/datatype/list'
        res = requests.get(requestAPI, headers=header)
    else:
        raise ValueError("Unknown request API: " + str(requestName))
    print("Read from API: " + requestAPI)
    return deserialize(res.text)


def load_from_cloud(requestName, **kwargs):
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = defaulturl + webapi.publicRoute + webapi.publicVersion
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
            res = requests.post(requestAPI, files={'file': (fileName, prd)}, data=data, headers=header)

        elif requestName == 'pullProduct':
            header['X-AUTH-TOKEN'] = kwargs['token']
            requestAPI = requestAPI + '/storage/get?urn=' + kwargs['urn']
            res = requests.get(requestAPI, headers=header, stream=True)
            # TODO: save product to local
        else:
            raise ValueError("Unknown request API: " + str(requestName))
    except Exception as e:
        return 'Load File failed: ' + str(e)
    print("Read from API: " + requestAPI)
    return deserialize(res.text)


def get_service_method(method):
    service = method.split('_')[0]
    serviceName = method.split('_')[1]
    if service not in webapi.PublicServices:
        return 'home', None
    return service, serviceName
