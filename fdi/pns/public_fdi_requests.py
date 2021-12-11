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
             ':' + str(pcc['node']['port']) + pcc['baseurl']
AUTHUSER = pcc['node']['username']
AUTHPASS = pcc['node']['password']


@functools.lru_cache(maxsize=16)
def getAuth(user=AUTHUSER, password=AUTHPASS):
    return HTTPBasicAuth(user, password)


def read_from_cloud(urn, poolurl, service=webapi.PublicServices[0]):
    logger.info("Params: " + str([urn, poolurl, service]))
    auth = getAuth()
    if service == webapi.PublicServices[-1]:
        api = 'http://123.56.102.90:31702/csdb/home/cache'
        res = requests.get(api, auth=auth)
        return res.text
    return "Not implemented"
