# -*- coding: utf-8 -*-

from .serializable import Serializable
from .copyable import Copyable
from .eq import DeepEqual
from .classes import Classes
from .quantifiable import Quantifiable

from functools import lru_cache
from collections import namedtuple
from collections import OrderedDict
from collections.abc import Iterable
from operator import mul
import builtins
import sys
from math import sqrt, asin, acos, pi
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

np_short = {'b': bool,  # Boolean
         'i8': np.int8,  # 8-bit signed integer
         'i16': np.int16,  # 16-bit signed integer
         'i32': np.int32,  # 32-bit signed integer
         'i64': np.int64,  # 64-bit signed integer
         'u8': np.uint8,  # 8-bit unsigned integer
         'u16': np.uint16,  # 16-bit unsigned integer
         'u32': np.uint32,  # 32-bit unsigned integer
         'u64': np.uint64,  # 64-bit unsigned integer
         'f16': np.float16,  # 16-bit floating point number
         'f32': np.float32,  # 32-bit floating point number
         'f64': np.float64,  # 64-bit floating point number
         'c64': np.complex64,  # 64-bit complex number
         'c128': np.complex128  # 128-bit complex number
         }

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

typecode_to_numpy_dtypekind = dict((v, k) for k, v in numpy_dtypekind_to_typecode.items()) 
    
typecode2np = {
    "b": np.int8,    # signed char
    "B": np.uint8,   # unsigned char
    "u": str,     # string
    "h": np.int16,   # signed short
    "H": np.uint16,  # unsigned integer
    "i": np.int16,   # signed integer
    "I": np.uint16,  # unsigned integer
    "l": np.int32,   # signed long
    "L": np.uint32,  # unsigned long
    "q": np.int64,   # signed long long
    "Q": np.uint64,  # unsigned long long
    "f": np.float32,  # float
    "d": np.float64,   # double
    "c": np.complex64,  # complex
    "c128": np.complex128,  # complex 128 b
    "t": bool,       # truth value
    "V": np.void,       # raw bytes block of fixed length
    "U": str
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
            try:
                re = tbd(vstring, base)
            except ValueError as e:
                re = vstring.split(',', 1)[0]
                logger.warning(f'{vstring} is not a proper {typ_}')
                # __import__("pdb").set_trace()
                pass
            return re
        elif t == 'bytes':
            return int(val).to_bytes(1, ENDIAN)
        return tbd(val)
    else:
        return Classes.mapping[t](val) if namespace is None else namespace[t](val)

"""
   An inertial attitude represented by body-referenced (+Z)(-Y)(-X) Euler angles.<p>
 
   The inertial attitude of a body can be represented by a triple (RA,DEC,POS) which
   defines Euler angles relative to the Equatorial reference frame. The body is
   rotated first through RA (right ascension) about the body +Z axis, followed DEC
   (declination) about the body -Y axis and finally POS (position angle) about the
   body -X axis.
 
   Hence, right ascension increases clockwise about the Z axis, declination increases
   anticlockwise about the Y axis and position angle increases anticlockwise about 
   the X axis. The position angle is the angle between the body X-Z plane and the
   plane defined by the body X axis and reference frame Z axis (North).
 
   This representation of attitude is especially useful for spacecraft with an
   astronomical telescope pointing along the X axis. The coordinates (RA,DEC)
   describe the pointing direction of the telescope, whilst POS describes the
   rotation of the telescope about the line of sight. The Attitude class extends
   Direction, since it is simply a Direction with an associated orientation.
 
   The position angle and right ascension are discontinuous at the poles (i.e.
   declination of +/-90 degrees). This requires care when performing calculations,
   as rounding errors could flip the attitude by 180 degrees. Consequently, it
   is generally preferred to represent attitudes as quaternions for performing
   calculations, since these do not suffer from singularities.

   In the limit, the sum RA+POS (mod 360) is constant at the North pole and the
   difference RA-POS (mod 360) is constant at the South pole. Hence, the three-axis
   attitude is well-defined on the whole celestial sphere by the triple (RA,DEC,POS),
   although there is a many-to-one mapping of this triple onto attitudes at the poles.
   The Attitude class provides a method to round (RA,DEC,POS) triples to a given
   precision for output (e.g. printing), as a single atomic operation that avoids
   problems with singularities. At the poles, many-to-one mapping of attitudes
   onto (RA,DEC,POS) triples is avoided by (arbitrarily) choosing RA=0.
 
   @author  Jon Brumfitt
"""

Attitude = namedtuple('Attitude', ['alpha', 'delta', 'phi'],
                      defaults=(0, 0, 0),
                      module=sys.modules['fdi.dataset.datatypes'])

Number = (float, int)

class Vector(Quantifiable, Serializable, DeepEqual, Iterable, Copyable):
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
        self._norm = None
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
        for c in components:
            if not isinstance(c, Number):
                raise TypeError('Components must all be numbers.')
        # must be list to make round-trip Json
        self._data = list(components)
        
    def dot(self, v):
        """
        Return the dot product of this vector by another vector, as
        a new vector.

        param v The other vector.
        """
        sd = self._data
        qd = v._data
        return sum(map(mul, sd, qd))
                   #+ sd.x * qd.x + sd.y * qd.y + sd.z * qd.z

    def cross(self, v):
        """
        Return the cross product of this vector by another vector, as
        a new vector.

        param v The other vector.
        """
        if len(v) != 3:
            raise NotImplementedError('cross operation only suppported in 3D.')

        sd = self._data
        qd = v._data
        return Vector3D((sd[1] * qd[2] - sd[2] * qd[1], sd[2] * qd[0] - sd[0] * qd[2], sd[0] * qd[1] - sd[1] * qd[0]))


    def norm(self):
        """
    
      * Return the L2 norm of this immutable vector.
      *
      * @return The L2 norm of this vector
      

        """
        if self._norm is not None:
            return self._norm
        else:
            sd = self._data
            self._norm = sqrt(sum(map(lambda u:u*u, sd)))
        return self._norm

    length = norm

    def normalize(self):
        """
 
        Normalize to unit length, returning a new vector.
      
        
        RETURNS
        -------
        This vector after normalizatiion

        THROWS
        ------
        ValueError if a zero vector.

        """
        return self.copy().mNormalize()

    def mNormalize(self):
        """
 
        Normalize to unit length, in place.
        
        The normalization is skipped if the vector is already normalized.
        This version modifies each component in place.
        
        RETURNS
        -------
        This vector after normalizatiion

        THROWS
        ------
        ValueError if a zero vector.
      

        """
        n1 = self.norm()
        if n1 == 0:
            raise ValueError("Cannot normalize zero vector")
        #  Do nothing if it is already normalized
        if abs(n1 - 1) > 2.5E-16:
            #  ULP = 2.22E-16
            norm = n1
            sd = self._data
            for i in range(len(sd)):
                sd[i] /= norm
        self._norm = 1
        return self


    def angle(self, v):
        """
     
          Return the angle in radians [0,pi], between this vector and another vector.
          
          @param v The other vector
          @return The angle in radians
          @throws ValueError if either vector is zero.
          
        """
        lsq = self.norm() * v.norm()
        a = self.dot(v) / lsq
        #  Use cross product for small angles
        if abs(a) < 0.99:
            return acos(a)
        elif a > 0:
            return asin(self.cross(v).norm() / lsq)
        else:
            return pi - asin(self.cross(v).norm() / lsq)
        
    def epsilonEquals(self, q, epsilon=None, fraction=1e-10):
        """
        Returns true if this quaternion is approximately equal to another.<p>
        The criterion is that the L-infinte distance between the two quaternions
        u and v is less than or equal to epsilon.

        If epsilon and fraction are both unspecified, fraction takes 1e-10 as the limit of fractional difference of `u` and `v` average; if epsilon is not specified and fraction is None, epsilon takes 1e-12; if both are specified, `epsilon` takes priority.
        PARAMETERS
        ----------
        q : Quaternion
            The other quaternion
        epsilon : float
            The maximum difference
        fraction : float
            The maximum relative differece. Ignored if `epsilon` is  given. 

        RETURNS
        -------
        bool

        true if the quaternions are approximately equal
        """
        if epsilon is None and fraction is None:
            epsilon = 1E-12
        sd = self._data
        qd = q._data

        if epsilon is None:
            return max(map(lambda s,q: 0 if (abs(s)+abs(q)) <= 1e-12 else abs((s-q)/(abs(s)+abs(q))), sd, qd)) <= fraction/2
        else:
            return max(map(lambda s,q: abs(s-q), sd, qd)) <= epsilon
        
    def __eq__(self, obj, verbose=False, **kwds):
        """ can compare value """
        t = type(obj)
        if not issubclass(t, self.__class__):
            return False
        if t.__name__ in DataTypes.values():
            return all(s==o for s,o in zip(self._data, obj._data))
        else:
            return super(Vector, self).__eq__(obj)

    def __lt__(self, obj):
        """ can compare value

            Compares the `norm()` result with `obj`.
        """
        if type(obj).__name__ in DataTypes.values():
            return self.norm() < obj
        else:
            return super(Vector, self).__lt__(obj)

    def __gt__(self, obj):
        """ can compare value.

        Compares the `norm()` result with `obj`.
        """
        if type(obj).__name__ in DataTypes.values():
            return self.norm() > obj
        else:
            return super(Vector, self).__gt__(obj)

    def __le__(self, obj):
        """ can compare value

            Compares the `norm()` result with `obj`.
        """
        if type(obj).__name__ in DataTypes.values():
            return self.norm() <= obj
        else:
            return super(Vector, self).__le__(obj)

    def __ge__(self, obj):
        """ can compare value

            Compares the `norm()` result with `obj`.
        """
        if type(obj).__name__ in DataTypes.values():
            return self.norm() >= obj
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

    def __iter__(self, *args, **kwargs):
        """ returns an iterator
        """
        return self._data.__iter__(*args, **kwargs)

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


    @ property
    def x(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getX()

    @ x.setter
    def x(self, x):
        """ for property setter

        Parameters
        ----------

        Returns
        -------

        """
        self.setX(x)

    def getX(self):
        """ Returns the actual x
        of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[0]

    def setX(self, x):
        """ Replaces the current x of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        if not isinstance(x, Number):
            raise TypeError('X must be a number.')

        self.setX(x)

    @ property
    def y(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getY()

    @ y.setter
    def y(self, y):
        """ for property setter

        Parameters
        ----------

        Returns
        -------

        """
        self.setY(y)

    def getY(self):
        """ Returns the actual y that is allowed for the y
        of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[1]

    def setY(self, y):
        """ Replaces the current y of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        if not isinstance(y, Number):
            raise TypeError('Y must be a number.')

        self._data[1] = y


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


    def mNormalize(self):
        """
         Normalize to unit length, in place.
        
        The normalization is skipped if the vector is already normalized.
        This version changes compnents in position.
        
        RETURNS
        -------
        Vector3D
            This vector after normalizatiion

        THROWS
        ------
        ValueError if a zero vector.
      

        """
        n1 = self.norm()
        if n1 == 0:
            raise ValueError("Cannot normalize zero vector")
        #  Do nothing if it is already normalized
        if abs(n1 - 1) > 2.5E-16:
            #  ULP = 2.22E-16
            norm = n1
            sd = self._data
            sd[0] /= norm
            sd[1] /= norm
            sd[2] /= norm
        self._norm = 1
        return self

    @ property
    def x(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getX()

    @ x.setter
    def x(self, x):
        """ for property setter

        Parameters
        ----------

        Returns
        -------

        """
        self.setX(x)

    def getX(self):
        """ Returns the actual x that is allowed for the x
        of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[0]

    def setX(self, x):
        """ Replaces the current x of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        if not isinstance(x, Number):
            raise TypeError('X must be a number.')

        self.setX(x)

    @ property
    def y(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getY()

    @ y.setter
    def y(self, y):
        """ for property setter

        Parameters
        ----------

        Returns
        -------

        """
        self.setY(y)

    def getY(self):
        """ Returns the actual y
        of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[1]

    def setY(self, y):
        """ Replaces the current y of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        if not isinstance(y, Number):
            raise TypeError('Y must be a number.')

        self._data[1] = y

    
    @ property
    def z(self):
        """ for propertz getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getZ()

    @ z.setter
    def z(self, z):
        """ for property setter

        Parameters
        ----------

        Returns
        -------

        """
        self.setZ(z)

    def getZ(self):
        """ Returns the actual z
        of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[2]

    def setZ(self, z):
        """ Replaces the current z of this vector.

        Parameters
        ----------

        Returns
        -------

        """
        if not isinstance(z, Number):
            raise TypeError('Z must be a number.')

        self._data[2] = z

