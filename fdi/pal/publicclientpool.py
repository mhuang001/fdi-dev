import logging
import sys

from .productpool import ManagedPool
from .urn import makeUrn
from ..dataset.deserialize import serialize_args
from ..dataset.serializable import serialize
from ..pal import webapi
from ..pns.public_fdi_requests import read_from_cloud
from ..utils.common import fullname
from ..utils.getconfig import getConfig

logger = logging.getLogger(__name__)
pcc = getConfig()

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


class PublicClientPool(ManagedPool):
    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super().__init__(**kwds)

    def setup(self):
        """ Sets up HttpPool interals.

        Make sure that self._poolname and self._poolurl are present.
        """

        if super().setup():
            return True

        return False

    def isAvailable(self):
        pass

    def getToken(self):
        pass

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """
        return urn in self._urns

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        return self._classes.keys()

    def getCount(self, typename):
        """
        Return the number of URNs for the product type.
        """
        try:
            return len(self._classes[typename]['sn'])
        except KeyError:
            return 0

    def doSave(self, resourcetype, index, data, tag=None, serialize_in=True, **kwds):
        """ to be implemented by subclasses to do the action of saving
        """
        raise(NotImplementedError)

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """
        return len(self._urns) == 0

    def getMetaByUrn(self, urn, resourcetype=None, index=None):
        """
        Get all of the meta data belonging to a product of a given URN.

        mh: returns an iterator.
        """
        raise NotImplemented

    def meta(self,  urn):
        """
        Loads the meta-data info belonging to the product of specified URN.
        """
        return self.getMetaByUrn(urn)

    def saveOne(self, prd, tag, geturnobjs, serialize_in, serialize_out, res, kwds):
        pass

    def doLoad(self, resourcetype, index, start=None, end=None, serialize_out=False):
        """ to be implemented by subclasses to do the action of loading
        """
        raise(NotImplementedError)

    def doRemove(self, resourcetype, index):
        """ to be implemented by subclasses to do the action of reemoving
        """
        raise(NotImplementedError)

    def doWipe(self):
        """ to be implemented by subclasses to do the action of wiping.
        """
        raise(NotImplementedError)

    def meta_filter(self, q, typename=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q is a MetaQuery
        valid inputs: typename and ns list; productref list; urn list
        """
        pass

    def prod_filter(self, q, cls=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q: an AbstractQuery.
        valid inputs: cls and ns list; productref list; urn list
        """

    def doSelect(self, query, results=None):
        """
        to be implemented by subclasses to do the action of querying.
        """
        raise(NotImplementedError)