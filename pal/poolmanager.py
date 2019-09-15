# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

import pal.localpool as plp

#from .definable import Definable


class PoolManager():
    """
    This class provides the means to reference ProductPool objects without having to hard-code the type of pool. For example, it could be desired to easily switch from one pool type to another.

This is done by calling the getPool(String) method, which will return an existing pool or create a new one if necessary.
    """
    # Global centralized dict that returns singleton -- the same -- pool for the same ID.
    _GlobalPoolList = {}

    def getPool(self, poolurn):
        """ returns an instance of pool according to urn. create the pool if it does not already exist. the same pool-URN always get the same pool.
        """
        sp = poolurn.split('://')
        # logger.debug('GPL ' + str(id(self._GlobalPoolList)) +
        #             str(self._GlobalPoolList))
        if self.isLoaded(poolurn):
            return self._GlobalPoolList[poolurn]
        else:
            if sp[0] == 'file':
                p = plp.LocalPool(poolurn=poolurn)
            # elif sp[0] == 'mem':
             #   return  # MemPool(poolurn)
            else:
                raise ValueError(sp[0] + ':// is not supported')
            self.save(poolurn, p)
            logger.debug('made pool ' + str(p))
            return p

    def getMap(self):
        """

        """
        return self._GlobalPoolList

    def isLoaded(self, poolurn):
        """
        Whether an item with the given id has been loaded (cached).
        """
        return poolurn in self._GlobalPoolList

    def removeAll(self):
        """ deletes all pools 
        """

        self._GlobalPoolList.clear()

    def save(self, poolurn, poolobj):
        """
        """
        self._GlobalPoolList[poolurn] = poolobj

    def size(self):
        """
        Gives the number of entries in this manager.
        """
        return len(self._GlobalPoolList)

    def __repr__(self):
        return self.__class__.__name__ + str(self._GlobalPoolList)
