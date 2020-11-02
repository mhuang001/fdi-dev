# -*- coding: utf-8 -*-
import pdb
from ..pns.pnsconfig import pnsconfig as pc
from ..utils.getconfig import getConfig
from .urn import parse_poolurl

import getpass
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

pc.update(getConfig())

DEFAULT_MEM_POOL = 'defaultmem'
# localpool
DEFAULT_POOL = 'pool_' + getpass.getuser()


class PoolManager(object):
    """
    This class provides the means to reference ProductPool objects without having to hard-code the type of pool. For example, it could be desired to easily switch from one pool type to another.

This is done by calling the getPool() method, which will return an existing pool or create a new one if necessary.
    """
    # Global centralized dict that returns singleton -- the same -- pool for the same ID.
    _GlobalPoolList = {}
    # maps scheme to default place\poolpath
    PlacePaths = {
        'file': '/tmp',
        'mem': '/',
        'http': '127.0.0.1:5000/v0.6',
        'https': '127.0.0.1:5000/v0.6',
        'server': '/tmp/data',
    }

    @classmethod
    def getPool(cls, poolname=None, poolurl=None, **kwds):
        """ returns an instance of pool according to name or path of the pool.

        Returns the pool object if the pool is registered. Creates the pool if it does not already exist. the same poolname-path always get the same pool.

        poolname: name of the pool.
        poolurl: if given the poolpath, scheme, place will be derived from it. if not given, PoolManager.PlacePaths[scheme] is used to get poolplace and poolpath, with scheme set to 'file'. 
If poolname is missing it is derived from poolurl; if poolurl is also absent, DEFAULT_POOL is assumed.
        kwds: passed to pool instanciation arg-list.

        """
        # logger.debug('GPL ' + str(id(cls._GlobalPoolList)) +
        #             str(cls._GlobalPoolList) + ' PConf ' + str(cls.PlacePaths))

        poolpath = None
        if poolname is None:
            if poolurl:
                # the last segment will be the poolname
                poolpath, schm, pl, poolname = parse_poolurl(poolurl)
            else:
                schm = 'file'
                poolname = DEFAULT_POOL
                poolpath = cls.PlacePaths[schm]
                poolurl = schm + '://' + poolpath + '/' + poolname
                logger.debug('DEFAULT_MEM_POOL assumed: %s.' % poolurl)
            if cls.isLoaded(poolname):
                return cls._GlobalPoolList[poolname]
        else:
            if cls.isLoaded(poolname):
                return cls._GlobalPoolList[poolname]
            if poolurl:
                poolpath, schm, pl, pn = parse_poolurl(poolurl)
            else:
                schm = 'file'
                poolpath = cls.PlacePaths[schm]
                poolurl = schm + '://' + poolpath + '/' + poolname
                logger.debug('PlacePaths is used: %s.' % poolurl)

        if schm == 'file':
            from . import localpool
            p = localpool.LocalPool(
                poolname=poolname, poolurl=poolurl, **kwds)
        elif schm == 'mem':
            from . import mempool
            p = mempool.MemPool(poolname=poolname, poolurl=poolurl, **kwds)
        elif schm == 'server':
            from . import httppool
            p = httppool.HttpPool(
                poolname=poolname, poolurl=poolurl, **kwds)
        elif schm in ('http', 'https'):
            from . import httpclientpool
            p = httpclientpool.HttpClientPool(
                poolname=poolname, poolurl=poolurl, **kwds)
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
    def getPoolurlMap(cls):
        """
        Gives the default poolurls of PoolManager.
        """
        return cls.PlacePaths

    @ classmethod
    def setPoolurlMap(cls, new):
        """
        Sets the default poolurls of PoolManager.
        """
        cls.PlacePaths.clear()
        cls.PlacePaths.update(new)

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

    def __repr__(self):
        return self.__class__.__name__ + str(cls._GlobalPoolList)
