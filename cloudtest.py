import logging
import sys

from fdi.pal.productpool import ProductPool
from fdi.pal.urn import makeUrn
from fdi.dataset.deserialize import serialize_args
from fdi.dataset.serializable import serialize
from fdi.pal import webapi
from fdi.pns.public_fdi_requests import get_service_method, datatype_from_cloud
from fdi.utils.common import fullname
from fdi.utils.getconfig import getConfig

logger = logging.getLogger(__name__)

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
    apipath = serialize_args(method, *args, not_quoted=self.not_quoted, **kwds)
    print(apipath)
    service, serviceName = get_service_method(method)
    if service == webapi.PublicServices[0]:
        # print(kwds)
        res = datatype_from_cloud(service, serviceName, *args, **kwds)
    else:
        res = ''
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
    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super().__init__(**kwds)
        self.not_quoted = True

    @toCloud()
    def is_connected(self):
        pass

    @toCloud()
    def datatype_delete(self, dataType=None):
        pass

    @toCloud()
    def datatype_list(self, dataType=None, key=None):
        pass

    @toCloud()
    def datatype_listNode(self, dataType=None, key=None):
        """
        列出指定产品类型属性节点值
        """
        pass

    @toCloud()
    def datatype_listMeta(self, dataType=None):
        pass

    # @toCloud()
    # def datatype_show_name(self):
    #     pass

    @toCloud()
    def datatype_upload(self, dataFilePath='', productType='', arguments=None):
        pass


pool = PublicClientPool()
# print(pool.datatype_list())
# print(pool.datatype_list('fits'))
# print(pool.datatype_listNode('data', 'fits'))
# print(pool.datatype_listMeta('fits'))
# print(pool.datatype_listMeta('da', 'adj'))
filePath = '/home/tearsyu/Documents/fdi/tests/resources/datatype_test.txt'
myArgs = {"radius:324"}
print(pool.datatype_upload(dataFilePath=filePath, productType='DATATYPE_TEST',   arguments=myArgs))
# pool.datatype_show_productType_attributes('a', 'b')
# args = {'a': [1, 2], 'b': 'sdf'}
# ptype = [1, 2, 3]
# pool.datatype_upload('filepath', ptype, args)
# pool.datatype_delete('Commex')