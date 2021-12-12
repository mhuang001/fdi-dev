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


def get_service_method(method):
    service = method.split('_')[0]
    serviceName = method.split('_')[1]
    if service not in webapi.PublicServices:
        return 'home', None
    return service, serviceName


def method_to_cloud_api(service, serviceName):
    requestUrl = defaulturl + webapi.publicRoute + webapi.publicVersion + '/' + service


def datatype_from_cloud(service, serviceName, *args, **kwds):
    """
    Unable to identify args and kwds.. maybe give up this method
    """
    print("Params: " + service + " / ServiceName: " + serviceName)

    requestUrl = defaulturl + webapi.publicRoute + webapi.publicVersion + '/' + service

    auth = getAuth()
    if serviceName == 'delete':
        return 'Not implemented, if need to check data type exists?'

    elif serviceName.startswith('list'):
        if serviceName == 'list':
            if len(args) == 0:
                requestUrl = requestUrl + '/' + serviceName
            elif len(args) == 1:
                requestUrl = requestUrl + '/list?substring=' + args[0]
            elif len(args) == 2 and type(args[0]) == str and type(args[1]) == str:
                requestUrl = requestUrl + '/' + args[0] + '/' + args[1]
            else:
                print("Request Cloud API: " + requestUrl)
                return 'Unknown request arguments, please check!'

        elif serviceName == 'listNode' and len(args) == 2 and type(args[0]) == str and type(args[1]) == str:
            requestUrl = requestUrl + '/' + args[0] + '/' + args[1] + '/json'

        elif serviceName == 'listMeta' and len(args) == 1 and type(args[0] == 'str'):
            requestUrl = requestUrl + '/' + args[0] + '/meta'

        else:
            print("Request Cloud API: " + requestUrl)
            return 'Unknown request arguments, please check!'
        print("Request Cloud API: " + requestUrl)
        res = requests.get(requestUrl, auth=auth)
    elif serviceName == 'upload':
        requestUrl = requestUrl + '/' + serviceName
        if len(args) == 3 and type(args[0]) == str and type(args[1]) == str and type(args[2]) == dict:
            import os
            if os.path.exists(args[0]):
                f = open(args[0], 'rb')
            else:
                return 'No such file: ' + args[0]
            args[2]['productType'] = args[1]
            res = requests.get(requestUrl, files={'file': f}, data=args[2])
        else:
            print("Request Cloud API: " + requestUrl)
            return 'Unknown request arguments, please check!'
    else:
        res = 'Not implemented'
    return res.text
