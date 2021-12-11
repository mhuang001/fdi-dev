import logging
import sys

from .urn import makeUrn
from ..dataset.deserialize import serialize_args
from ..dataset.serializable import serialize
from ..pal import webapi
from ..pns.public_fdi_requests import read_from_cloud
from ..utils.common import fullname
from ..utils.getconfig import getConfig

logger = logging.getLogger(__name__)
pcc = getConfig(conf='public')

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
else:
    PY3 = False
    strset = (str, unicode)

"""
Cloud apis classification:
DOC: http://123.56.102.90:31702/api/swagger-ui.html#/%E9%85%8D%E7%BD%AE%E7%AE%A1%E7%90%86
api_version = v1
classification = ['storage', 'pool', 'group', 'node', 'data', 'config', 'home']

INIT:
1. Connect to /home/cache RES ==>ok
2. 
"""

def tocloud(self, method, *args, **kwds):
    # if method == 'select':
    #    __import__('pdb').set_trace()

    apipath = serialize_args(method, *args, not_quoted=self.not_quoted, **kwds)

    urn = 'urn:::0'  # makeUrn(self._poolname, typename, 0)

    logger.debug("READ PRODUCT FROM REMOTE CLOUD===> " + urn)
    res = {}
    # code, res, msg = read_from_server(urn, self._poolurl, apipath)
    # if issubclass(res.__class__, str) and 'FAILED' in res or code != 200:
    #     for line in msg.split('\n'):
    #         excpt = line.split(':', 1)[0]
    #         if excpt in bltn:
    #             # relay the exception from server
    #             raise bltn[excpt](('Code %d: %s' % (code, msg)))
    #     raise RuntimeError('Executing ' + method +
    #                        ' failed. Code: %d Message: %s' % (code, msg))
    return res


def toCloud(method_name=None):
    """ decorator to divert local calls to server and return what comes back.

    """

    def inner(*sf):
        """ [self], fun """
        fun = sf[-1]

        def wrapper(*args, **kwds):
            return tocloud(args[0],
                           method_name if method_name else fun.__name__,
                           *args[1:],
                           **kwds)

        return wrapper

    return inner


class PublicClientPool:
    def __init__(self, makenew=True, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super().__init__(**kwds)
        self.not_quoted = True
        self.service = webapi.PublicServices[0]
        self._poolname = 'Not set'
        self._poolurl = 'Not set'

    def readHK(self):
        """
        loads and returns the housekeeping data in cloud
        """
        poolname = self._poolname
        logger.debug("READ HK FROM REMOTE===>poolurl: " + poolname)
        hk = {}

        # TODO: get hk and handle exceptions
        return hk

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_out=False, **kwds):
        alist = issubclass(products.__class__, list)
        if not alist:
            productlist = [products]
        else:
            productlist = products

        if len(productlist) == 0:
            return []
        # only type and poolname in the urn will be used
        urn = makeUrn(typename=fullname(productlist[0]),
                      poolname=self._poolname, index=0)
        first = True
        sized = '['
        for prd in productlist:
            sp = serialize(prd)
            sized += '%s %d, %s' % ('' if first else ',', len(sp), sp)
            first = False
        sized += ']'

        # TODO: save data to cloud and handle exception
        res = {}

        if alist:
            return serialize(res) if serialize_out else res
        else:
            return serialize(res[0]) if serialize_out else res[0]

    def schematicWipe(self):
        """
        does the scheme-specific remove-all from cloud
        """
        # TODO: remove data from cloud
        # res, msg = delete_from_server(None, self._poolurl, 'pool')
        # if res == 'FAILED':
        #     logger.error(msg)
        #     raise Exception(msg)
        return 0

    def isConnected(self):
        urn = 'urn:::0'
        return read_from_cloud(urn, self._poolurl, 'home')

    def setService(self, service):
        """
        ['storage', 'pool', 'group', 'node', 'data', 'config', 'home']
        """
        if service not in webapi.PublicServices:
            logger.error("Please select a service from: " + str(webapi.PublicServices))
        else:
            self.service = service


p = PublicClientPool()
print(p.isConnected())