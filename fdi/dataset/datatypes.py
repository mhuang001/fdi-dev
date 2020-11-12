# -*- coding: utf-8 -*-

from collections import OrderedDict

from .serializable import Serializable
from .eq import DeepEqual

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Vector(Serializable, DeepEqual):
    """ N dimensional vector.

    If unit, description, type etc meta data is needed, use a Parameter.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0] components.
        """
        if components is None:
            self._data = [0, 0, 0]
        else:
            self.setComponents(components)
        super(Vector, self).__init__(**kwds)

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
        # for c in components:
        #     if not isinstance(c, Number):
        #         raise TypeError('Components must all be numbers.')
        # must be list to make round-trip Json
        self._data = list(components)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return str(self._data)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            components=list(self.components),
            classID=self.classID)


class Quaternion(Vector):
    """ Quaternion with 4-component data.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0, 0] components

        """

        super(Quaternion, self).__init__(**kwds)

        if components is None:
            self._data = [0, 0, 0, 0]
        else:
            self.setComponents(components)
