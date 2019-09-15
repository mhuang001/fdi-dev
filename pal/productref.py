# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.metadataholder import MetaDataHolder
from dataset.serializable import Serializable
from dataset.eq import DeepEqual
from dataset.odict import ODict
from .comparable import Comparable
from .urn import Urn
from .common import getProductObject


class ProductRef(MetaDataHolder, Serializable, Comparable):
    """ A lightweight reference to a product that is stored in a ProductPool or in memory.
    """

    def __init__(self, urn=None, pool=None, product=None, **kwds):
        """ Urn can be the string or URNobject. if product is provided create an in-memory URN.
        mh: If a URN for a URN is needed, use Urn.getInMemUrnObj()
        pool is the object type.
        """
        super().__init__(**kwds)
        if issubclass(urn.__class__, str):
            urnobj = Urn(urn)
        elif issubclass(urn.__class__, Urn):
            urnobj = urn
        else:
            # allow ProductRef(p) where p is a Product
            product = urn
            urnobj = None  # in case urn is also None

        if product:
            # urnobj is the python obj id
            urnobj = Urn.getInMemUrnObj(product)
            self._meta = product.meta
        elif pool is not None and urnobj is not None:
            #    import pal.productstorage as pps
            #    storage = pps.ProductStorage(pool)
            self._meta = pool.meta(urnobj.urn)
        else:
            self._meta = None
        self.setUrnObj(urnobj)
        self._storage = None
        self._parents = []

    @property
    def product(self):
        return self.getProduct()

    def getProduct(self):
        """ Get the product that this reference points to.
        """

        return getProductObject(self.getUrn())

    def getStorage(self):
        """ Returns the product storage associated.
        """
        return self._storage

    def setStorage(self, storage):
        """ Returns the product storage associated.
        """
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

    def setUrnObj(self, urnobj):
        """ sets urn
        """
        if urnobj is not None:
            # logger.debug(urnobj)
            assert issubclass(urnobj.__class__, Urn)

        self._urnobj = urnobj
        if urnobj is not None:
            self._urn = urnobj.urn
            # if hasattr(self, '_storage') and self._storage:
            #    self._meta = self._storage.getMeta(self._urn)
        else:
            self._urn = None

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

    def addParent(self, parent):
        """ add a parent
        """
        self._parents.append(parent)

    def removeParent(self, parent):
        """ remove a parent
        """
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
        """
        return self._parents

    def setParents(self, parents):
        """ Sets the in-memory parent context products of this reference.
        """
        self._parents = parents

    def __eq__(self, o):
        """ has the same Urn.
        """
        if not issubclass(o.__class__, ProductRef):
            return False
        return self._urnobj == o._urnobj

    def __repr__(self):
        return self.__class__.__name__ + '{ ProductURN=' + self.urn + ', meta=' + str(self.getMeta()) + '}'

    def toString(self, matprint=None, trans=True):
        """
        """
        s = '# ' + self.__class__.__name__ + '\n'
        s += '# ' + self.urn + '\n'
        s += '# Parents:' + \
            str([p.__class__.__name__ +
                 '(' + p.description + ')'
                 for p in self.parents]) + '\n'
        s += '# meta;' + self.meta.toString()
        return s

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(urnobj=self.urnobj if issubclass(self.urnobj.__class__, Urn) else None,
                     _meta=self.getMeta(),
                     classID=self.classID,
                     version=self.version)
