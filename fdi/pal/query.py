# -*- coding: utf-8 -*-

from ..dataset.serializable import Serializable
from ..dataset.product import Product
from ..utils.common import bstr

from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class StorageQuery(Serializable):
    """ Query on a ProductStorage. """

    # def __init__(self, where=None, type=None, vaiable=None, allVersions=None, **kwds):
    #     self._where = where
    #     self._type = type
    #     self._variable = vaiable
    #     self._allVersions = allVersions
    def __init__(self, **kwds):
        self.query_all = True
        super(StorageQuery, self).__init__(**kwds)

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    @property
    def type(self):
        return self.getType()

    @type.setter
    def type(self, type):
        self.setType(type)

    def getType(self):
        """ Get the class used in the query. """
        return self._type

    def setType(self, type):
        """ Sets the type of this object.
        """
        self._type = type

    @property
    def variable(self):
        return self.getVariable()

    @variable.setter
    def variable(self, variable):
        self.setVariable(variable)

    def getVariable(self):
        """ Get the variable name used in the query expression, eg "p". """
        return self._variable

    def setVariable(self, variable):
        """ Sets the variable of this object.
        """
        self._variable = variable

    @property
    def where(self):
        return self.getWhere()

    @where.setter
    def where(self, where):
        self.setWhere(where)

    def getWhere(self):
        """ Get the query expression to be evaluated. """
        return self._where

    def setWhere(self, where):
        """ Sets the where of this object.
        """
        self._where = where

    def retrieveAllVersions(self):
        """ Returns the allVersions related to this object."""
        return self._allVersions

    @property
    def allVersions(self):
        return self.getAllVersions()

    @allVersions.setter
    def allVersions(self, allVersions):
        self.setAllVersions(allVersions)

    def getAllVersions(self):
        """ Are all versions to be retrieved, or just the latest? """
        return self._allVersions

    def setAllVersions(self, allVersions):
        """ Sets the allVersions of this object.
        """
        self._allVersions = allVersions

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 **kwds):
        """
        """

        s = '<' + self.__class__.__name__ + ' ' + \
            ', '.join((str(k) + '=' + bstr(v)
                       for k, v in self.__getstate__().items())) + '>'
        return s

    def __getstate__(self):
        return OrderedDict(
            where=self._where,
            type=self._type,
            vaiable=self._variable,
            allVersions=self._allVersions,
        )


class AbstractQuery(StorageQuery):
    """ provides default implementations for the pal storage query. """

    def __init__(self, product=Product, variable='p', where='', allVersions=False, **kwds):
        """ creates an AbstractQuery with product variable name, query string or function.

        product: type (Class or 'Card' name) of the products to be queried.
        where: the query string.
        """
        self._type = product
        self._where = where
        self._variable = variable
        self._allVersions = allVersions

        super(AbstractQuery, self).__init__(**kwds)


class MetaQuery(AbstractQuery):
    """ Meta data query formulates a query on the meta data of a Product.

    Typically this type of query is faster than a full query on the Product Access Layer.

    """

    def __init__(self, product=Product, where='', allVersions=False, **kwds):
        """ creates an MetaQuery with a query string or function.

        product: type (Class or 'Card' name) of the products to be queried.
        where: the query string.
        'where' is a query string or function that returns True or False.
        In the query string variable name is 'm' for a MetaData type, as in ``m = product.meta``.
        """

        super(MetaQuery, self).__init__(product=product, variable='m',
                                        where=where, allVersions=allVersions, **kwds)
