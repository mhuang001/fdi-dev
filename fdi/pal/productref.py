# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
from .context import Context
from .urn import Urn
from .comparable import Comparable
from ..dataset.product import Product
from ..dataset.odict import ODict
from ..dataset.serializable import Serializable
from ..dataset.attributable import Attributable
from ..dataset.eq import DeepEqual

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class ProductRef(Attributable, DeepEqual, Serializable, Comparable):
    """ A lightweight reference to a product that is stored in a ProductPool or in memory.
    """

    def __init__(self, urn=None, poolname=None, product=None, meta=None, **kwds):
        """ Urn can be the string or URNobject. if product is provided create an in-memory URN.
        Poolname if given overrides the pool name in urn, and causes metadata to be loaded from pool, unless this prodref points to a mempool.
        If meta is given, it will be used instead of that from poolname.
        A productref created from a single product will result in a memory pool urn, and the metadata won't be loaded.
        """

        urnobj = None
        super(ProductRef, self).__init__(**kwds)
        if issubclass(urn.__class__, str):
            urnobj = Urn(urn)
        elif issubclass(urn.__class__, Urn):
            urnobj = urn
        elif issubclass(urn.__class__, Product):
            # allow ProductRef(p) where p is a Product
            if product is None:
                product = urn
        else:
            urnobj = None

        if product is not None:
            from .poolmanager import PoolManager, DEFAULT_MEM_POOL
            from . import productstorage
            pool = PoolManager.getPool(poolurl='mem:///' + DEFAULT_MEM_POOL)
            st = productstorage.ProductStorage(pool)
            urnobj = st.save(product, geturnobjs=True)
            # a lone product passed to prodref will be stored to mempool

        self.setUrnObj(urnobj, poolname, meta)

        if product and isinstance(product, Context):
            self._product = product

        self._parents = []

    @property
    def product(self):
        return self.getProduct()

    def getProduct(self):
        """ Get the product that this reference points to.

        If the product is a Context, it is kept internally, so further accesses don't need to ask the storage for loading it again.
        Otherwise, the product is returned but the internal reference remains null, so every call to this method involves a request to the storage.

        This way, heavy products are not kept in memory after calling this method, thus maintaining the ProductRef a lighweight reference to the target product.

        In case of a Context, if it is wanted to free the reference, call unload().

        Returns:
        the product
        """

        if self._poolname is None:
            return None
        if hasattr(self, '_product') and self._product is not None:
            return self._product
        from .poolmanager import PoolManager
        p = PoolManager.getPool(self._poolname).loadProduct(self.getUrn())
        if issubclass(p.__class__, Context):
            self._product = p
        return p

    def getPoolname(self):
        """ Returns the name of the product pool associated.
        """
        return self._poolname

    def getStorage(self):
        """ Returns the product storage associated.
        """
        raise NotImplementedError
        return self._storage

    def setStorage(self, storage):
        """ Sets the product storage associated.
        """
        raise NotImplementedError
        self._storage = storage
        # if hasattr(self, '_urn') and self._urn:
        #    self._meta = self._storage.getMeta(self._urn)

    def getType(self):
        """ Specifies the Product class to which this Product reference is pointing to.
        """
        return self._urnobj.getType()

    @property
    def urn(self):
        """ Property """
        return self.getUrn()

    @urn.setter
    def urn(self, urn):
        """
        """
        self.setUrn(urn)

    def setUrn(self, urn):
        """
        """
        self.setUrnObj(Urn(urn))

    def getUrn(self):
        """ Returns the Uniform Resource Name (URN) of the product.
        """
        return self._urnobj.urn

    @property
    def urnobj(self):
        """ Property """
        return self.getUrnObj()

    @urnobj.setter
    def urnobj(self, urnobj):
        """
        """
        self.setUrnObj(urnobj)

    def setUrnObj(self, urnobj, poolname=None, meta=None):
        """ sets urn

        A productref created from a single product will result in a memory pool urn, and the metadata won't be loaded.

        Parameters:
        -----------
        urnobj: Urn
        a URN object.
        poolname: str
        if given overrides the pool name in urn, and causes metadata to be loaded from pool.
        meta: MetaData
        If  is given, it will be used instead of that from poolname.
        """
        if urnobj is not None:
            # logger.debug(urnobj)
            assert issubclass(urnobj.__class__, Urn)

        self._urnobj = urnobj
        if urnobj is not None:
            self._urn = urnobj.urn

            from .poolmanager import PoolManager, DEFAULT_MEM_POOL
            from . import productstorage
            loadmeta = (poolname or meta) and poolname != DEFAULT_MEM_POOL
            if poolname is None:
                poolname = urnobj.pool
            pool = PoolManager.getPool(poolname)
            self._meta = (meta if meta else pool.meta(
                urnobj.urn)) if loadmeta else None
            self._poolname = poolname
            self._product = None
        else:
            self._urn = None
            self._poolname = None
            self._meta = None
            self._product = None

    def getUrnObj(self):
        """ Returns the URN as an object.
        """
        return self._urnobj

    @property
    def meta(self):
        """ Property """
        return self.getMeta()

    def getMeta(self):
        """ Returns the metadata of the product.
        """
        return self._meta

    def getHash(self):
        """ Returns a code number for the product; actually its MD5 signature. 
        This allows checking whether a product already exists in a pool or not.
        """
        return self.hash()

    def getSize(self):
        """ Returns the estimated size(in bytes) of the product in memory. 
        Useful for providing this information for a user that wants to download the product from a remote site.
        Returns:
        the size in bytes
        """
        raise NotImplementedError()

    def unload(self):
        """ Clear the cached meta and frees internal reference to the product, so it can be garbage collected.
        """
        self._product = None
        self._meta = None

    def isLoaded(self):
        """ Informs whether the pointed product is already loaded.
        """
        return self._product is not None

    def addParent(self, parent):
        """ add a parent
        """
        if any(id(parent) == id(x) for x in self._parents):
            return
        self._parents.append(parent)

    def removeParent(self, parent):
        """ remove a parent

        :param parent: 

        """
        if parent is not None:
            self._parents.remove(parent)

    @property
    def parents(self):
        """ property """

        return self.getParents()

    @parents.setter
    def parents(self, parents):
        """ property """

        self.setParents(parents)

    def getParents(self):
        """ Return the in-memory parent context products of this reference.
        That is, the contexts in program memory that contain this product reference object. 
        A context that contains a different product reference object pointing to the same URN is not a parent of this product reference.

        Furthermore, it should be understood that this method does not return the parent contexts of the product pointed to by this reference as stored in any underlying pool or storage.

        Returns:
        the parents 
        """
        return self._parents

    def setParents(self, parents):
        """ Sets the in-memory parent context products of this reference.

        :param parents: 

        """
        self._parents = parents

    def equals(self, o, verbose=False):
        """     true if o is a non-null ProductRef, with the same Product type than this one, and:

        urns and products are null in both refs, or
        nurs are equal and products are null, or # <-- mh
        urns are null in both refs, and their products are equal, or
        urns and products are equal in both refs
        """
        t1 = issubclass(o.__class__, ProductRef)
        if not t1:
            if verbose:
                msg = 'Input o is not a ProductRef'
                return msg
            return False
        if self._product is None:
            if o._product is None:
                if o._urnobj is None and self._urnobj is None or o._urnobj == self._urnobj:
                    if verbose:
                        msg = 'Both onject._products are None or have equal URN.'
                        return msg
                    return True
            else:
                if verbose:
                    msg = 'Self._product is None but not for the other obj.'
                    return msg
                return False
        else:
            if self._product == o._product and (self._product.type == o._product.type):
                if (o._urnobj is None and self._urnobj is None) or \
                   (o._urnobj == self._urnobj):
                    if verbose:
                        print('True due to equal _project and _urnobj')
                    return True

        return False

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 **kwds):
        """
        """
        s = self.__class__.__name__
        s += ' {' + self.urn
        if level == 0:
            s += '\n# Parents=' + \
                str([str(id(p)) + ' ' + p.__class__.__name__ +
                     '"' + p.description + '"'
                     for p in self.parents]) + '\n'
            m = self.getMeta()
            ms = m.toString(level=level,
                            tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                            **kwds) if m else ''
            s += '# meta=' + ms

        else:
            s += ' Parents=' + str([id(p) for p in self.parents])
            s += ' meta= ' + 'None' if self.getMeta() is None else self.getMeta().toString(level=level,
                                                                                           tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                                                                                           **kwds)
        s += '}'
        return s

    __str__ = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(urnobj=self.urnobj if issubclass(self.urnobj.__class__, Urn) else None,
                           _STID=self._STID)
