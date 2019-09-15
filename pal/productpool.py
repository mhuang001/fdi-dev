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

from .urn import Urn, makeUrn, parseUrn
from .productref import ProductRef
from .common import getProductObject
from .definable import Definable
from .taggable import Taggable
from .versionable import Versionable

from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict

lockpath = '/tmp'


class ProductPool(Definable, Taggable, Versionable):
    """
    """

    def __init__(self, poolurn='file:///tmp/pool', **kwds):
        super().__init__(**kwds)
        self._poolurn = poolurn
        pr = urlparse(poolurn)
        self._scheme = pr.scheme
        self._place = pr.netloc
        # convenient access path
        self._poolpath = pr.netloc + \
            pr.path if pr.scheme in ('file', 'mem') else pr.path
        # {type|classname -> {'sn:[sn]'}}
        self._classes = ODict()
        logger.debug(self._poolpath)

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """
        self._urns[ref.urn]['refcnt'] -= 1

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """
        return urn in self._urns

    def getDefinition(self):
        """
        Returns pool definition info which contains pool type and other pool specific configuration parameters
        """
        return super().getDefinition()

    def getId(self):
        """
        Gets the identifier of this pool.
        """
        return self._poolurn

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
        return self.getId()

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
        return getProductObject(urn)

    def meta(self,  urn):
        """ 
        Loads the meta-data belonging to the product of specified URN.
        """
        return self._urns[urn]['meta']

    def reference(self,  ref):
        """ 
        Increment the reference count of a ProductRef.
        """

    def schematicRemove(self,  typename, serialnum):
        """ to be implemented by subckasses to do the scheme-specific removing
        """
        pass

    def remove(self,  urn):
        """
        Removes a Product belonging to specified URN.
        """

        poolname, resourcecn, indexs, scheme, place, poolpath = \
            parseUrn(urn)

        if self._poolurn != poolname:
            raise ValueError(
                urn + ' is not from the pool ' + pool)

        prod = resourcecn
        sn = int(indexs)

        c, t, u = self._classes, self._tags, self._urns
        # save a copy for rolling back
        cs, ts, us = deepcopy(c), deepcopy(t), deepcopy(u)

        if urn not in u:
            raise ValueError(
                '%s not found in pool %s.' % (urn, self.getId()))

        with filelock.FileLock(lockpath + '/lock'):
            self.removeUrn(urn)
            c[prod]['sn'].remove(sn)
            if len(c[prod]['sn']) == 0:
                del c[prod]
            try:
                self.schematicRemove(typename=prod,
                                     serialnum=sn)
            except Exception as e:
                msg = 'product ' + urn + ' removal failed'
                logger.debug(msg)
                # undo changes
                c, t, u = cs, ts, us
                raise e

    def removeAll(self):
        """
        Remove all pool data (self, products) and all pool meta data (self, descriptors, indices, etc.).
        """

        try:
            self.schematicWipe()
        except Exception as e:
            msg = self.getId() + 'wiping failed'
            logger.debug(msg)
            raise e
        self._classes.clear()
        self._tags.clear()
        self._urns.clear()
        logger.debug('Done.')

    def saveDescriptors(self,  urn,  desc):
        """
        Save/Update descriptors in pool.
        """

    def schematicSave(self,  typename, serialnum, data):
        """ to be implemented by subckasses to do the scheme-specific saving
        """
        pass

    def saveProduct(self,  product, tag=None):
        """
        Saves specified product and returns the designated URN.
        Saves a product or a list of products to the pool, possibly under the supplied tag, and return the reference (or a list of references if the input is a list of products).
        """
        c, t, u = self._classes, self._tags, self._urns
        # save a copy
        cs, ts, us = deepcopy(c), deepcopy(t), deepcopy(u)

        if not issubclass(product.__class__, list):
            prds = [product]
        else:
            prds = product
        rfs = []
        for prd in prds:
            pn = prd.__class__.__qualname__

            with filelock.FileLock(lockpath + '/lock'):
                if pn in c:
                    sn = (c[pn]['currentSN'] + 1)
                else:
                    sn = 0
                    c[pn] = ODict(sn=[])

                c[pn]['currentSN'] = sn
                c[pn]['sn'].append(sn)
                urnobj = Urn(cls=prd.__class__, pool=self._poolurn, index=sn)
                urn = urnobj.urn

                if urn not in u:
                    u[urn] = ODict(tags=[], meta=prd.meta)

                if tag is not None:
                    self.setTag(tag, urn)

                try:
                    self.schematicSave(typename=pn,
                                       serialnum=sn,
                                       data=prd)
                except Exception as e:
                    msg = 'product ' + urn + ' saving failed'
                    logger.debug(msg)
                    # undo changes
                    c, t, u = cs, ts, us
                    raise e

            rf = ProductRef(urn=urnobj)
            # it seems that there is no better way to set meta
            rf._meta = prd.getMeta()
            rfs.append(rf)
        logger.debug('generated prefs ' + str(len(rfs)))
        if issubclass(product.__class__, list):
            return rfs
        else:
            return rfs[0]

    def select(self,  query):
        """
        Returns a list of references to products that match the specified query.
        """
        c, t, u = self._classes, self._tags, self._urns
        cs, ts, us = deepcopy(c), deepcopy(t), deepcopy(u)
        return

    def select(self,  query,  results):
        """
        Refines a previous query, given the refined query and result of the previous query.
        """
        return

    def __repr__(self):
        return self.__class__.__name__ + ' { pool= ' + str(self._poolurn) + ' }'
