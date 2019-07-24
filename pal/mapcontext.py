
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from pal.urn import Urn
from pal.productref import ProductRef
from pal.comparable import Comparable
from .common import getJsonObj
from .context import Context
from dataset.product import Product
from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict


class Context(Product):
    """ A Context is a special kind of Product that can hold references to other Products.

This abstract product introduces the lazy loading and saving of references to Products or ProductRefs that it is holding. It remembers its state. 
http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/api/herschel/ia/pal/Context.html
    """

    def __init__(self, value=None, **kwds):
        """ 
        """
        super().__init__(**kwds)
        self.value = value
        self.type = value.__class__.__name__

    def getAllRefs(self):
        """ Provides a set of the unique references stored in this context.
        """

    def getAllRefs(self, recursive, includeContexts):
        """ Provides a set of the unique references stored in this context.
        """
        raise NotImplementedError()

    def hasDirtyReferences(self, storage):
        """ Returns a logical to specify whether this context has dirty references or not.
        """
        raise NotImplementedError()

    @staticmethod
    def isContext(cls):
        """ Yields true if specified class belongs to the family of contexts.
        """
        return issubclass(cls, Context)

    def isValid(self, ):
        """ Provides a mechanism to ensure whether it is valid to store this context in its current state.
        """
        raise NotImplementedError()

    def readDataset(self, storage, table, defaultPoolId):
        """ Reads a dataset with information within this context that is normally not accessible from the normal Product interface."""
        raise NotImplementedError()

    def refsChanged(self, ):
        """ Indicates that the references have been changed in memory, which marks this context as dirty.
        """
        raise NotImplementedError()

    def writeDataset(self,  storage):
        """ Creates a dataset with information within this context that is normally not accessible from the normal Product interface.
        """
        raise NotImplementedError()
