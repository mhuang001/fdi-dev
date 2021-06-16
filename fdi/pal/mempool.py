# -*- coding: utf-8 -*-
from .productpool import ManagedPool
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class MemPool(ManagedPool):
    """ the pool will save all products in memory.
    """

    def __init__(self, **kwds):
        """ creates data structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """

        super(MemPool, self).__init__(**kwds)

    def setup(self):
        """ Sets up MemPool interals.

        make sure that self._poolname and self._poolurl are present.
        """

        if super().setup():
            return True

        self._MemPool = {}
        # if self._poolname not in self._MemPool:
        #      self._MemPool[self._poolname] = {}
        c, t, u = tuple(self.readHK().values())

        logger.debug('created ' + self.__class__.__name__ +
                     ' ' + self._poolname + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

        return False

    def getPoolSpace(self):
        """ returns the map of this memory pool.
        """
        return self._MemPool
        # if self._poolname in self._MemPool:
        #     return self._MemPool[self._poolname]
        # else:
        #     return None

    def readHK(self, hktype=None, serialize_in=True, serialize_out=False):
        """
        loads and returns the housekeeping data

        hktype: one of 'classes', 'tags', 'urns' to return. default is None to return alldirs
        serialize_out: if True return serialized form. Default is false.
        """

        if serialize_out:
            raise NotImplementedError
        if hktype is None:
            hks = ['classes', 'tags', 'urns']
        else:
            hks = [hktype]
        hk = {}
        myspace = self.getPoolSpace()
        for hkdata in hks:
            if len(myspace) == 0:
                r = {}
            else:
                r = myspace[hkdata]
            hk[hkdata] = r
        logger.debug('HK read from ' + self._poolname)
        return hk if hktype is None else hk[hktype]

    def writeHK(self):
        """
           save the housekeeping data to mempool
        """

        myspace = self.getPoolSpace()
        myspace['classes'] = self._classes
        myspace['tags'] = self._tags
        myspace['urns'] = self._urns

    def doSave(self, resourcetype, index, data, tag=None, serialize_in=True, **kwds):
        """ 
        does the media-specific saving
        """
        resourcep = resourcetype + '_' + str(index)
        myspace = self.getPoolSpace()
        myspace[resourcep] = data
        self.writeHK()
        logger.debug('HK written')

    def doLoad(self, resourcetype, index, serialize_out=False):
        """
        does the action of loadProduct.
        note that the index is given as a string.
        """
        if serialize_out:
            raise NotImplementedError
        indexstr = str(index)
        resourcep = resourcetype + '_' + indexstr
        myspace = self.getPoolSpace()
        return myspace[resourcep]

    def doRemove(self, resourcetype, index):
        """
        does the action of removal.
        """
        resourcep = resourcetype + '_' + str(index)
        myspace = self.getPoolSpace()
        del myspace[resourcep]
        self.writeHK()

    def doWipe(self):
        """
        does the action of remove-all
        """

        # logger.debug()
        p = self.getPoolSpace()
        p.clear()

        # del p will only delete p in current namespace, not anything in _MemPool
        # this wipes all mempools
        # pools = [x for x in self._MemPool]
        # for x in pools:
        #    del self._MemPool[x]
        # if self._poolname in self._MemPool:
        #    del self._MemPool[self._poolname]

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
