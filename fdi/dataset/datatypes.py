# -*- coding: utf-8 -*-

from .serializable import Serializable
from .eq import DeepEqual
from .classes import Classes

from collections import OrderedDict
import builtins

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

""" Allowed data (Parameter and Dataset) types and the corresponding classe names.
The keys are mnemonics for humans; the values are type(x).__name__.
"""
DataTypes = {
    'binary': 'int',
    'integer': 'int',
    'short': 'int',
    'byte': 'int',
    'hex': 'int',
    'float': 'float',
    'string': 'str',
    'boolean': 'bool',
    'finetime': 'FineTime',
    'finetime1': 'FineTime1',
    'baseProduct': 'BaseProduct',
    'mapContext': 'MapContext',
    'product': 'Product',
    'vector': 'Vector',
    'vector2d': 'Vector2D',
    'quaternion': 'Quaternion',
    '': 'None'
}


""" maps class type names to human-friendly types """
DataTypeNames = {}
for tn, tt in DataTypes.items():
    if tt == 'int':
        DataTypeNames[tt] = 'integer'
    else:
        DataTypeNames[tt] = tn
DataTypeNames.update({
    'NoneType': '',
    'dict': 'vector',
    'ODict': 'vector'
})
del tt, tn


def cast(val, typ_, namespace=None):
    """ casts the input value to type specified, which is in DataTypeNames.

    For example 'binary' type '0x9' is casted to int 9.

    namespace: default is Classes.mapping.
    """
    t = DataTypes[typ_]
    bd = builtins.__dict__
    vstring = str(val).lower()
    if t in bd.keys():
        if t == 'int':
            base = 16 if vstring.startswith(
                '0x') else 2 if vstring.startswith('0b') else 10
            return bd[t](vstring, base)
        return bd[t](val)
    else:
        return Classes.mapping[t](val) if namespace is None else namespace[t](val)


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

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            components=list(self._data),
            _STID=self._STID)


class Vector2D(Vector):
    """ Vector with 2-component data.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0] components

        """

        super(Vector2D, self).__init__(**kwds)

        if components is None:
            self._data = [0, 0]
        else:
            self.setComponents(components)


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
