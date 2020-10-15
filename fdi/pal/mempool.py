# -*- coding: utf-8 -*-
from .productpool import ProductPool
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class MemPool(ProductPool):
    """ the pool will save all products in memory.
    """

    _MemPool = {}

    def __init__(self, **kwds):
        """ creates data structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """

        super(MemPool, self).__init__(**kwds)

        if self._poolname not in self._MemPool:
            self._MemPool[self._poolname] = {}
        c, t, u = self.readHK()

        logger.debug('created ' + self.__class__.__name__ +
                     ' ' + self._poolurn + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def getPoolSpace(self):
        """ returns the map of this memory pool.
        """

        if self._poolname in self._MemPool:
            return self._MemPool[self._poolname]
        else:
            return None

    def readHK(self):
        """
        loads and returns the housekeeping data
        """
        myspace = self.getPoolSpace()
        if len(myspace) == 0:
            return {}, {}, {}
        else:
            return myspace['classes'], myspace['tags'], myspace['urns']

    def writeHK(self):
        """
           save the housekeeping data to mempool
        """

        myspace = self.getPoolSpace()
        myspace['classes'] = self._classes
        myspace['tags'] = self._tags
        myspace['urns'] = self._urns

    def schematicSave(self, resourcetype, index, data, tag=None):
        """ 
        does the media-specific saving
        """
        resourcep = resourcetype + '_' + str(index)
        myspace = self.getPoolSpace()
        myspace[resourcep] = data
        self.writeHK()
        logger.debug('HK written')

    def schematicLoadProduct(self, resourcetype, index):
        """
        does the scheme-specific part of loadProduct.
        note that the index is given as a string.
        """
        indexstr = str(index)
        resourcep = resourcetype + '_' + indexstr
        myspace = self.getPoolSpace()
        return myspace[resourcep]

    def schematicRemove(self, resourcetype, index):
        """
        does the scheme-specific part of removal.
        """
        resourcep = resourcetype + '_' + str(index)
        myspace = self.getPoolSpace()
        del myspace[resourcep]
        self.writeHK()

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """

        # logger.debug()
        # p = self.getPoolSpace()
        # del p will only delete p in current namespace, not anything in _MemPool
        # this wipes all mempools
        #pools = [x for x in self._MemPool]
        # for x in pools:
        #    del self._MemPool[x]
        if self._poolname in self._MemPool:
            del self._MemPool[self._poolname]

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
