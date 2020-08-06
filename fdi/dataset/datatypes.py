# -*- coding: utf-8 -*-
from numbers import Number


from .serializable import Serializable
from .odict import ODict
from .quantifiable import Quantifiable
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable
#from .metadata import ParameterTypes

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Vector(Annotatable, Copyable, DeepEqual, Quantifiable, Serializable):
    """ Three dimensional vector with a unit.
    """

    def __init__(self, components=[0, 0, 0], description='UNKNOWN', unit='', **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0] components and 'UNKNOWN' description, unit ''.
        With a signle argument: arg -> components, 'UNKNOWN'-> description, ''-> unit.
        With two positional arguments: arg1 -> components, arg2-> description, ''-> unit.
        With three positional arguments: arg1 -> components, arg2-> description, 'arg3-> unit.
        """
        super(Vector, self).__init__(
            description=description, unit=unit, **kwds)
        self.setComponents(components)

    def accept(self, visitor):
        """ Adds functionality to classes of this components."""
        visitor.visit(self)

    @property
    def components(self):
        """ for property getter
        """
        return self.getComponents()

    @components.setter
    def components(self, components):
        """ for property setter
        """
        self.setComponents(components)

    def getComponents(self):
        """ Returns the actual components that is allowed for the components
        of this vector."""
        return self._components

    def setComponents(self, components):
        """ Replaces the current components of this vector. """
        for c in components:
            if not isinstance(c, Number):
                raise TypeError('Components must all be numbers.')
        # must be list to make round-trip Json
        self._components = list(components)

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ %s (%s) "%s"}' %\
            (str(self.components), str(self.getUnit()), str(self.description))

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     components=self.components,
                     unit=self.unit,
                     classID=self.classID)


class Quaternion(Vector):
    """ Quaternion with a unit.
    """

    def __init__(self, components=[0, 0, 0, 0], **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0, 0] components and 'UNKNOWN' description, unit ''.
        With a signle argument: arg -> components, 'UNKNOWN'-> description, ''-> unit.
        With two positional arguments: arg1 -> components, arg2-> description, ''-> unit.
        With three positional arguments: arg1 -> components, arg2-> description, 'arg3-> unit.
        """
        super(Quaternion, self).__init__(components=components, **kwds)
