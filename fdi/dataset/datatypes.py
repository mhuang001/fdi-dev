# -*- coding: utf-8 -*-
from numbers import Number
from collections import OrderedDict

from .serializable import Serializable
from .odict import ODict
from .dataset import ArrayDataset
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable
#from .metadata import ParameterTypes

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Vector(ArrayDataset):
    """ N dimensional vector with a unit.
    """

    def __init__(self, components=None, description='UNKNOWN', unit=None, typ_=None, default=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0] components and 'UNKNOWN' description, unit ''.
        With a signle argument: arg -> components, 'UNKNOWN'-> description, ''-> unit.
        With two positional arguments: arg1 -> components, arg2-> description, ''-> unit.
        With three positional arguments: arg1 -> components, arg2-> description, 'arg3-> unit.
        """
        if components is None:
            components = [0, 0, 0]
        self._default = default
        super(Vector, self).__init__(data=components,
                                     description=description, unit=unit, typ_=typ_, **kwds)

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
        return self._data

    def setComponents(self, components):
        """ Replaces the current components of this vector. """
        for c in components:
            if not isinstance(c, Number):
                raise TypeError('Components must all be numbers.')
        # must be list to make round-trip Json
        self._data = list(components)

    # def __repr__(self):
    #     return self.__class__.__name__ + \
    #         '{ %s (%s) "%s"}' %\
    #         (str(self.components), str(self.getUnit()), str(self.description))

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           components=list(self.components),
                           unit=self.unit,
                           type=self._type,
                           default=self._default,
                           typecode=self._typecode,
                           classID=self.classID)


class Quaternion(Vector):
    """ Quaternion with a 4-component data.
    """

    def __init__(self, components=None, description='UNKNOWN', unit=None, typ_=None, default=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0, 0] components and 'UNKNOWN' description, unit ''.
        With a signle argument: arg -> components, 'UNKNOWN'-> description, ''-> unit.
        With two positional arguments: arg1 -> components, arg2-> description, ''-> unit.
        With three positional arguments: arg1 -> components, arg2-> description, 'arg3-> unit.
        """
        if components is None:
            components = [0, 0, 0, 0]

        super(Vector, self).__init__(data=components, description=description,
                                     unit=unit, typ_=typ_, default=default, **kwds)
