# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from . import localpool, mempool

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
    def getPool(cls, poolurn):
        """ returns an instance of pool according to urn. create the pool if it does not already exist. the same pool-URN always get the same pool.
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
            else:
                raise NotImplementedError(sp[0] + ':// is not supported')
            cls.save(poolurn, p)
            logger.debug('made pool ' + str(p))
            return p

    @classmethod
    def getMap(cls):
        """

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

    @classmethod
    def __repr__(cls):
        return cls.__class__.__name__ + str(cls._GlobalPoolList)
