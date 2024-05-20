#!/usr/bin/env python


from .datatypes import Vector, Attitude, Vector3D

from collections import namedtuple
from collections.abc import Sequence

import sys
from math import pi, sin as _sin, cos as _cos, atan2 as _atan2, asin as _asin, \
    sqrt as _sqrt

Number = (float, int)
RAD = 180 / pi

# def bsr(value, bits):
#     """ bsr(value, bits) -> value shifted right by bits

#     This function is here because an expression in the original java
#     source contained the token '>>>' and/or '>>>=' (bit shift right
#     and/or bit shift right assign).  In place of these, the python
#     source code below contains calls to this function.

#     Copyright 2003 Jeffrey Clement.  See pyrijnadel.py for license and
#     original source.
#     """
#     minint = -2147483648
#     if bits == 0:
#         return value
#     elif bits == 31:
#         if value & minint:
#             return 1
#         else:
#             return 0
#     elif bits < 0 or bits > 31:
#         raise ValueError('bad shift count')
#     tmp = (value & 0x7FFFFFFE) // 2**bits
#     if (value & minint):
#         return (tmp | (0x40000000 // 2**(bits-1)))
#     else:
#         return tmp

""" 
     This file is part of Herschel Common Science System (HCSS).
     Copyright 2001-2012 Herschel Science Ground Segment Consortium
    
     HCSS is free software: you can redistribute it and/or modify
     it under the terms of the GNU Lesser General Public License as
     published by the Free Software Foundation, either version 3 of
     the License, or (at your option) any later version.

     HCSS is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
     GNU Lesser General Public License for more details.

     You should have received a copy of the GNU Lesser General
     Public License along with HCSS.
     If not, see <http://www.gnu.org/licenses/>.

     package: herschel.share.fltdyn.math

     A quaternion w + ix + jy + kz.<p>

     Quaternions provide an efficient way to represent and manipulate rotations
     including spacecraft attitudes. They do not suffer from the singularity
     problems of Euler angles (e.g. the Attitude class).<p>
     
     Like several other classes in this package, mutating versions of some of
     the more common methods are provided. These return the mutated object,
     allowing operations to be concatenated as expressions, without the need
     to create new Quaternions as temporary variables. For example:<p>
     
     <tt>Quaternion q1 = q2.copy().mMultiply(q3).mMultiply(q4).mMultiply(q4);</tt>
     <p>
     
     The <tt>copy()</tt> operation can be omitted by simply using the non-mutating
     <tt>multiply()</tt> method for the first call as follows:<p>
     
     <tt>Quaternion q1 = q2.multiply(q3).mMultiply(q4).mMultiply(q5);</tt>
    
     @author  Jon Brumfitt
"""

"""
`Quat is a `namedtuple` with four components named 'x', 'y', 'z', and'w' for the three vector components and scalar compnent of a quaternion, with a default value of (0, 0, 0, 0).
"""
Quat = namedtuple('Quat', ['x', 'y', 'z', 'w'], defaults=[0, 0, 0, 0],
                  module=sys.modules['fdi.dataset.quaternion'])

class xQuaternion(Vector):
    """ Quaternion with 4-component data.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        (0, 0, 0, 0) components
        
        Parameters
        ----------
        components : list
            The four components.
        
        Returns
        -------
        """
        super(Quaternion, self).__init__(**kwds)

        if components is None:
            self._data = Quat(x=0, y=0, z=0, w=0)
        else:
            self.setComponents(components)

class Quaternion(Vector):
    """ Quaternion with 4-component data.
         

    """

    def setComponents(self, components):
        """ Replaces the current components of this quaternion.

        Parameters
        ----------
        components : list, None
            A sequence of numbers to be set as the contents of this quaternion.
        Returns
        -------

        """

        self._data = Quat() if components is None else Quat(*components)

    _data = Quat()
    _unit = None
    _typecode = None
    
    def __init__(self, components=None,
                 angle=None, z=None, w=None, **kwds):
        """ Create a quatnion instance.

        
         Note that some math libraries specify quaternion arguments in the order
         XYZW while others use WXYZ. This library uses XYZW, which is consistent
         with Java3D's Quat4d class and the conventions used in the Herschel/Planck
         ACMS.

        Several forms of invocation are allowed::

          * Invoking with no argument results in a vector of
        [0, 0, 0, 1] components, representing a zero rotation.
          * with one argument of a Sequence 's', the result is 
        ```x=s[0], y=s[1], z=s[2], w=s[3]```. Particularly if
        's' is also a Quaternion, a copy of 's' is created.
          * with four arguments each of which is a `float` or `int`, the argument will be taken as `x`, `y`, `z`, `w`.
          * if component is a `Seuquence` and float angle components, a `rotation` quaternion is made


        Parameters
        ----------
        components: sequence of 4 floats, or an axis.
        angle: float
           if set, component will be treated as an axis, the result is rotation about an axis for the amount of the given AxisAngle.
        Returns
        -------
        """

        cc = components.__class__
        if issubclass(cc, Vector):
            components = components._data
            cc = components.__class__
            
        if components is None:
            if angle is None:
                super(Quaternion, self).__init__(components, **kwds)
                self.setComponents((0, 0, 0, 1))
            else:
                raise TypeError(f'When the first component given to Quaternion initialization is `None`, the rest three all should be `None`.')
        elif issubclass(cc, Quaternion):
            super(Quaternion, self).__init__(components, **kwds)
            if issubclass(angle.__class__, Number):
                """
                Create a unit Quaternion corresponding to a rotation of 'angle' about 'axis'.
                The axis vector need not be normalized.
                """

                axis = components

                # Normalizing the vector ensures the quaternion is normalized.
                v = axis.normalize()
                sd = v._data
                sinA = _sin(angle / 2)
                cosA = _cos(angle / 2)
                self.setComponents((sd[0]*sinA,
                                    sd[1]*sinA,
                                    sd[2]*sinA,
                                    cosA))

            elif angle is None:
                # Create a copy of another Quaternion.
                self.setComponents(components)
        elif issubclass(cc, Sequence):
            if angle is None:
                super(Quaternion, self).__init__(components, **kwds)
                self.setComponents(components)
            elif issubclass(angle.__class__, Number):
                if len(components) == 3:
                    super(Quaternion, self).__init__(components, **kwds)
                    # rotation
                    self.mRotate(components, angle)
                else:
                    raise TypeError('When angle is a number, the first arguement must be a vector with 3 components.')
            else:
                raise TypeError('When component is a Sequence, angle should be a Number or None.')
        elif issubclass(cc, Number):
            if issubclass(angle.__class__, Number) and \
               issubclass(z.__class__, Number) and \
               issubclass(w.__class__, Number):
                # input is x, y, z, w
                _c = (components, angle, z, w)
                super(Quaternion, self).__init__(_c, **kwds)
                self.setComponents(_c)
            else:
                raise TypeError(f'When the first component given to Quaternion initialization is float ({components}), the rest three all should be floats.')
        else:
            raise TypeError(f'Invalid parameters for making a Quaternion: {components} {angle}, z = {z}, w = {w}.')

    def mNormalize(self):
        """
 
        Normalize to unit length, in place.
        
        The normalization is skipped if the vector is already normalized.
        This version changes `_data` container, because it is immutable.
        Still is in place w.r.t this Quaternion.
        
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
            newd = Quat(sd[0]/norm, sd[1]/norm, sd[2]/norm, sd[3]/norm)
            self._data = newd
        self._norm = 1
        return self

    def mRotate(self, axis, angle):
        """Set the current quaternion to be the rotation of a given angle around a given axis.

        Parameters
        ----------
        axis : Vector3D, Vector
            The axis to rotate around.
        angle : float, int
            The angle to rotate by.

        Returns
        -------
        None
            None

        Examples
        --------
        FIXME: Add docs.

        """
        if not issubclass(axis.__class__, Vector):
            axis = Vector(axis)
        na = axis.normalize()

        sinA = _sin(angle / 2)
        cosA = _cos(angle / 2)

        sd = self._data
        qd = na._data
        _x = qd[0] * sinA
        _y = qd[1] * sinA
        _z = qd[2] * sinA
        _w = cosA
        self._data = Quat(_x, _y, _z, _w)
        self._norm = None
        return self
    
    
    @staticmethod
    def rotation(v1, v2):
        """Create the Quaternion that gives the shortest rotation from v1 to v2.
             
        parameters
        ----------
        v1: Vector
               Initial vector
        v2: Vector
                Final vector
        return
        ------
        Quaternion that rotates v1 to v2

        throws
        ------
        ValueError if v1 and v2 are collinear
        """
        return Quaternion(v1.cross(v2), v1.angle(v2))

    @staticmethod
    def xRotation(angle):
        """ Create an active rotation about the X axis.

        parameters
        ----------
        angle: float
             Rotation angle in radians
        return
        ------
        Quaternion representing the rotation
        """

        return Quaternion(_sin(angle / 2), 0, 0, _cos(angle / 2))

    @staticmethod
    def yRotation(angle):
        """ Create an active rotation about the Y axis.

        parameters
        ----------
        angle: float
             Rotation angle in radians
        return
        ------
        Quaternion representing the rotation
        """

        return Quaternion(0, _sin(angle / 2), 0, _cos(angle / 2))

    @staticmethod
    def zRotation(angle):
        """ Create an active rotation about the Z axis.

        parameters
        ----------
        angle: float
             Rotation angle in radians
        return
        ------
        Quaternion representing the rotation
        """
        return Quaternion(0, 0, _sin(angle / 2), _cos(angle / 2))

    def cross(self, v):
        """
        Return the cross product of this quaternion by another quaternion, as
        a new quaternion.

        param v The other vector.
        """

        sd = self._data
        qd = v._data
        return Vector3D((sd[1] * qd[2] - sd[2] * qd[1], sd[2] * qd[0] - sd[0] * qd[2], sd[0] * qd[1] - sd[1] * qd[0]))

    def set(self, q):
        """
        Set this Quaternion equal to another one.

        parameters
        ----------
        q The quaternion
        """
        
        self.setComponents(q._data)

 
    def XtoMatrix3(self):
        """
        Return the rotation matrix that corresponds to this Quaternion.<p>

        If the quaternion represents an active rotation, the matrix will
        also be an active rotation.

        return A rotation matrix equivalent to this quaternion
        """

        m = Matrix3()
        m.set(self)
        return m

 
    def toAttitude(self, deg=False):
        """
        Convert this Quaternion to an equivalent Attitude.
        
        The quaternion does not have to be normalized.

        Parameters
        ----------
        deg:   bool
            Output in degrees instead of radians.
        RETURN
        ------
        Attitude
            an Attitude equivalent to this Quaternion
        """
      
        sd = self._data
        xx = sd.x * sd.x
        yy = sd.y * sd.y
        zz = sd.z * sd.z
        ww = sd.w * sd.w
        d  = sd.x * sd.z - sd.y * sd.w
        uu = xx + yy + zz + ww
        xa = 0
        ya = 0
        za = 0
         
        # Set the threshold for special handling close to poles.
        # If this is set too low, the accuracy of RA and POS suffers.
        # If it is set too high, the accuracy of DEC suffers (as it is rounded).
        # 1E-13 degrees is a good trade-off.
        # 	 
        threshold = 1E-13
        #  DEC=89.999974 degrees (0.09 arcsec)
        limit = 0.5 * (1 - threshold)
        sd = self._data
        if abs(d) > limit * uu:
            #  Close to a pole
            za = -_atan2(2 * (sd.x * sd.y - sd.z * sd.w), yy + ww - xx - zz)
            if d >= 0:
                ya = pi / 2
            else:
                ya = -pi / 2
        else:
            xa = -_atan2(2 * (sd.y * sd.z + sd.x * sd.w), zz + ww - xx - yy)
            ya = _asin(2 * d / uu)
            za = _atan2(2 * (sd.x * sd.y + sd.z * sd.w), xx + ww - yy - zz)
            if za < 0:
                za += (pi + pi)
                
        return Attitude(za*RAD, ya*RAD, xa*RAD) if deg else Attitude(za, ya, xa)


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
    def Xx(self, x):
        """ for property setter

        Parameters
        ----------
        x : int, float
        The first component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        self.setX(x)

    def getX(self):
        """ Returns the actual x that is allowed for the x
        of this quaternion.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[0]

    def XsetX(self, x):
        """ Replaces the current x of this quaternion.

        Parameters
        ----------
        x : int, float
        The first component of the quaternion part of the Quaternion.

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
    def Xy(self, y):
        """ for property setter

        Parameters
        ----------
        y : int, float
        The second component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        self.setY(y)

    def getY(self):
        """ Returns the actual y
        of this quaternion.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[1]

    def XsetY(self, y):
        """ Replaces the current y of this quaternion.

        Parameters
        ----------
        y : int, float
        The second component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        if not isinstance(y, Number):
            raise TypeError('Y must be a number.')

        self._data[1] = y

    
    @ property
    def z(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getZ()

    @ z.setter
    def Xz(self, z):
        """ for property setter

        Parameters
        ----------
        z : int, float
        The third component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        self.setZ(z)

    def getZ(self):
        """ Returns the actual z
        of this quaternion.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[2]

    def XsetZ(self, z):
        """ Replaces the current z of this quaternion.

        Parameters
        ----------
        z : int, float
        The third component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        if not isinstance(z, Number):
            raise TypeError('Z must be a number.')

        self._data[2] = z

    @ property
    def w(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------
        """
        return self.getW()

    @ w.setter
    def Xw(self, w):
        """ for property setter

        Parameters
        ----------
        w : int, float
        The third component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        self.setW(w)

    def getW(self):
        """ Returns the actual w
        of this quaternion.

        Parameters
        ----------

        Returns
        -------

        """
        return self._data[3]

    def XsetW(self, w):
        """ Replaces the current w of this quaternion.

        Parameters
        ----------
        w : int, float
        The third component of the quaternion part of the Quaternion.

        Returns
        -------

        """
        if not isinstance(w, Number):
            raise TypeError('W must be a number.')

        self._data[3] = w
 
    def normalize(self):
        """
        Normalize this quaternion, returning a new object.

        RETURNS
        -------
        Quaternion
            A new normalized quaternion
        """

        return self.copy().mNormalize()

 
    def mNormalizeSign(self):
        """
        Normalize the signs to ensure scalar component is non-negative.
        
        Negating all four components of a quaternion, effectively adds
        PI to the rotation angle. This is equivalent to a rotation of
        (2*PI - angle) in the opposite direction. However, when using 
        quaternions to represent attitudes this is irrelevant and it
        is convenient to normalize the quaternion so that the scalar
        component is non-negative. 

        RETURNS
        -------
        Quaternion
            This quaternion after normalization
        """
      
        sd = self._data
        if sd.w < 0:
            sd = self._data
            _x = -sd.x
            _y = -sd.y
            _z = -sd.z
            _w = -sd.w
            self._data = Quat(_x, _y, _z, _w)
        return self

 
    def normalizeSign(self):
        """
        Normalize the signs to ensure scalar component is non-negative,
             returning a new object.

        return A new quaternion with normalized signs.
        See `mNormalizeSign`
        """
        return self.copy().mNormalizeSign()

 
        """
        Return the magnitude (norm) of this quaternion.<p>
             This is 1 if the quaternion is normalized.
             return Magnitude of this quaternion
             deprecated Use norm method
      
        def magnitude(self):
        
        return sqrt(self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z)

        """
 
    def norm(self):
        """             Return the L2 norm of this quaternion.

             return L2 norm of this quaternion
        """
         
       
        sd = self._data
        return _sqrt(sd[0] * sd[0] + sd[1] * sd[1] + sd[2] * sd[2] + sd[3] * sd[3])

 
    def normSquared(self):
        """
        Return the square of the L2 norm of this quaternion.

        RETURN
        ------
        float
            Squarer of the L2 norm of this quaternion
        """
      
        sd = self._data
        return sd[0] * sd[0] + sd[1] * sd[1] + sd[2] * sd[2] + sd[3] * sd[3]

 
    def mMultiply(self, q):
        """
        Multiply this quaternion by another one, in place.<p>
        This is the Grassman product, which corresponds to composition
        of two rotations. If A and B are active rotations, A.B is
        rotation A followed by rotation B.

        PARAMETERS
        ----------
        q : Quaternion
            The other quaternion

        RETURNS
        -------
        Quaternion
            This quaternion after multication by other quaternion
        """
        
        sd = self._data
        qd = q._data
        
        _x = sd.w * qd.x + sd.x * qd.w + sd.y * qd.z - sd.z * qd.y
        _y = sd.w * qd.y + sd.y * qd.w + sd.z * qd.x - sd.x * qd.z
        _z = sd.w * qd.z + sd.z * qd.w + sd.x * qd.y - sd.y * qd.x
        _w = sd.w * qd.w - sd.x * qd.x - sd.y * qd.y - sd.z * qd.z

        self._data = Quat(_x, _y, _z, _w)
        self._norm = None
        
        return self

 
        """
             Multiply this quaternion by another one, returning a new object.
        @parameters
        ----------
        q The other quaternion
             @return The Grassman product
             @see #mMultiply
        """
        
    def multiply(self, q):

        return self.copy().mMultiply(q)

    __mul__ = multiply
    __imul__ = mMultiply
    
    def mConjugate(self):
        """
        Conjugate this quaternion in place.
        @return This quaternion after conjugation
      
        """
        sd = self._data
        _x = -sd.x
        _y = -sd.y
        _z = -sd.z
        _w = sd.w
        self._data = Quat(_x, _y, _z, _w)
        return self

 
    def conjugate(self):
        """
        Conjugate this quaternion, returning a new object.
        @return The conjugate
        """
      
        return self.copy().mConjugate()

 
    def mConjugateWith(self, a):
        """
        Conjugate this quaternion with unit quaternion <tt>a</tt>, in place.<p>

        This quaternion <tt>b</tt>, becomes a.b.a*.<p>
             
        This method is deprecated and replaced by <tt>rotate(Quaternion)</tt>.
        Note that the new method computes B.A.Binv instead of A.B.A*, with the
        roles of A and B interchanged. The use of inverse avoids the need to
        normalize the quaternion.

        parameters
        ----------
        a The other quaternion A
             @return This quaternion after conjugation with A
             @deprecated Use qb.rotate(qa) instead of qa.copy().mConjugateWith(qb.normalize())
        """
        sd = self._data      
        qd = a._data
        w = qd.w
        x = qd.x
        y = qd.y
        z = qd.z
        w2 = w * w
        x2 = x * x
        y2 = y * y
        z2 = z * z
        wz = w * z
        xy = x * y
        wy = w * y
        xz = x * z
        yz = y * z
        wx = w * x
        xr = 2 * ((xy - wz) * sd.y + (wy + xz) * sd.z) + (w2 + x2 - y2 - z2) * sd.x
        yr = 2 * ((xy + wz) * sd.x + (yz - wx) * sd.z) + (w2 - x2 + y2 - z2) * sd.y
        sd.z = 2 * ((xz - wy) * sd.x + (yz + wx) * sd.y) + (w2 - x2 - y2 + z2) * sd.z
        sd.w *= (w2 + x2 + y2 + z2)
        sd.x = xr
        sd.y = yr
        return self

 
    def rotate(self, p):
        """
        Rotate the rotation P with this Quaternion Q, returning Q.P.Qinv.
        If this quaternion Q represents the rotation of frame B with respect to 
        frame A, then <tt>Q.rotate(P)</tt> transforms the rotation P from frame A
        to frame B. Also, <tt>Q.conjugate().rotate(P)</tt>transforms P from frame B
        to frame A.
             
        <tt>Q.rotate(P) == Q.multiply(P).multiply(Q.conjugate())</tt>
             
        PARAMETERS
        ----------
        p : Quaternion
            to be rotated
        
        RETURNS
        -------
        Quaternion
            Rotated quaternion

        THROWS
        ------
        ValueError if this quaternion is zero
        """
      
        if not issubclass(p.__class__, Quaternion):
            raise TypeError('A quaternion is needed for rotate.')
        
        sd = self.normalize()._data
        qd = p._data

        vx = qd[0]
        vy = qd[1]
        vz = qd[2]
        ax = sd.y * vz - sd.z * vy
        ay = sd.z * vx - sd.x * vz
        az = sd.x * vy - sd.y * vx
        rx = 2 * (sd.w * ax + sd.y * az - sd.z * ay) + vx
        ry = 2 * (sd.w * ay + sd.z * ax - sd.x * az) + vy
        rz = 2 * (sd.w * az + sd.x * ay - sd.y * ax) + vz
        return Quaternion(rx, ry, rz, qd[3])

 
        """
             Return the dot product of this quaternion with another.
             @parameters
        ----------
q The other quaternion
             @return The dot product
        """
    def dot(self, q):
        sd = self._data
        qd = q._data
        return sd.w * qd.w + sd.x * qd.x + sd.y * qd.y + sd.z * qd.z

 
    def toAxisAngle(self):
        """
             Return the rotation axis and angle.<p>
             If the angle is zero, the axis vector is set to (1,0,0).
             @return The rotation expressed as an AxisAngle
        """
      
        a = self.angle()
        sd = self._data
        if a == 0:
            return self.AxisAngle(Vector3D(1, 0, 0), 0)
        else:
            v = Vector3D(sd.x, sd.y, sd.z)
            return self.AxisAngle(v.normalize(), a)

 
    def axis(self):
        """
        Return the unit vector of the rotation axis.<p>

        If the angle is zero, the axis vector is set to (1,0,0).

        RETURNS
        -------
        The normalized axis vector
        """
      
        sd = self._data
        a = self.angle()
        if a == 0:
            return Vector3D((1, 0, 0))
        else:
            return Vector3D(sd[:3]).mNormalize()

 
    def angle(self):
        """
        Return the rotation angle (radians) about the axis vector.

        The result is in the range 0 to 2*PI.
        The quaternion need not be normalized.
        
        RETURNS
        -------
        
        The rotation angle in radians
        """
        sd = self._data
        r = _sqrt(sd.x * sd.x + sd.y * sd.y + sd.z * sd.z)
        return 2 * _atan2(r, sd.w)

 
    def equals(self, obj):
        """
             Return true if this quaternion is equal to another quaternion.<p>
             Equality is defined such that NaN=NaN and -0!=+0, which
             is appropriate for use as a hash table key.
        @parameters
        ----------
        obj The object to be compared
        @return true if the objects are equal
        """
      
        if not (isinstance(obj, (Quaternion, ))):
            return False
        sd = self._data
        qd = obj._data

        return ((sd[0]) == (qd[0])) and ((sd[1]) == (qd[1])) and ((sd[2]) == (qd[2])) and ((sd[3]) == (qd[3]))

 
    # def hashCode(self):
    #     """
    #          Return the hash code of this quaternion.
    #          @return The hash code
    #     """
      
    #     result = 17
    #     f = Double.doubleToLongBits(sd.x)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     f = Double.doubleToLongBits(sd.y)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     f = Double.doubleToLongBits(sd.z)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     f = Double.doubleToLongBits(sd.w)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     return result

 
    def epsilonEquals(self, q, epsilon=None, fraction=1e-10):
        """
        Returns true if this quaternion is approximately equal to another.
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
            try:
                s = abs(sd.x) + abs(qd.x)
                dx = 0 if (s) <= 1e-12 else abs((sd.x - qd.x)/s)
                s = abs(sd.y) + abs(qd.y)
                dy = 0 if (s) <= 1e-12 else abs((sd.y - qd.y)/s)
                s = abs(sd.z) + abs(qd.z)
                dz = 0 if (s) <= 1e-12 else abs((sd.z - qd.z)/s)
                s = abs(sd.w) + abs(qd.w)
                dw = 0 if (s) <= 1e-12 else abs((sd.w - qd.w)/s)
            except ZeroDivisionError:
                return False
            return max(dx, dy, dz, dw) <= fraction/2
        else:
            dx = abs(sd.x - qd.x)
            dy = abs(sd.y - qd.y)
            dz = abs(sd.z - qd.z)
            dw = abs(sd.w - qd.w)
            return max(dx, dy, dz, dw) <= epsilon
 
    def Xcopy(self):
        """
             Return a copy of this quaternion.
             @return A copy of this quaternion
        """      

        return Quaternion(self)

 
    def clone(self):
        """
             Return a clone of this object.
             @return A clone of this quaternion
        """      

        try:
            return super(Quaternion, self).clone()
        except CloneNotSupportedException as e:
            raise Error("Assertion failed")

 
    def XXX__str__(self):
        """
             Return a string representation of the quaternion.<p>
             The exact details of the representation are unspecified
             and subject to change.
             @return String representation of this object
        """
      
        return "[" + sd.x + ", " + sd.y + ", " + sd.z + ", " + sd.w + "]"

 
    def rotateVector(self, v):
        """
        Rotate a vector.

        This returns <tt>Q.[0,V].Qinv</tt>, where <tt>[0,V]</tt> is a quaternion
        with scalar part 0 and vector part V.
             
        If the quaternion Q represents the rotation of frame B with respect to 
        frame A, then <tt>Q.rotateVector(v)</tt> is an active rotation of a vector
        in frame A or a passive transformation of a vector from frame B to frame A.

        PARAMETERS
        ----------
        v : Vector3D
            The vector to be rotated
        
        RETURNS
        -------
        Vecter3D
            The rotated vector.
        """
      
        sd = self.normalize()._data
        qd = v._data

        vx = qd[0]
        vy = qd[1]
        vz = qd[2]
        ax = sd.y * vz - sd.z * vy
        ay = sd.z * vx - sd.x * vz
        az = sd.x * vy - sd.y * vx
        rx = 2 * (sd.w * ax + sd.y * az - sd.z * ay) + vx
        ry = 2 * (sd.w * ay + sd.z * ax - sd.x * az) + vy
        rz = 2 * (sd.w * az + sd.x * ay - sd.y * ax) + vz
        return Vector3D((rx, ry, rz))

 
    def rotateAxes(self, v):
        """
        Inverse rotation of a vector.
        
        This returns <tt>Qinv.[0,V].Q</tt>, where [0,V] is a Quaternion 
        with scalar part 0 and vector part V. It is equivalent to 
            <tt>Q.inverse().rotateVector(v)</tt><p>
             
        If the quaternion Q represents the rotation of frame B with respect to 
        frame A, then <tt>Q.rotateAxes(v)</tt> is passive transformation of 
        a vector from frame A to frame B or an active rotation of a vector in 
        frame B.

        PARAMETERS
        ----------
        v : Vector3D
            The vector to be transformed

        RETURNS
        -------
        Vector3D
             The transformed vector.
        """
      
        return self.conjugate().rotateVector(v)

    def rotateI(self):
        """ 
        Return the I vector rotated by this quaternion.
        
        This is the X axis in the rotated frame.
        It is equivalent to rotateVector(new Vector3D(1,0,0)).
             
        RETURNS
        -------
        Vector3D
            I vector rotated by this quaternion.
        """      

        sd = self._data
        m2 = sd.w * sd.w + sd.x * sd.x + sd.y * sd.y + sd.z * sd.z
        if m2 == 0:
            raise ValueError("Zero quaternion")
        rx = -2 * (sd.y * sd.y + sd.z * sd.z) / m2 + 1
        ry = 2 * (sd.w * sd.z + sd.x * sd.y) / m2
        rz = 2 * (sd.x * sd.z - sd.w * sd.y) / m2
        return Vector3D((rx, ry, rz))

    def rotateJ(self):
        """
        Return the J vector rotated by this quaternion.<p>
             
        This is the Y axis in the rotated frame.
        It is equivalent to rotateVector(new Vector3D(1,0,0)).
             
        RETURNS
        -------
        Vector3D
            J vector rotated by this quaternion.
        """      

        sd = self._data
        m2 = sd.w * sd.w + sd.x * sd.x + sd.y * sd.y + sd.z * sd.z
        if m2 == 0:
            raise ValueError("Zero quaternion")
        rx = 2 * (sd.y * sd.x - sd.w * sd.z) / m2
        ry = -2 * (sd.z * sd.z + sd.x * sd.x) / m2 + 1
        rz = 2 * (sd.w * sd.x + sd.y * sd.z) / m2
        return Vector3D((rx, ry, rz))

 
    def rotateK(self):
        """
        Return the K vector rotated by this quaternion.<p>
             
        This is the Z axis in the rotated frame.
        It is equivalent to rotateVector(new Vector3D(0,0,1)).
             
        RETURNS
        -------
        Vector3D
            K vector rotated by this quaternion.
        """      

        sd = self._data
        m2 = sd.w * sd.w + sd.x * sd.x + sd.y * sd.y + sd.z * sd.z
        if m2 == 0:
            raise ValueError("Zero quaternion")
        rx = 2 * (sd.w * sd.y + sd.z * sd.x) / m2
        ry = 2 * (sd.z * sd.y - sd.w * sd.x) / m2
        rz = -2 * (sd.x * sd.x + sd.y * sd.y) / m2 + 1
        return Vector3D((rx, ry, rz))

 
    def isNormalized(self, epsilon):
        """
             Test whether the quaternion is normalized.<p>
             The quaternion is considered normalized if the square of its
             norm does not differ from one by more than 2*epsilon.

        parameters
        ----------
        epsilon : float
             Allowed tolerance
        """
      
        sd = self._data
        sq = sd.w * sd.w + sd.x * sd.x + sd.y * sd.y + sd.z * sd.z
        return abs(sq - 1) <= epsilon * 2

    def mPower(self, t):
        """ 
             Raise a quaternion to a scalar power, in-place.<p>
             
             This returns a quaternion with unit norm and hence does
             not raise the norm to the exponent.
             @parameters
        ----------
        t The exponent
             RETURNS The resulting quaternion
        """
      
        theta = t * self.angle() / 2
        v = self.axis()
        s = _sin(theta)
        sd.w = _cos(theta)
        sd.x = v.getX() * s
        sd.y = v.getY() * s
        sd.z = v.getZ() * s
        return self

    __ipow__ = mPower


    def sqrt(self):
        """
        Return the square root of this quaternion.<p>
             
        This method is faster than <tt>mPower(0.5)</tt>.
        It returns the positive sqrt for [0,0,0,1] and throws an exception for [0,0,0,-1].
             
        @throws ValueError if this quaternion normalized is [0,0,0,-1].

        """         
      
        q = self.normalize()
        q._data.w += 1
        return q.normalize()

    
    def slerp(self, q, alpha):
        """ 
             Spherical Linear Interpolation (SLERP) between two quaternions.<p>
             Equivalent to <tt>slerp(q, alpha, true)</tt>

             parameters
             ----------
             q : Quaternion
                 The other quaternion
             alpha: float
                 The interpolation factor
             return
             ------
               The interpolated quaternion
        """
      
        return self.slerp_0(q, alpha, True)

 
    def slerp_0(self, q, alpha, shortest):
        """
             Spherical Linear Interpolation (SLERP) between two quaternions.<p>
             For interpolation, <tt>alpha</tt> is in the range [0,1].
             When <tt>alpha=0</tt>, the result equals this quaternion.
             When <tt>alpha=1</tt>, the result equals the other quaternion 
             (possibly negated). Values outside the range [0,1] may be used 
             for extrapolation.<p>

             If <tt>shortest==true</tt> and the angle between the quaternions, in 4-space 
             is greater than 90 degrees, one of the quaternions is negated so that rotation 
             is in the shortest direction.
             @parameters
        ----------
q The other quaternion
             @parameters
        ----------
alpha The interpolation factor
             @parameters
        ----------
shortest Return the shortest rotation
             RETURNS The interpolated quaternion
        """
      
        qb = q.copy()
        #  If angle (in 4D) > 90 degrees, invert one of the quaternions,
        #  to give an acute angle, to rotate in the shortest direction.
        if shortest and self.dot(qb) < 0:
            qb.mMultiply(-1)
        return self.multiply(self.conjugate().mMultiply(qb).mPower(alpha))

    def lerp(self, q, alpha):

        sd = self._data
        qb = q.copy()
        qd = qb.data
        if self.dot(qb) < 0:
            qb.mMultiply(-1)
        beta = 1 - alpha
        x = sd.x * beta + qd.x * alpha
        y = sd.y * beta + qd.y * alpha
        z = sd.z * beta + qd.z * alpha
        w = sd.w * beta + qd.w * alpha
        return Quaternion(x, y, z, w)


    def mMultiply_0(self, k):

        sd = self._data
        _x = sd[0] * k
        _y = sd[1] * k
        _z = sd[2] * k
        _w = sd[3] * k
        self._data = Quat(_x, _y, _z, _w)
        self._norm = None
        return self

    def mAdd(self, q):

        sd = self._data
        qd = q._data
        _x = sd[0] + qd.x
        _y = sd[1] + qd.y
        _z = sd[2] + qd.z
        _w = sd[3] + qd.w
        self._data = Quat(_x, _y, _z, _w)
        self._norm = None
        return self
    
    __iadd__ = mAdd

    def mSubtract(self, q):

        sd = self._data
        qd = q._data
        _x = sd[0] - qd.x
        _y = sd[1] - qd.y
        _z = sd[2] - qd.z
        _y = sd[3] - qd.w
        self._data = Quat(_x, _y, _z, _w)
        self._norm = None
        return self

    __isub__ = mSubtract


