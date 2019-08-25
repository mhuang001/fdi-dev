# -*- coding: utf-8 -*-
import filelock
import os
from pathlib import Path
from copy import deepcopy
import collections
import shutil
from urllib.parse import urlparse

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .urn import Urn
from .productref import ProductRef
from .comparable import Comparable
from .common import getJsonObj
from .definable import Definable
from .taggable import Taggable
from .versionable import Versionable

from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict

# Global centralized dict that returns the same ProductStorage+pool.
PoolStorageList = []


class ProductPool(Definable, Taggable, Versionable):
    """
    """

    def __init__(self, poolurn='file:///tmp/pool', **kwds):
        super().__init__(**kwds)
        self._poolurn = poolurn
        sp = poolurn.split('://')
        self._scheme = sp[0]
        self._poolpath = sp[1]
        self._classes = ODict()
        logger.debug(poolpath)

    @staticmethod
    def getPool(poolurn):
        """ returns an instance of pool according to urn.
        """
        sp = poolurn.split('://')
        if sp[0] == 'file':
            return LocalPool(poolurn)
        elif sp[0] == 'mem':
            return MemPool(poolurn)
        else:
            raise ValueError(sp[0] + ':// is not supported')

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """
        self._urns[ref.urn]['refcnt'] -= 1

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """

    def getDefinition(self):
        """
        Returns pool definition info which contains pool type and other pool specific configuration parameters
        """
        return super().getDefinition()

    def getId(self):
        """
        Get the identifier of this pool.
        """
        returns self._poolurn

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        return self._classes.keys()

    def getReferenceCount(self, ref):
        """ 
        Returns the reference count of a ProductRef.
        """
        self._urns[ref.urn]['refcnt'] += 1

    def getUrnId(self):
        """
        Get the identifier of this pool used to build URN, usually it's same as id returned by getId().
        """
        return self.getDefinition()

    def isAlive(self):
        """
        Test if the pool is capable of responding to commands.
        """
        return True

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """
        return len(self._urns) == 0

    def loadDescriptors(self, urn):
        """
        Loads the descriptors belonging to specified URN.
        """
        return self._urns[urn]

    def loadProduct(self, urn):
        """
        Loads a Product belonging to specified URN.
        """

    def meta(self,  urn):
        """ 
        Loads the meta-data belonging to the product of specified URN.
        """

    def reference(self,  ref):
        """ 
        Increment the reference count of a ProductRef.
        """

    def remove(self,  urn):
        """
        Removes a Product belonging to specified URN.
        """

    def removeAll(self, ):
        """
        Remove all pool data (self, products) and all pool meta data (self, descriptors, indices, etc.).
        """

    def saveDescriptors(self,  urn,  desc):
        """
        Save/Update descriptors in pool.
        """

    def doSaving(self, poolpath, typename, serialnum, data):
        """ to be implemented by subckasses to do the media-specific saving
        """

    def saveProduct(self,  product, tag=None):
        """
        Saves specified product and returns the designated URN.
        Save a product or a list of products to the pool, possibly under the supplied tag, and return the reference (or a list of references if the input is a list of products).
        """
        c = self._classes
        t = self._tags
        # save a copy
        cs, ts = deepcopy(c), deepcopy(t)

        poolpath = sp[1]

        if not issubclass(product.__class__, list):
            prds = [product]
        else:
            prds = product
        rfs = []
        for prd in prds:
            pn = prd.__class__.__qualname__

            with filelock.FileLock(poolpath + '/lock'):
                if pn in c:
                    sn = (c[pn]['currentSN'] + 1)
                else:
                    sn = 0
                    c[pn] = ODict({'sn': ODict()})
                if tag is not None:
                    if tag not in t:
                        t[tag] = ODict({pn: []})

                c[pn]['currentSN'] = sn
                s2t = c[pn]['sn']
                if sn in s2t:
                    s2t[sn]['meta'] = prd.meta
                    s2t[sn]['tags'].append(tag)
                else:
                    s2t[sn] = ODict(meta=prd.meta, tags=[tag])

                if tag is not None:
                    t[tag][pn].append(sn)

                try:
                    self.doSaving(poolpath, typename=pn,
                                  serialnum=sn, data=prd)
                except Exception as e:
                    # undo changes
                    c = cl
                    t = ta
                    raise e
            u = Urn(cls=prd.__class__, pool=pool, index=sn)
            rf = ProductRef(urnobj=u)
            # it seems that there is no better way to set meta
            rf._meta = prd.getMeta()
            rfs.append(rf)
        if not issubclass(product.__class__, list):
            return rfs[0]
        else:
            return rfs

    def select(self,  query):
        """
        Returns a list of references to products that match the specified query.
        """

    def select(self,  query,  results):
        """
        Refines a previous query, given the refined query and result of the previous query.
        """
