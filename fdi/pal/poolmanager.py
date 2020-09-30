# -*- coding: utf-8 -*-
from . import localpool, mempool, httpclientpool, httppool
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


#from .definable import Definable
DEFAULT_MEM_POOL = 'mem:///default'


class PoolManager(object):
    """
    This class provides the means to reference ProductPool objects without having to hard-code the type of pool. For example, it could be desired to easily switch from one pool type to another.

This is done by calling the getPool(String) method, which will return an existing pool or create a new one if necessary.
    """
    # Global centralized dict that returns singleton -- the same -- pool for the same ID.
    _GlobalPoolList = {}

    @classmethod
    def getPool(cls, poolurn, isServer=False):
        """ returns an instance of pool according to urn.

        create the pool if it does not already exist. the same pool-URN always get the same pool.
        """
        # logger.debug('GPL ' + str(id(cls._GlobalPoolList)) +
        #             str(cls._GlobalPoolList))
        if cls.isLoaded(poolurn):
            return cls._GlobalPoolList[poolurn]
        else:
            sp = poolurn.split('://')
            if sp[0] == 'file':
                p = localpool.LocalPool(poolurn=poolurn)
            elif sp[0] == 'mem':
                p = mempool.MemPool(poolurn=poolurn)
            elif (sp[0] == 'http' or sp[0] == 'https') and isServer == False:
                p = httpclientpool.HttpClientPool(poolurn=poolurn)
            elif (sp[0] == 'http' or sp[0] == 'https') and isServer == True:
                p = httppool.HttpPool(poolurn=poolurn)
            else:
                raise NotImplementedError(sp[0] + ':// is not supported')
            cls.save(poolurn, p)
            logger.debug('made pool ' + str(p))
            return p

    @classmethod
    def getMap(cls):
        """
        Returns a poolname - poolobject map.
        """
        return cls._GlobalPoolList


    @classmethod
    def isLoaded(cls, poolurn):
        """
        Whether an item with the given id has been loaded (cached).
        """
        return poolurn in cls._GlobalPoolList

    @classmethod
    def removeAll(cls):
        """ deletes all pools from the pool list, pools unwiped
        """

        cls._GlobalPoolList.clear()

    @classmethod
    def save(cls, poolurn, poolobj):
        """
        """
        cls._GlobalPoolList[poolurn] = poolobj

    @classmethod
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

    @classmethod
    def __repr__(cls):
        return cls.__name__ + str(cls._GlobalPoolList)
