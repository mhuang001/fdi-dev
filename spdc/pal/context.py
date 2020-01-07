# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from spdc.dataset.product import Product
from spdc.dataset.dataset import CompositeDataset


class Context(Product):
    """ A  special kind of Product that can hold references to other Products.

This abstract product introduces the lazy loading and saving of references to Products or ProductRefs that it is holding. It remembers its state.
http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/api/herschel/ia/pal/Context.html
    """

    def __init__(self,  **kwds):
        """
        """
        super(Context, self).__init__(**kwds)

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

    def isValid(self):
        """ Provides a mechanism to ensure whether it is valid to store this context in its current state.
        """
        raise NotImplementedError()

    def readDataset(self, storage, table, defaultPoolId):
        """ Reads a dataset with information within this context that is normally not accessible from the normal Product interface."""
        raise NotImplementedError()

    def refsChanged(self):
        """ Indicates that the references have been changed in memory, which marks this context as dirty.
        """
        self._dirty = True

    def writeDataset(self,  storage):
        """ Creates a dataset with information within this context that is normally not accessible from the normal Product interface.
        """
        raise NotImplementedError()


class MapRefsDataset(CompositeDataset):
    """ add put(n, ref)
    """

    def __init__(self,  **kwds):
        """
        """
        super(MapRefsDataset, self).__init__(**kwds)

    def put(self, key, ref):
        """
        """
        self.set(key, ref)


class MapContext(Context):
    """ Allows grouping Products into a map of (String, ProductRef) pairs.
    New entries can be added if they comply to the adding rules of this context. The default behaviour is to allow adding any (String,ProductRef).

    An example::

        image     = ImageProduct(description="hi")
        spectrum  = SpectrumProduct(description="there")
        simple    = Product(description="everyone")

        context=MapContext()
        context.refs.put("x",ProductRef(image))
        context.refs.put("y",ProductRef(spectrum))
        context.refs.put("z",ProductRef(simple))
        print context.refs.size() # 3
        print context.refs.get('x').product.description # hi
        print context.refs.get('y').product.description # there
        print context.refs.get('z').product.description # everyone

    It is possible to insert a ProductRef at a specific key in the MapContext. The same insertion behaviour is followed as for a java Map, in that if there is already an existing ProductRef for the given key, that ProductRef is replaced with the new one::

         product4=SpectrumProduct(description="everybody")
         context.refs.put("y", ProductRef(product4))
         product5=SpectrumProduct(description="here")
         context.refs.put("a", ProductRef(product5))

         print context.refs.get('x').product.description # hi
         print context.refs.get('y').product.description # everybody
         print context.refs.get('z').product.description # everyone
         print context.refs.get('a').product.description # here
    """

    def __init__(self,  **kwds):
        """
        """
        super(MapContext, self).__init__(**kwds)
        self.setRefs(MapRefsDataset())
        self._dirty = False

    @property
    def refs(self):
        """ Property """
        return self.getRefs()

    @refs.setter
    def refs(self, refs):
        """
        """
        self.setRefs(refs)

    def setRefs(self, refs):
        """
        """
        self.set('refs', refs)

    def getRefs(self):
        """ Returns the URN as an object.
        """
        return self.get('refs')

    def getAllRefs(self, recursive=False, includeContexts=True, seen=None):
        """ Provides a set of the unique references stored in this context. This includes references that are contexts, but not the contents of these subcontexts. This is equivalent to getAllRefs(recursive=false, includeContexts= true).
        recursive - if true, include references in subcontexts
        includeContexts - if true, include references to contexts, not including this one
        """
        if not Context.isContext(self):
            raise ValueError('self is not a context')
        if seen is None:
            see = list()
        rs = list()
        for x in self.refs.values():
            if Context.isContext(x):
                if includeContexts:
                    if x == self:
                        pass
                    else:
                        if x not in rs:
                            rs.append(x)
                if recursive:
                    if x not in seen:
                        seen.append(x)
                        # enter the context
                        rs.add(x.getAllRefs(recursive=recursive,
                                            includeContexts=includeContexts,
                                            seen=seen))
                else:
                    pass
            else:
                # not contex
                # records
                if x not in rs:
                    rs.append(x)

        return rs

    def hasDirtyReferences(self, storage):
        """ Returns a logical to specify whether this context has dirty references or not.
        """
        return self._dirty

    @staticmethod
    def isContext(cls):
        """ Yields true if specified class belongs to the family of contexts.
        """
        return issubclass(cls, Context)

    def isValid(self, ):
        """ Provides a mechanism to ensure whether it is valid to store this context in its current state.
        """
        return True

    def readDataset(self, storage, table, defaultPoolId):
        """ Reads a dataset with information within this context that is normally not accessible from the normal Product interface."""
        raise NotImplementedError()

    def writeDataset(self,  storage):
        """ Creates a dataset with information within this context that is normally not accessible from the normal Product interface.
        """
        raise NotImplementedError()
