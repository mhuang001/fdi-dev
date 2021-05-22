# -*- coding: utf-8 -*-

from ..dataset.serializable import Serializable
from ..dataset.baseproduct import BaseProduct
from ..dataset.odict import ODict
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' % (logger.getEffectiveLevel()))


class ContextRuleException(ValueError):
    pass


class RefContainer(ODict):  # XXXXXXXX order
    """ A map where Rules of its owner Context are applied when put(k,v) is called, and the owner MapContext's ID can be put to v's parents list.

    Implemented.Composite so that RefContainer has a _STID when json.loads'ed.
    A MapContext has a _sets, which has a refs:RefContainer, which has a _sets, which has a name:ProductRef.
    when used as context.refs.get('x').product.description, the RefContainer is called with get() or __getitem__(), which calls superclass composite's _set's __getitem__()
    """

    def __init__(self, **kwds):
        """ 
        """
        super(RefContainer, self).__init__(**kwds)
        self.setOwner(None)

    @property
    def owner(self):
        """ Property """
        return self.getOwner()

    @owner.setter
    def owner(self, owner):
        """
        """
        self.setOwner(owner)

    def getOwner(self):
        """ Returns the reference container mapping
        """
        return self._owner

    def setOwner(self, owner):
        """ records who owns this container.

        Due to reason described in __setitem__ doc, existing refs will be set again upon owner set
        """

        if hasattr(self, '_owner') and self._owner is not None and id(self._owner) == id(owner):
            return
        self._owner = owner
        old = self.data
        self.data = dict()
        for k, r in old.items():
            self.__setitem__(k, r)
        del old

    def __setitem__(self, key, ref):
        """
            when deserialized contained refs will be set with _owner==None
            then the following are done when the assembled refContainer is
            set('refs',refC) to the owner context.
        """
        if key is None:
            raise KeyError()
        if ref is None:
            raise ValueError()

        # during deserialization __setitem__ is called before _owner is set by Context,setRefs()
        if hasattr(self, '_owner') and self._owner is not None:
            from .productref import ProductRef
            if isinstance(ref, ProductRef):
                ref.addParent(self._owner)
            else:
                raise TypeError(type(ref).__name__ +
                                ' is not a Product Reference')
            if not self._owner.applyRule(key, ref):
                ContextRuleException('Ref %s fails rule test of %s.' %
                                     (ref.toString(level=2),
                                      self._owner.__class__.__name__)
                                     )
        super().__setitem__(key, ref)

    def __delitem__(self, key):
        if key is None:
            raise KeyError()
        # during deserialization __setitem__ are called before _owner is set by Context,setRefs()
        if hasattr(self, '_owner'):
            from .productref import ProductRef
            ref = self.__getitem__(key)
            if isinstance(ref, ProductRef):
                ref.removeParent(self._owner)
        super().__delitem__(key)

    def clear(self):
        """ remove all productRefs """
        ks = list(self.keys())
        for k in ks:
            self.__delitem__(k)

    def put(self, key, ref):
        """ set label-ref pair after validating then add parent to the ref
        """
        self.__setitem__(key, ref)

    def set(self, key, ref):
        self.put(key, ref)

    def get(self, key):
        """
        """
        return self.__getitem__(key)

    def size(self):
        """ """
        return len(self.keys())

    # def __getstate__(self):
    #     """ Can be encoded with serializableEncoder """
    #     return ODict(
    #         data=self.data,
    #         _STID=self._STID)


class AbstractContext():
    """ A  special kind of Product that can hold references to other Products.

This abstract product introduces the lazy loading and saving of references to Products or ProductRefs that it is holding. It remembers its state.
http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/api/herschel/ia/pal/Context.html
    """

    def __init__(self,  **kwds):
        """ Sets ``rule`` to ``None`` if ``zInfo`` does not have ``refs``, else to ``zInfo['refs']``.
        """
        super(AbstractContext, self).__init__(**kwds)

        self._dirty = False
        if 'refs' not in self.zInfo:
            self._rule = None  # None means there is no rule.
        else:
            self._rule = self.zInfo['refs']
        refC = None
        # this line must stay after _rule is set.
        self.setRefs(refC)

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
        """ Changes/Adds the mapping container that holds references.
        """
        self.set('refs', refs)

    def set(self, name, refs):
        """ add owner to RefContainer
        """
        if isinstance(refs, RefContainer) and name == 'refs':
            refs.setOwner(self)
        super().set(name, refs)

    def getRefs(self):
        """ Returns the reference container mapping
        """
        return self.get('refs')

    def getAllRefs(self, recursive, includeContexts):
        """ Provides a set of the unique references stored in this context.
        """
        raise NotImplementedError()

    def hasDirtyReferences(self, storage):
        """ Returns a logical to specify whether this context has dirty references or not.
        """
        raise NotImplementedError()

    @classmethod
    def isContext(cls):
        """ Yields true if specified class belongs to the family of contexts.
        """
        return issubclass(cls, AbstractContext)

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

    def getRule(self):
        """ Get the rule that controls the products to be added into the context.
        """
        return self._rule

    def setRule(self, rule):
        """ Set the rule that controls the products to be added into the context.
        """
        self._rule = rule

    def addRule(self, rule):
        """ Add to  the rule that controls the products to be added into the context.
         The new rule will be old rule AND added rule.
        """
        raise NotImplementedError()

    def applyRule(self, *args):
        """ returns True if the input ProductRef passes rule.

        If ``refs`` is not specified in ``zInfo`` return True.
        If ``zInfo['refs'] is empty, return True.

        Subclasses can override this method according to what is written in zInfo.
        """
        if self._rule is None:
            return True
        if len(self._rule) == 0:
            return True

        return True


class Context(AbstractContext, BaseProduct):
    """ See docstring of AbstractContext.
    """

    def __init__(self,  **kwds):
        """
        """
        super(Context, self).__init__(**kwds)

    def applyRule(self, *args):
        """ returns True if the input ProductRef passes rule.

        Default behavior is return the  superclass.applyRule() result.

        Subclasses can override this method according to what is written in zInfo.
        """
        return super().applyRule(*args)

    def getAllRefs(self, recursive=False, includeContexts=True, seen=None):
        """ Provides a set of the unique references stored in this context.
        This includes references that are contexts, but not the contents of these subcontexts. This is equivalent to getAllRefs(recursive=false, includeContexts= true).
        recursive - if true, include references in subcontexts
        includeContexts - if true, include references to contexts, not including this one
        """
        if not Context.isContext(self):
            raise TypeError('This ref does not point to a context')
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


class AbstractMapContext(AbstractContext):
    """
    """

    def __init__(self,  **kwds):
        """
        """
        super(AbstractMapContext, self).__init__(**kwds)
        refC = RefContainer()
        # this line must stay after _rule is set.
        self.setRefs(refC)


class MapContext(Context):
    """ Allows grouping Products into a map of (String, ProductRef) pairs.
    New entries can be added if they comply to the adding rules of this context. The default behaviour is to allow adding any (String,ProductRef) given that ``rule`` is not set.

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

    It is possible to insert a ProductRef at a specific key in the MapContext. The same insertion behaviour is followed as for a Python dict, in that if there is already an existing ProductRef for the given key, that ProductRef is replaced with the new one::

         product4=SpectrumProduct(description="everybody")
         context.refs.put("y", ProductRef(product4))
         product5=SpectrumProduct(description="here")
         context.refs.put("a", ProductRef(product5))

         print context.refs.get('x').product.description # hi
         print context.refs.get('y').product.description # everybody
         print context.refs.get('z').product.description # everyone
         print context.refs.get('a').product.description # here

    Note that the rules are only applied when putting an entry to the map!

    Be aware that

    1. the put() method of the map view may throw a ContextRuleException if the data added to the context violates the rules applied to the context.
    2. the put() method of the map view may throw a ValueError if either of the arguments to the put() method are null.


             BaseProduct--Product
                        \\
    AbstractContext------Contex---------MapContext

    """

    def __init__(self,  **kwds):
        """
        """
        super().__init__(**kwds)
        refC = RefContainer()
        # this line must stay after _rule is set.
        self.setRefs(refC)

    def addRule(self, rule):
        """ Add to  the rule that controls the products to be added into the context.
         The new rule will be old rule AND added rule.
        """
        self._rule.update(rule)

    def applyRule(self, key, ref):
        """ returns True if the input key name and ProductRef pass rule.

        Default behavior is return True if the fully qualified class name of the product which ref refers to equals ``zInfo['refs'][key]``, OR the superclass.applyRule() result.

        Subclasses can override this method according to what is written in zInfo.
        """
        if super().applyRule():
            return True
        if 'refs' in self.zInfo:
            return ref.urnobj.getTypeName() in self.zInfo['refs']
