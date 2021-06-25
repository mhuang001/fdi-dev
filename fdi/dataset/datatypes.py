# -*- coding: utf-8 -*-

from functools import lru_cache
from .serializable import Serializable
from .eq import DeepEqual
from .classes import Classes
from .quantifiable import Quantifiable

from collections import OrderedDict
import builtins
from math import sqrt
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

""" Allowed data (Parameter and Dataset) types and the corresponding classe names.
The keys are mnemonics for humans; the values are type(x).__name__.
"""
DataTypes = {
    'baseProduct': 'BaseProduct',
    'binary': 'int',
    'boolean': 'bool',
    'byte': 'int',
    'finetime': 'FineTime',
    'finetime1': 'FineTime1',
    'float': 'float',
    'hex': 'int',
    'integer': 'int',
    'list': 'list',
    'mapContext': 'MapContext',
    'product': 'Product',
    'quaternion': 'Quaternion',
    'short': 'int',
    'string': 'str',
    'tuple': 'tuple',
    # 'numericParameter': 'NumericParameter',
    # 'dateParameter': 'DateParameter',
    # 'stringParameter': 'StringParameter',
    'vector': 'Vector',
    'vector2d': 'Vector2D',
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


@lru_cache(maxsize=64)
def lookup_bd(t):

    try:
        return builtins.__dict__[t]
    except KeyError:
        return None


def cast(val, typ_, namespace=None):
    """ casts the input value to type specified, which is in DataTypeNames.

    For example 'binary' type '0x9' is casted to int 9.

    namespace: default is Classes.mapping.
    """
    t = DataTypes[typ_]
    vstring = str(val).lower()
    tbd = lookup_bd(t)
    if tbd:
        if t == 'int':
            base = 16 if vstring.startswith(
                '0x') else 2 if vstring.startswith('0b') else 10
            return tbd(vstring, base)
        return tbd(val)
    else:
        return Classes.mapping[t](val) if namespace is None else namespace[t](val)


class Vector(Quantifiable, Serializable, DeepEqual):
    """ N dimensional vector.

    If unit, description, type etc meta data is needed, use a Parameter.

    A Vector can compare with a value whose type is in ``DataTypes``, the quantity being used is the magnitude.
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

    def __eq__(self, obj, verbose=False, **kwds):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return sqrt(sum(x*x for x in self._data)) == obj
        else:
            return super(Vector, self).__eq__(obj)

    def __lt__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return sqrt(sum(x*x for x in self._data)) < obj
        else:
            return super(Vector, self).__lt__(obj)

    def __gt__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return sqrt(sum(x*x for x in self._data)) > obj
        else:
            return super(Vector, self).__gt__(obj)

    def __le__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return sqrt(sum(x*x for x in self._data)) <= obj
        else:
            return super(Vector, self).__le__(obj)

    def __ge__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return sqrt(sum(x*x for x in self._data)) >= obj
        else:
            return super(Vector, self).__ge__(obj)

    def __len__(self):
        return len(self._data)

    __hash__ = DeepEqual.hash

    def toString(self, level=0, **kwds):
        return self.__repr__()

    __str__ = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            components=list(self._data),
            unit=self._unit,
            typecode=self._typecode,
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
