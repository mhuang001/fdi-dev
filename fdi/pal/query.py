# -*- coding: utf-8 -*-

from ..dataset.serializable import Serializable
from ..dataset.product import Product
import pdb
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class StorageQuery(Serializable):
    """ Query on a ProductStorage. """

    def __init__(self, **kwds):
        self.query_all = True
        super(StorageQuery, self).__init__(**kwds)

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def getType(self):
        """ Get the class used in the query. """
        return self._type

    def getVariable(self):
        """ Get the variable name used in the query expression, eg "p". """
        return self._variable

    def getWhere(self):
        """ Get the query expression to be evaluated. """
        return self._where

    def retrieveAllVersions(self):
        """ Are all versions to be retrieved, or just the latest? """
        return self._allVersions


class AbstractQuery(StorageQuery):
    """ provides default implementations for the pal storage query. """

    def __init__(self, product=Product, variable='p', where='', allVersions=False, **kwds):
        """ creates an AbstractQuery with product variable name, query string or function."""
        self._type = product
        self._where = where
        self._variable = variable
        self._allVersions = allVersions

        super(AbstractQuery, self).__init__(**kwds)

    def hashCode(self):
        return None

    def toString(self):
        """
        """

        s = self.__class__.__name__ +\
            '"%s", product = %s, variable = %s, allVersions = %s' % \
            (str(self._where), str(self._type), str(
                self._variable), str(self._allVersions))
        return s


class MetaQuery(AbstractQuery):
    """ Meta data query formulates a query on the meta data of a Product.

    Typically this type of query is faster than a full query on the Product Access Layer.

    """

    def __init__(self, product=Product, where='', allVersions=False, **kwds):
        """ creates an MetaQuery with a query string or function.

        'where' is a query string or function that returns True or False.
        In the query string variable name is 'm' for a MetaData type, as in ``m = product.meta``.
        """
        # pdb.set_trace()
        super(MetaQuery, self).__init__(product=product, variable='m',
                                        where=where, allVersions=allVersions, **kwds)
