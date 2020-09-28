# -*- coding: utf-8 -*-
from . import productref
from .poolmanager import PoolManager
from .productpool import ProductPool
from .urn import Urn
from ..dataset.odict import ODict
import collections
import getpass

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


#from .productpool import ProductPool
DefaultPool = 'file:///tmp/pool_' + getpass.getuser()


class ProductStorage(object):
    """ Logical store created from a pool or a poolURN.

    Every instanciation with the same pool will  result in a new instance of ProdStorage.
    """

    def __init__(self, pool=None, isServer=False, **kwds):
        """ input is a pool urn
        """
        if not pool:
            pool = DefaultPool

        super(ProductStorage, self).__init__(**kwds)
        self._pools = ODict()  # dict of pool-urn keys
        self.isServer = isServer
        self.register(pool)

    def register(self, pool):
        """ Registers the given pools to the storage.
        """

        if issubclass(pool.__class__, ProductPool):
            self._pools[pool.getId()] = pool
            return

        # check if pool is part of an existing one
        for ex in self._pools:
            lex = ex.split('/')
            lu = pool.split('/')
            ml = min(len(lex), len(lu))
            if lex[:ml] == lu[:ml]:
                raise ValueError(
                    'pool ' + pool + ' and existing ' + ex + ' overlap.')
        self._pools[pool] = PoolManager.getPool(pool, self. isServer)

        logger.debug('registered pool ' + str(self._pools))

    def load(self, urnortag):
        """ Loads a product with a URN or a list of products with a tag, from the (writeable) pool.  It always creates new ProductRefs.
        returns productref(s).
        urnortag: urn or tag
        """
        poolurn = self.getWritablePool()

        def runner(urnortag):
            if issubclass(urnortag.__class__, list):
                ulist = []
                [ulist.append(runner(x)) for x in urnortag]
                return ulist
            else:
                if issubclass(urnortag.__class__, str):
                    if len(urnortag) > 3 and urnortag[0:4] == 'urn:':
                        urns = [urnortag]
                    else:
                        urns = self.getUrnFromTag(urnortag)
                elif issubclass(urnortag.__class__, Urn):
                    urns = [urnortag.urn]
                else:
                    raise ValueError(
                        'must provide urn, urnobj, tags, or lists of them')
                ret = []
                for x in urns:
                    pr = productref.ProductRef(x, poolurn)
                    ret.append(pr)
                return ret
        ls = runner(urnortag=urnortag)
        # return a list only when more than one refs
        return ls if len(ls) > 1 else ls[0]

    def save(self, product, tag=None, poolurn=None, geturnobjs=False):
        """ saves to the writable pool if it has been registered.
        if not, registers and saves. product can be one or a list of prpoducts.
        Returns: one or a list of productref with storage info. mh: or UrnObjs if geturnobjs is True.
        """

        if poolurn == None:
            if len(self._pools) > 0:
                poolurn = self.getWritablePool()
            else:
                raise ValueError('no pool registered')
        elif poolurn not in self._pools:
            self.register(poolurn)

        desc = [x.description for x in product] if issubclass(
            product.__class__, list) else product.description
        logger.debug('saving product:' + str(desc) +
                     ' to pool ' + str(poolurn) + ' with tag ' + str(tag))

        try:
            ret = self._pools[poolurn].saveProduct(
                product, tag=tag, geturnobjs=geturnobjs)
        except Exception as e:
            logger.error('unable to save to the writable pool.')
            raise e
        if not geturnobjs:
            if issubclass(ret.__class__, list):
                for x in ret:
                    x.setStorage(self)
            else:
                ret.setStorage(self)
        return ret

    def remove(self, urn):
        """ removes product of urn from the writeable pool
        """
        poolurn = self.getWritablePool()
        logger.debug('removing product:' + str(urn) +
                     ' from pool ' + str(poolurn))
        try:
            self._pools[poolurn].remove(urn)
        except Exception as e:
            logger.error('unable to remove from the writable pool.')
            raise e

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """

    def getPools(self):
        """  Returns the set of ProductPools registered.
        mh: in a list of poolurns
        """
        return list(self._pools.keys())

    def getPool(self, poolurn):
        """ mh: returns the pool object from poolurn
        """
        if poolurn not in self._pools:
            raise ValueError('pool ' + poolurn + ' not found')
        return self._pools[poolurn]

    def getWritablePool(self):
        """ returns the poolurn of the first pool, which is the only writeable pool.
        """
        return self.getPools()[0]

    def getAllTags(self):
        """ Get all tags defined in the writable pool.
        """
        return self._pools[self.getWritablePool()].getTags()

    def getProductClasses(self, poolurn):
        """  Yields all Product classes found in this pool.
        """
        return self._pools[poolurn].getProductClasses()

    def getTags(self, urn):
        """  Get the tags belonging to the writable pool that associated to a given URN.
        returns an iterator.
        """
        return self._pools[self.getWritablePool()].getTags(urn)

    def getMeta(self, urn):
        """  Get the metadata belonging to the writable pool that associated to a given URN.
        returns an ODict.
        """
        if not issubclass(urn.__class__, str):
            urn = urn.urn

        return self._pools[self.getWritablePool()].meta(urn)

    def getUrnFromTag(self, tag):
        """ Get the URN belonging to the writable pool that is associated
        to a given tag.
        """

        return self._pools[self.getWritablePool()].getUrn(tag)

    def wipePool(self, poolurn):
        """
        """
        if poolurn not in self._pools:
            raise ValueError('pool ' + poolurn + ' not found')
        sp = poolurn.split('://')
        if sp[0] not in ['file', 'mem', 'http', 'https']:
            raise ValueError(sp[0] + ':// is not supported')
        self._pools[poolurn].removeAll()

    def select(self, query, previous=None):
        """ Returns a list of URNs to products that match the specified query.

        Parameters:
        query - the query object
        previous - results to be refined
        Returns:
        the set of return eferences to products matching the supplied query.
        """
        ret = []
        for poolnm, pool in self._pools.items():
            c, t, u = pool._classes, pool._tags, pool._urns
            ret += pool.select(query, previous)
        return ret

    def __eq__(self, o):
        """ has the same urn of the writable pool.
        """
        return self.getWritablePool() == o.getWritablePool()

    def __repr__(self):
        return self.__class__.__name__ + ' { pool= ' + str(self._pools) + ' }'
