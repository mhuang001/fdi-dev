# -*- coding: utf-8 -*-
import pdb
from ..pns.pnsconfig import pnsconfig as pc
from ..utils.getconfig import getConfig

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

pc.update(getConfig())

# from .definable import Definable
DEFAULT_MEM_POOL = 'defaultmem'


class PoolManager(object):
    """
    This class provides the means to reference ProductPool objects without having to hard-code the type of pool. For example, it could be desired to easily switch from one pool type to another.

This is done by calling the getPool(String) method, which will return an existing pool or create a new one if necessary.
    """
    # Global centralized dict that returns singleton -- the same -- pool for the same ID.
    _GlobalPoolList = {}
    # maps scheme to default place\poolpath
    DefaultPlacePoolpath = {
        'file': '/tmp/',
        'mem': '/',
        'http': '127.0.0.1:5000/',
        'https': '127.0.0.1:5000/',
    }

    @classmethod
    def getPool(cls, poolname, pathurl=None, isServer=False):
        """ returns an instance of pool according to name and path-URL of the pool.

        create the pool if it does not already exist. the same poolname-baseURL always get the same pool.
        pathurl: poolURL without the poolname part. if not given, PoolManager.DefaultPlacePoolpath['file'] is used, with scheme set to 'file'.
        """
        # logger.debug('GPL ' + str(id(cls._GlobalPoolList)) +
        #             str(cls._GlobalPoolList) + ' PConf ' + str(cls._PoolConfig))
        if cls.isLoaded(poolname):
            return cls._GlobalPoolList[poolname]
        else:
            if pathurl is None:
                schm = 'file'
                pathurl = schm + '://' + cls.DefaultPlacePoolpath[schm]
            else:
                schm = pathurl.lsplit(':', 1)[0]

            from . import localpool, mempool, httpclientpool, httppool

            if schm == 'file':
                p = localpool.LocalPool(
                    poolname=poolname, pathurl=pathurl)
            elif schm == 'mem':
                p = mempool.MemPool(poolname=poolname)
            elif schm in ('http', 'https'):
                if isServer:
                    p = httppool.HttpPool(
                        poolname=poolname, pathurl=pathurl)
                else:
                    p = httpclientpool.HttpClientPool(
                        poolname=poolname, pathurl=pathurl)
            else:
                raise NotImplementedError(schm + ':// is not supported')
            cls.save(poolname, p)
            logger.debug('made pool ' + str(p))
            return p

    @ classmethod
    def getMap(cls):
        """
        Returns a poolname - poolobject map.
        """
        return cls._GlobalPoolList

    @ classmethod
    def isLoaded(cls, poolname):
        """
        Whether an item with the given id has been loaded (cached).
        """
        return poolname in cls._GlobalPoolList

    @ classmethod
    def removeAll(cls):
        """ deletes all pools from the pool list, pools unwiped
        """

        cls._GlobalPoolList.clear()

    @ classmethod
    def save(cls, poolname, poolobj):
        """
        """
        cls._GlobalPoolList[poolname] = poolobj

    @ classmethod
    def getPathUrlMap(cls):
        """
        Gives the default pathurls of PoolManager.
        """
        return cls.DefaultPlacePoolpath

    @ classmethod
    def setPathUrlMap(cls, new):
        """
        Sets the default pathurls of PoolManager.
        """
        cls.DefaultPlacePoolpath.clear()
        cls.DefaultPlacePoolpath.update(new)

    @ classmethod
    def size(cls):
        """
        Gives the number of entries in this manager.
        """
        return len(cls._GlobalPoolList)

    def items(self):
        """
        Returns map's items
        """
        return self._GlobalPoolList.items()

    def __setitem__(self, *args, **kwargs):
        """ sets value at key.
        """
        self._GlobalPoolList.__setitem__(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        """ returns value at key.
        """
        return self._GlobalPoolList.__getitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        """ removes value and its key.
        """
        self._GlobalPoolList.__delitem__(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        """ size of data
        """
        return self._GlobalPoolList.__len__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        """ returns an iterator
        """
        return self._GlobalPoolList.__iter__(*args, **kwargs)

    @ classmethod
    def __repr__(cls):
        return cls.__name__ + str(cls._GlobalPoolList)
