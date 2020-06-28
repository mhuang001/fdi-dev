# -*- coding: utf-8 -*-
import filelock
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


from . import productpool


class MemPool(productpool.ProductPool):
    """ the pool will save all products in memory.
    """

    _MemPool = {}

    def __init__(self, **kwds):
        """ creates data structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super(MemPool, self).__init__(**kwds)

        logger.debug(self._poolpath)
        if self._poolpath not in self._MemPool:
            self._MemPool[self._poolpath] = {}
        c, t, u = self.readHK()

        logger.debug('pool ' + self._place + self._poolurn + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def getPoolSpace(self):
        """ returns the map of this memory pool.
        """
        return self._MemPool[self._poolpath]

    def readHK(self):
        """
        loads and returns the housekeeping data
        """
        myspace = self.getPoolSpace()
        if len(myspace) == 0:
            return {}, {}, {}
        else:
            return myspace['classes'], myspace['tags'], myspace['urns']

    def writeHK(self, fp0):
        """
           save the housekeeping data to mempool
        """

        myspace = self._MemPool[fp0]
        myspace['classes'] = self._classes
        myspace['tags'] = self._tags
        myspace['urns'] = self._urns

    def schematicSave(self, typename, serialnum, data):
        """ 
        does the media-specific saving
        """
        fp0 = self._poolpath
        resourcep = typename + '_' + str(serialnum)
        myspace = self.getPoolSpace()
        myspace[resourcep] = data
        self.writeHK(fp0)
        logger.debug('HK written')

    def schematicLoadProduct(self, resourcename, indexstr):
        """
        does the scheme-specific part of loadProduct.
        note that the index is given as a string.
        """
        fp0 = self._poolpath
        resourcep = resourcename + '_' + indexstr
        myspace = self.getPoolSpace()
        return myspace[resourcep]

    def schematicRemove(self, typename, serialnum):
        """
        does the scheme-specific part of removal.
        """
        fp0 = (self._poolpath)
        resourcep = typename + '_' + str(serialnum)
        myspace = self.getPoolSpace()
        del myspace[resourcep]
        self.writeHK(fp0)

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """

        # logger.debug()
        # p=self.getSpace() ; del p will only delete p, not anything in _MemPool
        pools = [x for x in self._MemPool]
        for x in pools:
            del self._MemPool[x]

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
