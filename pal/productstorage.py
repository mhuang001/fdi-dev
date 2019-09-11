# -*- coding: utf-8 -*-
import filelock
from copy import deepcopy
from pathlib import Path
import collections
import shutil
from urllib.parse import urlparse

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .urn import Urn
import pal.productref as ppr
from .productpool import ProductPool
from .poolfactory import getPool

from pns.common import getJsonObj
from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict


class ProductStorage():
    """
    """

    def __init__(self, pool='file:///tmp/pool', **kwds):
        super().__init__(**kwds)
        self._pools = collections.OrderedDict()  # dict of pool-urn keys
        self.register(pool)

    def register(self, pool):
        """ Registers the given pools to the storage.
        """

        if issubclass(pool.__class__, ProductPool):
            self._pools[pool.getId()] = pool
            return

        # check duplicated case
        # if pool in GlobalPoolList:
        #    return

        # check if pool is part of an existing one
        for ex in self._pools:
            lex = ex.split('/')
            lu = pool.split('/')
            ml = min(len(lex), len(lu))
            if lex[:ml] == lu[:ml]:
                raise ValueError(
                    'pool ' + pool + ' and existing ' + ex + ' overlap.')

        self._pools[pool] = getPool(pool)

        logger.debug('registered pool ' + str(self._pools))

    def load(self, urnortag):
        """ Loads a product with a URN or a list of products with a tag, from the pool.  It always creates new ProductRefs. returns productref(s).
        urnortag: urn or tag
        """

        if issubclass(urn.__class__, str):
            if len(urnortag) > 3 and urnortag[0:4] == 'urn:':
                return ppr.ProductRef(urn=urnortag, storage=self)
            else:
                urns = self.getUrnFromTag(urnortag)
                return [ppr.ProductRef(urn=u, storage=self) for u in urns]
        else:
            return ppr.ProductRef(urnortag, storage=self)

    def save(self, product, tag=None, poolurn=None):
        """ saves to the writable pool if it has been registered, if not registers and saves.
        """

        if poolurn == None:
            if len(self._pools) > 0:
                poolurn = self.getWritablePool()
            else:
                raise ValueError('no pool registered')
        elif poolurn not in self._pools:
            self.register(poolurn)

        logger.debug('saving product:' + str(product) +
                     ' to pool ' + str(poolurn) + ' with tag ' + str(tag))

        try:
            ret = self._pools[poolurn].saveProduct(product, tag=tag)
        except Exception as e:
            logger.error('unable to save to the writable pool.')
            raise e

        return ret

    def remove(self, urn):
        """ removes product of urn from the writeable pool
        """
        poolurn = self.getWritablePool()
        logger.debug('removing product:' + str(product) +
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
        mh: in a list of (pool, {'classes','tags'})
        """
        return list(self._pools.keys())

    def getPool(self, pool):
        """ mh: returns  {'classes','tags'}
        """
        if pool not in self._pools:
            raise ValueError('pool ' + pool + ' not found')
        return self._pools[pool]

    def getWritablePool(self):
        return self.getPools()[0]

    def getAllTags(self):
        """ Get all tags defined in the writable pool.
        """
        return self._pools[self.getWritablePool()].getTags()

    def getProductClasses(self, pool):
        """  Yields all Product classes found in this pool.
        """
        return self._pools[pool].getProductClasses()

    def getTags(self, urn):
        """  Get the tags belonging to the writable pool that associated to a given URN.
        returns an iterator.
        """
        return self.getWritablePool().getTags(urn)

    def getMeta(self, urn):
        """  Get the metadata belonging to the writable pool that associated to a given URN.
        returns a dict.
        """
        if not issubclass(urn.__class__, str):
            urn = Urn(urn=urn)

        return self.getWritablePool().meta()

    def getUrnFromTag(self, tag):
        """ Get the URN belonging to the writable pool that is associated
        to a given tag.
        """

        return self.getWritablePool().getUrn(tag)

    def wipePool(self, poolurn):
        """
        """
        if poolurn not in self._pools:
            raise ValueError('pool ' + poolurn + ' not found')
        sp = poolurn.split('://')
        if sp[0] != 'file':
            raise ValueError(sp[0] + ':// is not supported')
        self._pools[poolurn].removeAll()

    def __repr__(self):
        return self.__class__.__name__ + ' { pool= ' + str(self._pools) + ' }'
