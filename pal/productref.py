# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.metadataholder import MetaDataHolder
from dataset.serializable import Serializable
from dataset.eq import DeepEqual
from dataset.odict import ODict
from .comparable import Comparable
from .urn import Urn
from . import productstorage
from .common import getProductObject


class ProductRef(MetaDataHolder, Serializable, Comparable, DeepEqual):
    """ A lightweight reference to a product that is stored in a ProductPool or in memory.
    """

    def __init__(self, urnobj=None, storage=None, **kwds):
        """ if urnobj is not None and not a Urn instance create an in-memory URN. 
        mh: If a URN for a URN is needed, use Urn.getInMemUrnObj()
        """
        super().__init__(**kwds)
        if urnobj is not None and not issubclass(urnobj.__class__, Urn):
            # urnobj is the python obj id
            urnobj = Urn.getInMemUrnObj(urnobj)

        self.setUrnObj(urnobj, storage)
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

    def setUrnObj(self, urnobj, storage=None):
        """ use supplied productstorage or create to get metaadata
        """
        if urnobj is not None:
            logger.debug(urnobj)
            assert issubclass(urnobj.__class__, Urn)

        self._urnobj = urnobj
        if urnobj is not None:
            self._urn = urnobj.urn
            if urnobj._scheme == 'file':
                if storage is not None:
                    s = storage
                else:
                    s = productstorage.ProductStorage(urnobj._pool)
                self._storage = s
                # there seems no better way to set ref meta
                self._meta = s.getMeta(urnobj)
            else:
                self._meta = ODict()
        else:
            self._urn = None
            self._meta = ODict()

    def getUrnObj(self):
        """ Returns the URN as an object.
        """
        return self._urnobj

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
        """
        """
        return self._urnobj == o._urnobj and sorted(self.parents) == sorted(o.parents)

    def __repr__(self):
        return self.__class__.__name__ + '{ ProductURN=' + self.urn + ', meta=' + str(self.getMeta()) + '}'

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(urnobj=self.urnobj if issubclass(self.urnobj.__class__, Urn) else None,
                     parents=self.parents,
                     _meta=self.getMeta(),
                     classID=self.classID,
                     version=self.version)
