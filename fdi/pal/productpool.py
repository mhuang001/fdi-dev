# -*- coding: utf-8 -*-

from ..dataset.baseproduct import BaseProduct
from ..dataset.classes import Classes
from ..dataset.product import Product
from .urn import Urn, parseUrn, parse_poolurl, makeUrn
from .versionable import Versionable
from .taggable import Taggable
from .definable import Definable
from ..utils.common import (fullname, lls, trbk, pathjoin,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG
                            )
from .query import AbstractQuery, MetaQuery, StorageQuery

from collections import OrderedDict, ChainMap
from functools import lru_cache
import logging
import sys

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    from urllib.parse import urlparse
else:
    PY3 = False
    from urlparse import urlparse

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class PoolNotFoundError(Exception):
    pass


class ProductPool(Definable, Taggable, Versionable):
    """ A mechanism that can store and retrieve Products.

A product pool should not be used directly by users. The general user should access data in a ProductPool through a ProductStorage instance.

When implementing a ProductPool, the following rules need to be applied:

    1. Pools must guarantee that a Product saved via the pool saveProduct(Product) method is stored persistently, and that method returns a unique identifier (URN). If it is not possible to save a Product, an IOException shall be raised.
    2. A saved Product can be retrieved using the loadProduct(Urn) method, using as the argument the same URN that assigned to that Product in the earlier saveProduct(Product) call. No other Product shall be retrievable by that same URN. If this is not possible, an IOException or GeneralSecurityException is raised.
    3. Pools should not implement functionality currently implemented in the core package. Specifically, it should not address functionality provided in the Context abstract class, and it should not implement versioning/cloning support.

    """

    def __init__(self, poolname='', poolurl='', **kwds):
        """
        Creates and initializes a productpool.

        * poolname: if provided will override that in poolurl.
        * poolurl: needed to initialize.

        """
        super().__init__(**kwds)

        # put thesee lines here to avoid `setup`ish entanglement.
        self.setPoolname(poolname)
        self.setPoolurl(poolurl)

        # self._pathurl = pr.netloc + pr.path
        # self._pathurl = None
        self._poolmanager = None
        self.ignore_error_when_delete = False

    class ParametersIncommpleteError(Exception):
        pass

    def setup(self):
        """ Sets up interal machiney of this Pool,
        but only if self._poolname and self._poolurl are present,
        and other pre-requisits are met.

        Subclasses should implement own setup(), and
        make sure that self._poolname and self._poolurl are present with ``

        if <pre-requisit not met>: return True
        if super().setup(): return True

        # super().setup() has done its things by now.
        <do setup>
        return False
``
        returns: Whether to allow subclasses to run their `setup()`s. True if not both  self._poolname and self._poolurl are present, and every thing is GO.

        """
        # if poolname:
        #     self.setPoolname(poolname)

        # if poolurl:
        #     self._poolurl = 'for setup'
        #     self.setPoolurl(poolurl)

        # ._poolname and ._poolurl are determined here. Look no further.
        # if super().setup():
        #    return True

        # if not hasattr(self, '_poolurl') or not self._poolurl:
        return False

    @property
    def poolname(self):
        """ for property getter
        """
        return self.getPoolname()

    @poolname.setter
    def poolname(self, poolname):
        """ for property setter
        """
        self.setPoolname(poolname)

    def getPoolname(self):
        """ Gets the poolname of this pool as an Object. """
        return self._poolname

    def setPoolname(self, poolname):
        """ Replaces the current poolname of this pool.
        """
        self._poolname = poolname

    @property
    def poolurl(self):
        """ for property getter
        """
        return self.getPoolurl()

    @poolurl.setter
    def poolurl(self, poolurl):
        """ for property setter
        """
        self.setPoolurl(poolurl)

    def getPoolurl(self):
        """ Gets the poolurl of this pool as an Object. """
        return self._poolurl

    def setPoolurl(self, poolurl):
        """ Replaces the current poolurl of this pool.
        """
        s = (not hasattr(self, '_poolurl') or not self._poolurl)
        self._poolpath, self._scheme, self._place, \
            self._poolname, self._username, self._password = \
            parse_poolurl(poolurl)
        self._poolurl = poolurl
        # call setup only if poolurl was None
        if s:
            # this will ask all superclasses to run their setup that needs poolurl. This code is not in ``__init__`` because pools can be initialized w/o poolurl..
            self.setup()

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def getPoolManager(self):
        """
        """
        return self._poolmanager

    def setPoolManager(self, pm):
        """
        """
        self._poolmanager = pm

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.

        XXX TODO
        """

        raise (NotImplementedError)

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """

        raise (NotImplementedError)

    def getDefinition(self):
        """
        Returns pool definition info which contains pool type and other pool specific configuration parameters
        """
        return super().getDefinition()

    def getId(self):
        """
        Gets the identifier of this pool.
        """
        return self._poolname

    def getPoolurl(self):
        """
        Gets the pool URL of this pool.
        """
        return self._poolurl

    def getPlace(self):
        """
        Gets the place of this pool.
        """
        return self._place

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        raise (NotImplementedError)

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        raise (NotImplementedError)

    def getScheme(self):
        """
        Gets the scheme of this pool.
        """
        return self._scheme

    def getUrnId(self):
        """
        Get the identifier of this pool used to build URN, usually it's same as id returned by getId().
        """
        return self.getId()

    @staticmethod
    def vectorize(*p):
        """
      ::
        vectorize(9, [8,7,6]) -> ([9, 9, 9], [8, 7,  6], True)
        """

        lens = [len(v) if isinstance(v, (list, tuple)) else 0 for v in p]

        sz = max(lens)
        # remove redundant
        s = set(lens)
        alist = any(s)
        # remove longest and scalar
        s.remove(sz)
        try:
            s.remove(0)
        except KeyError:
            pass
        if len(s):
            # found more than 2 sizes
            raise ValueError(f'Some args have different sizes {s}.')
        if sz == 0:
            # force scalar  to vector
            sz = 1

        res = [q if l else ([q] * sz) for q, l in zip(p, lens)]
        res.append(alist)
        return tuple(res)

    def isAlive(self):
        """
        Test if the pool is capable of responding to commands.
        """
        return True

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """

        raise NotImplementedError

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, asyn=False, **kwds):
        """ to be implemented by subclasses to do the scheme-specific saving
        """
        raise (NotImplementedError)

    def saveProduct(self, product, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, asyn=False, **kwds):
        """
        Saves specified product(s) and returns the designated ProductRefs or URNs.

        Saves a product or a list of products to the pool, possibly under the
        supplied tag(s), and returns the reference (or a list of references if
        the input is a list of products), or Urns if geturnobjs is True.

        See pal document for pool structure.

        Parameters
        ----------
        product : BaseProduct, list
            Product or a list of them or '[ size1, prd, size2, prd2, ...]'.
        tag : str, list
            If given a tag, all products will be having this tag.
        If a list tags are given to every one product then the
        number of tags must not be the same to that of `product`. If
        they are equal, each tag is goven to the product at the same
        index in the `product` list.
        serialize_out : bool
            if `True` returns contents in serialized form.
        serialize_in : bool
            If set, product input is serialized.

        """

        if not (issubclass(product.__class__, BaseProduct)
                or issubclass(product.__class__, str)
                or isinstance(product, list)
                and (issubclass(product[0].__class__, BaseProduct)
                or issubclass(product[0].__class__, str))
                ):
            # p is urn string from server-side LocalPool
            if isinstance(product, list):
                tstr = f'list({product[0].__class__.__name__})'
            else:
                tstr = f'{type(product)}'
            msg = f'Cannot remove a product with a {tstr} as input.'
            raise TypeError(msg)

        res = self.schematicSave(product, tag=tag,
                                 geturnobjs=geturnobjs,
                                 serialize_in=serialize_in,
                                 serialize_out=serialize_out,
                                 asyn=asyn, **kwds)

        if issubclass(product.__class__, str) or\
                isinstance(product, list) and\
                issubclass(product[0].__class__, str):
            # p is urn string from server-side LocalPool, return the str
            return res

        if isinstance(res, list):
            for p, u in zip(product, res):
                p._urn = u if geturnobjs else u.getUrnObj()
        else:
            product._urn = res if geturnobjs else res.getUrnObj()
        return res

    def loadDescriptors(self, urn):
        """
        Loads the descriptors belonging to specified URN.
        """

        raise (NotImplementedError)

    def schematicLoad(self, resourcetype, index,
                      start=None, end=None, serialize_out=False):
        """ to be implemented by subclasses to do the scheme-specific loading
        """
        raise (NotImplementedError)

    def loadProduct(self, urn, serialize_out=False, asyn=False):
        """
        Loads a Product belonging to specified URN.

        serialize_out: if True returns contents in serialized form.
        """
        poolname, resource, index = parseUrn(urn)
        if poolname != self._poolname:
            raise (ValueError('wrong pool: ' + poolname +
                              ' . This is ' + self._poolname))
        ret = self.schematicLoad(
            resourcetype=resource, index=index, serialize_out=serialize_out)

        if issubclass(ret.__class__, str) or isinstance(ret, list) and \
           issubclass(ret[0].__class__, str):
            # ret is a urn string from server-side LocalPool
            return ret

        if isinstance(ret, list):
            logger.warning('TODO: unexpected')
            for x, u in zip(ret, urn):
                x._urn = u
        else:
            ret._urn = urn

        return ret

    def meta(self, urn):
        """
        Loads the meta-data belonging to the product of specified URN.
        """

        raise (NotImplementedError)

    @property
    def count(self):
        """ for property getter
        """
        return self.getCount()

    @count.setter
    def count(self, count):
        """ for property setter
        """
        raise ValueError('Pool.count is read-only.')

    def getCount(self, typename=None):
        """
        Return the number of URNs for the product type.
        """

        raise (NotImplementedError)

    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """

        raise (NotImplementedError)

    def schematicRemove(self, urn=None, resourcetype=None, index=None, asyn=False, **kwds):
        """ to be implemented by subclasses to do the scheme-specific removing
        """
        raise (NotImplementedError)

    def remove(self, urn=None, resourcetype=None, index=None, ignore_error=False, asyn=False, **kwds):
        """
        Removes a Product belonging to specified URN or a pair of data type and serial number.
        """
        self.ignore_error_when_delete = ignore_error
        if not urn and (not resourcetype or not index):
            return 0
        res = self.schematicRemove(
            urn, resourcetype=resourcetype, index=index, asyn=asyn, **kwds)
        return res

    def schematicWipe(self):
        """ to be implemented by subclasses to do the scheme-specific wiping.
        """
        raise (NotImplementedError)

    def schematicGetTag(self):
        """ to be implemented by subclasses to do the scheme-specific tag getting.
        """
        raise (NotImplementedError)

    def schematicRemoveTag(self):
        """ to be implemented by subclasses to do the scheme-specific tag removing.
        """
        raise (NotImplementedError)

    def getTags(self, urn=None, asyn=False, **kwds):
        """ 
        Get all of the tags that map to a given URN or a pair of data type and serial number.

        Get all known tags if urn is not specified.

        If datatype and sn are given, use them and ignore urn.
        """
        # res = self.schematicGetTags(asyn=asyn, **kwds)
        return

    def removeTag(self, tag=None, ignore_error=False, asyn=False, **kwds):
        """
        Removes a tag or a list of tags.

        The associated products are not removed.

        Parameters
        ----------
        asyn : bool
            doing it in parallel.

        Returns
        -------
        int
            0 means OK.

        Raises
        ------
        ValueError
            Target not found.

        Examples
        --------
        FIXME: Add docs.

        """
        self.ignore_error_when_delete = ignore_error
        if not tag:
            return 0

        # res = self.schematicRemoveTag(tag, asyn=asyn, **kwds)
        # return res

    def wipe(self, ignore_error=False, keep=True, asyn=False, **kwds):
        """
        Remove all pool data (self, products) and all pool meta data (self, descriptors, indices, etc.).

        Parameters
        ----------
        keep : boolean
            If set (default) clean up data and metadata but keep the container object.
        """

        r = self.schematicWipe(asyn=asyn, **kwds)
        # try:
        # except ServerError as e:
        #     if ignore_error:
        #         return r
        #     else:
        #         raise
        logger.debug('Removing pool gets {r}')
        return r

    removeAll = wipe
    """ `ProductPool.removeAll` is an aliase for `ProductPool.wipe`."""

    def saveDescriptors(self, urn, desc):
        """
        Save/Update descriptors in pool.
        """
        raise (NotImplementedError)

    def schematicSelect(self,  query, previous=None):
        """
        to be implemented by subclasses to do the scheme-specific querying.
        """
        raise (NotImplementedError)

    def select(self,  query, variable='m', ptype=Product,
               previous=None):
        """Returns a list of references to products that match the specified query.

        Parameters
        ----------
        query : str
            the 'where' query string to make a query object.
        variable : str
            name of the dummy variable in the query string.
            if `variable` is 'm', query goes via `MetaQuery(ptype, query)` ; else by `AbstractQuery(ptype, variable, query)` .
        ptype : class
            The class object whose instances are to be queried. Or
            fragment of the name of such classes.
        previous : list or str
            of urns, possibly from previous search. or a string of comma-separated urns, e.g. `'urn:a:foo:12,urn:b:bar:9'`

        Returns
        -------
        list
            of found URNs.

        """
        if issubclass(previous.__class__, str):
            previous = previous.split(',')
        if issubclass(query.__class__, StorageQuery):
            res = self.schematicSelect(query, previous)
            return res
        if issubclass(ptype.__class__, str):
            for cn, cls in Classes.mapping.items():
                if ptype in cn and issubclass(cls, BaseProduct):
                    break
            else:
                raise (ValueError(ptype + ' is not a product type.'))
            ptype = cls
        if variable == 'm':
            res = self.schematicSelect(MetaQuery(ptype, where=query), previous)
        else:
            res = self.schematicSelect(AbstractQuery(
                ptype, where=query, variable=variable), previous)
        return res

    def qm(self, qw, prod='BaseProduct', urns=None):
        """ short-hand method for `select(qw, variable'm', ptype=prod, previous=urns`.

        example:
        ..code:
        curl http://foo.edu:23456/data/pool/api/qm__m["age"]>66 and m["name"]=="Bob"'
        """
        return self.select(qw, variable='m', ptype=prod, previous=urns)

    def __repr__(self):
        co = ', '.join(str(k) + '=' + lls(v, 40)
                       for k, v in self.__getstate__().items())
        # co = ', '.join(str(k)+'=' + (v if issubclass(v.__class__, str) else
        #                              '<' + v.__class__.__name__+'>') \
        #                for k, v in self.__getstate__().items())
        return '<'+self.__class__.__name__ + ' ' + co + '>'

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(
            poolurl=self._poolurl if hasattr(self, '_poolurl') else None,
        )

###########################
