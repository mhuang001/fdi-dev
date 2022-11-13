# -*- coding: utf-8 -*-

from .serializable import Serializable
from .eq import DeepEqual
from .classes import Classes
from .quantifiable import Quantifiable

from functools import lru_cache
from collections import OrderedDict
import builtins
from math import sqrt
import array
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

bltns = vars(builtins)

ENDIAN = 'little'
""" Endianess of products generated. """

# data_type in parameter/column descriptors vs `data.__class__.__name__`
DataTypes = {
    'array': 'array.array',
    'baseProduct': 'BaseProduct',
    'binary': 'int',
    'boolean': 'bool',
    'byte': 'int',
    'complex': 'complex',
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
    'vector3d': 'Vector3D',
    '': 'None'
}
""" Allowed data (Parameter and Dataset) types and the corresponding classe names.
The keys are mnemonics for humans; the values are type(x).__name__.
"""

DataTypeNames = {}
for tn, tt in DataTypes.items():
    if tt == 'int':
        DataTypeNames[tt] = 'integer'
    else:
        DataTypeNames[tt] = tn
DataTypeNames.update({
    'NoneType': '',
    'dict': 'vector',
    'OrderedDict': 'vector',
    'UserDict': 'vector',
    'ODict': 'vector',
})
""" maps class type names to human-friendly types, reverse `DataTypes`. """

del tt, tn


try:
    import numpy as np

    # numpy type to python type https://stackoverflow.com/a/34919415/13472124
    # nptype_to_pythontype = {v: getattr(bltns, k)
    #                        for k, v in np.typeDict.items() if k}
    pass
except ImportError:
    pass

# https://docs.python.org/3.6/library/ctypes.html#fundamental-data-types

ctype_to_typecode = {
    'c_bool': 't_',    # Bool
    'c_char': 'b',  # 1-char bytes
    'c_wchar': 'b',  # 1-char string
    'c_byte': 'b',  # int? signed char
    'c_ubyte': 'B',  # unsigned char
    'c_short': 'h',  # signed short
    'c_ushort': 'H',  # unsigned short
    'c_int': 'i',  # signed int
    'c_uint': 'I',  # unsigned int
    'c_long': 'l',  # signed long
    'c_ulong': 'L',  # unsigned long
    'c_longlong': 'q',  # signed long long
    'c_ulonglong': 'Q',  # unsigned long long
    'c_float': 'f',  # float
    'c_double': 'd',  # double
    'c_char_p': 'u',  # string
}

# from https://stackoverflow.com/a/53702352/13472124 by tel


def get_typecodes():
    import numpy as np
    import ctypes as ct
    import pprint
    # np.ctypeslib.as_ctypes_type(dtype)
    simple_types = [
        ct.c_byte, ct.c_short, ct.c_int, ct.c_long, ct.c_longlong,
        ct.c_ubyte, ct.c_ushort, ct.c_uint, ct.c_ulong, ct.c_ulonglong,
        ct.c_float, ct.c_double,
    ]
    return pprint.pprint([
        {np.dtype(ctype).str: ctype.__name__ for ctype in simple_types},
        {ctype_to_typecode[ctype.__name__]: np.dtype(
            ctype).itemsize for ctype in simple_types}
    ])

# generated with get_typecodes() above


# w/o endian
numpytype_to_ctype = {
    'f4': 'c_float',
    'f8': 'c_double',
    'i2': 'c_short',
    'i4': 'c_int',
    'i8': 'c_long',
    'u2': 'c_ushort',
    'u4': 'c_uint',
    'u8': 'c_ulong',
    'i1': 'c_byte',
    'u1': 'c_ubyte'
}

# generated with get_typecodes() above

typecode_itemsize = {'B': 1,
                     'H': 2,
                     'I': 4,
                     'L': 8,
                     'b': 1,
                     'd': 8,
                     'f': 4,
                     'h': 2,
                     'i': 4,
                     'l': 8}

numpy_dtypekind_to_typecode = {
    'b': 't_',  # 'boolean',
    'i': 'i',    # integer',
    'u': 'I',    # unsigned integer',
    'f': 'd',    # float',
    'c': 'c',    # complex float',
    'm': 'datetime.timedelta',    # timedelta',
    'M': 'datetime,    # datetime',
    'O': 'object',    # object',
    'S': 'B',    # string',
    'U': 'B',    # unicode string',
    'V': 'V',    # fixed chunk of memory for other type ( void )',
}


def numpytype_to_typecode(x): return ctype_to_typecode[numpytype_to_ctype[x]]


def cast(val, typ_, namespace=None):
    """Casts the input value to type specified.

    For example 'binary' type '0x9' is casted to int 9.

    Parameters
    ----------
    val : multiple
        value to be casted.
    typ_ : string
        "human name" of `datatypes.DataTypeNames`. e.g. `integer`, `vector2d`, 'list'.
    namespace : dict
        namespace to look up classes. default is `Classes.mapping`.

    Returns
    -------
    multiple
        Casted value.

    Raises
    ------

    """

    t = DataTypes[typ_]
    vstring = str(val).lower()
    tbd = bltns.get(t, None)  # lookup_bd(t)
    if tbd:
        if t == 'int':
            base = 16 if vstring.startswith(
                '0x') else 2 if vstring.startswith('0b') else 10
            return tbd(vstring, base)
        elif t == 'bytes':
            return int(val).to_bytes(1, ENDIAN)
        return tbd(val)
    else:
        return Classes.mapping[t](val) if namespace is None else namespace[t](val)


class Vector(Quantifiable, Serializable, DeepEqual):
    """ N dimensional vector.

    If description, type etc meta data is needed, use a Parameter.

    A Vector can compare with a value whose type is in ``DataTypes``, the quantity being used is the magnitude.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0] components.

        Parameters
        ----------

        Returns
        -------

        """
        if components is None:
            self._data = [0, 0, 0]
        else:
            self.setComponents(components)
        super().__init__(**kwds)

    @ property
    def components(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getComponents()

    @ components.setter
    def components(self, components):
        """ for property setter

        Parameters
        ----------

        Returns
        -------

        """
        self.setComponents(components)

    def getComponents(self):
        """ Returns the actual components that is allowed for the components
        of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data

    def setComponents(self, components):
        """ Replaces the current components of this vector.

        Parameters
        ----------

        Returns
        -------

        """
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
        """
        Parameters
        ----------

        Returns
        -------

        """
        return len(self._data)

    def toString(self, level=0, **kwds):
        return self.__repr__()

    __str__ = toString

    string = toString
    txt = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder
        Parameters
        ----------

        Returns
        -------

        """
        return OrderedDict(
            components=list(self._data),
            unit=self._unit,
            typecode=self._typecode)


class Vector2D(Vector):
    """ Vector with 2-component data"""

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0] components
        Parameters
        ----------

        Returns
        -------
        """
        super().__init__(**kwds)

        if components is None:
            self._data = [0, 0]
        else:
            self.setComponents(components)


class Vector3D(Vector):
    """ Vector with 3-component data"""

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0]] components
        Parameters
        ----------

        Returns
        -------
        """
        super().__init__(**kwds)

        if components is None:
            self._data = [0, 0, 0]
        else:
            self.setComponents(components)


class Quaternion(Vector):
    """ Quaternion with 4-component data.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0, 0] components
        Parameters
        ----------

        Returns
        -------
        """
        super(Quaternion, self).__init__(**kwds)

        if components is None:
            self._data = [0, 0, 0, 0]
        else:
            self.setComponents(components)
