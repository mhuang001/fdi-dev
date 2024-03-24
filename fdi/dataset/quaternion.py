#!/usr/bin/env python


from .datatypes import Vector

from collections.abc import Sequence
""" generated source for module <stdin> """

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

class Quaternion(Vector):
    """ Quaternion with 4-component data.
    """

    def __init__(self, components=None, **kwds):
        """ invoked with no argument results in a vector of
        [0, 0, 0, 0] components
        
        Parameters
        ----------
        components : list
            The four components.
        
        Returns
        -------
        """
        super(Quaternion, self).__init__(**kwds)

        if components is None:
            self._data = [0, 0, 0, 0]
        else:
            self.setComponents(components)

class aQuaternion(Vector):
    """ Quaternion with 4-component data.
         

    """
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
          * with four arguments each of which is a `float`, the argument will be taken as `x`, `y`, `z`, `w`.
          * 
        [0, 0, 0, 1] components


        Parameters
        ----------
        components: sequence of 4 floats, or an axis.
        angle: float
           if set, component will be treated as an axis, the result is rotation about an axis for the amount of the given AxisAngle.
        Returns
        -------
        """

        super(Quaternion, self).__init__(**kwds)

        cc = components.__class__
        if components is None:
            if angle is None:
                self._x = 0
                self._y = 0
                self._z = 0
                self._w = 1
                self._data = [0, 0, 0, 1]
            else:
                raise TypeError(f'When the first component given to Quaternion initialization is `None`, the rest three all should be `None`.')
        elif issubclass(cc, Quaternion):
            if issubclass(angle.__class__, float):
                """
                Create a unit Quaternion corresponding to a rotation of 'angle' about 'axis'.
                The axis vector need not be normalized.
                """
                axis = components

                # Normalizing the vector ensures the quaternion is normalized.
                v = axis.normalize()
                sinA = sin(angle / 2)
                cosA = cos(angle / 2)
                self._x = v.getX() * sinA
                self._y = v.getY() * sinA
                self._z = v.getZ() * sinA
                self._w = cosA
                self._data = [self._x, self._y, self._z, self._w]

            elif angle is None:
                # Create a copy of another Quaternion.
                self._x, self._y, self._z, self._w = tuple(components[:4])
                self.setComponents(components[:4])
        elif issubclass(cc, Sequence):
                self._x, self._y, self._z, self._w = tuple(components[:4])
                self.setComponents(components[:4])
        elif issubclass(cc, (float)):
            if issubclass(angle.__class__, float) and \
               issubclass(z.__class__, float) and \
               issubclass(w.__class__, float):
                # input is x, y, z, w
                self._data = [components, angle , z, w]
                self._x, self._y, self._z, self._w = (components, angle , z, w)
            else:
                raise TypeError(f'When the first component given to Quaternion initialization is float ({components}), the rest three all should be floats.')
        else:
            raise TypeError(f'Invalid parameters for making a Quaternion: {components} {angle}, z = {z}, w = {w}.')

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
        RuntimeException if v1 and v2 are collinear
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

        return Quaternion(sin(angle / 2), 0, 0, cos(angle / 2))

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

        return Quaternion(0, sin(angle / 2), 0, cos(angle / 2))

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
        return Quaternion(0, 0, sin(angle / 2), cos(angle / 2))

    def set(self, q):
        """
        Set this Quaternion equal to another one.

        parameters
        ----------
        q The quaternion
        """
        
        self._x = q._x
        self._y = q._y
        self._z = q._z
        self._w = q._w

 
    def toMatrix3(self):
        """
        Return the rotation matrix that corresponds to this Quaternion.<p>

        If the quaternion represents an active rotation, the matrix will
        also be an active rotation.

        return A rotation matrix equivalent to this quaternion
        """

        m = Matrix3()
        m.set(self)
        return m

 
    def toAttitude(self):
        """
             Convert this Quaternion to an equivalent Attitude.<p>
             The quaternion does not have to be normalized.
             return an Attitude equivalent to this Quaternion
        """
      
        """ generated source for method toAttitude """
        xx = self._x * self._x
        yy = self._y * self._y
        zz = self._z * self._z
        ww = self._w * self._w
        d = self._x * self._z - self._y * self._w
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
        if abs(d) > limit * uu:
            #  Close to a pole
            za = -atan2(2 * (self._x * self._y - self._z * self._w), yy + ww - xx - zz)
            if d >= 0:
                ya = PI / 2
            else:
                ya = -PI / 2
        else:
            xa = -atan2(2 * (self._y * self._z + self._x * self._w), zz + ww - xx - yy)
            ya = asin(2 * d / uu)
            za = atan2(2 * (self._x * self._y + self._z * self._w), xx + ww - yy - zz)
        return Attitude(za, ya, xa)

 
    def getX(self):
        """
             Return the X component of the quaternion.
             return The X component
        """
        return self._x

 
    def getY(self):
        """
             Return the Y component of the quaternion.
             return The Y component
        """
        return self._y

 
    def getZ(self):
        """
             Return the Z component of the quaternion.
             return The Z component
        """
        return self._z

 
    def getW(self):
        """
             Return the W (scalar) component of the quaternion.
             return The W component
        """
        return self._w

 
    def mNormalize(self):
        """
        Normalize this quaternion.<p>
             
        The normalization is skipped if the Quaternion is already normalized.
        return This quaternion after normalization
        """
   
        n2 = normSquared()
        if n2 == 0:
            raise RuntimeException("Cannot normalize zero quaternion")
        #  Do nothing if it is already normalized
        if abs(n2 - 1) > 5E-16:
            #  ULP = 2.22E-16
            norm = sqrt(n2)
            self._w /= norm
            self._x /= norm
            self._y /= norm
            self._z /= norm
        return self

 
    def normalize(self):
        """
             Normalize this quaternion, returning a new object.
             return A new normalized quaternion
        """
        return self.copy().mNormalize()

 
    def mNormalizeSign(self):
        """
             Normalize the signs to ensure scalar component is non-negative.<p>
             Negating all four components of a quaternion, effectively adds
             PI to the rotation angle. This is equivalent to a rotation of
             (2*PI - angle) in the opposite direction. However, when using 
             quaternions to represent attitudes this is irrelevant and it
             is convenient to normalize the quaternion so that the scalar
             component is non-negative. 
             return This quaternion after normalization
        """
      
        """ generated source for method mNormalizeSign """
        if self._w < 0:
            self._x = -self._x
            self._y = -self._y
            self._z = -self._z
            self._w = -self._w
        return self

 
    def normalizeSign(self):
        """
        Normalize the signs to ensure scalar component is non-negative,
             returning a new object.

             return A new quaternion with normalized signs
             see #mNormalizeSign
        """
        """ generated source for method normalizeSign """
        return copy().mNormalizeSign()

 
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
         
       
        return sqrt(self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z)

 
    def normSquared(self):
        """
             Return the square of the L2 norm of this quaternion.
             return Squarer of the L2 norm of this quaternion
        """
      

        return self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z

 
    def mMultiply(self, q):
        """
             Multiply this quaternion by another one, in place.<p>
             This is the Grassman product, which corresponds to composition
             of two rotations. If A and B are active rotations, A.B is
             rotation A followed by rotation B.
        parameters
        ----------
        q The other quaternion
        return This quaternion after multication by other quaternion
        """
      
        x = self._w * q._x + self._x * q._w + self._y * q._z - self._z * q._y
        y = self._w * q._y + self._y * q._w + self._z * q._x - self._x * q._z
        z = self._w * q._z + self._z * q._w + self._x * q._y - self._y * q._x
        self._w = self._w * q._w - self._x * q._x - self._y * q._y - self._z * q._z
        self._x = x
        self._y = y
        self._z = z
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
        """ generated source for method multiply """
        return copy().mMultiply(q)

 
    def mConjugate(self):
        """
             Conjugate this quaternion in place.
             @return This quaternion after conjugation
      
        """
        self._x = -self._x
        self._y = -self._y
        self._z = -self._z
        return self

 
    def conjugate(self):
        """
             Conjugate this quaternion, returning a new object.
             @return The conjugate
        """
      
        return copy().mConjugate()

 
    def mConjugateWith(self, a):
        """
             Conjugate this quaternion with unit quaternion <tt>a</tt>, in place.<p>

             This quaternion <tt>b</tt>, becomes a.b.a*.<p>
             
             This method is deprecated and replaced by <tt>rotate(Quaternion)</tt>.
             Note that the new method computes B.A.Binv instead of A.B.A*, with the
             roles of A and B interchanged. The use of inverse avoids the need to
             normalize the quaternion.
             @parameters
        ----------
        a The other quaternion A
             @return This quaternion after conjugation with A
             @deprecated Use qb.rotate(qa) instead of qa.copy().mConjugateWith(qb.normalize())
        """
      
        
        w = a._w
        x = a._x
        y = a._y
        z = a._z
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
        xr = 2 * ((xy - wz) * self._y + (wy + xz) * self._z) + (w2 + x2 - y2 - z2) * self._x
        yr = 2 * ((xy + wz) * self._x + (yz - wx) * self._z) + (w2 - x2 + y2 - z2) * self._y
        self._z = 2 * ((xz - wy) * self._x + (yz + wx) * self._y) + (w2 - x2 - y2 + z2) * self._z
        self._w *= (w2 + x2 + y2 + z2)
        self._x = xr
        self._y = yr
        return self

 
    def rotate(self, p):
        """
             Rotate the rotation P with this Quaternion Q, returning Q.P.Qinv.<p>
             
             If this quaternion Q represents the rotation of frame B with respect to 
             frame A, then <tt>Q.rotate(P)</tt> transforms the rotation P from frame A
             to frame B. Also, <tt>Q.conjugate().rotate(P)</tt>transforms P from frame B
             to frame A.<p>
             
             <tt>Q.rotate(P) == Q.multiply(P).multiply(P.conjugate())</tt><p>
             
        @parameters
        ----------
        p Quaternion to be rotated
             @return Rotated quaternion
             @throws RuntimeException if this quaternion is zero
        """
      
        
        m2 = self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z
        if m2 == 0:
            raise RuntimeException("Zero quaternion")
        vx = p.getX()
        vy = p.getY()
        vz = p.getZ()
        ax = self._y * vz - self._z * vy
        ay = self._z * vx - self._x * vz
        az = self._x * vy - self._y * vx
        rx = 2 / m2 * (self._w * ax + self._y * az - self._z * ay) + vx
        ry = 2 / m2 * (self._w * ay + self._z * ax - self._x * az) + vy
        rz = 2 / m2 * (self._w * az + self._x * ay - self._y * ax) + vz
        return Quaternion(rx, ry, rz, p.getW())

 
        """
             Return the dot product of this quaternion with another.
             @parameters
    def dot(self, q):
        ----------
q The other quaternion
             @return The dot product
        """
        """ generated source for method dot """
        return self._w * q._w + self._x * q._x + self._y * q._y + self._z * q._z

 
    def toAxisAngle(self):
        """
             Return the rotation axis and angle.<p>
             If the angle is zero, the axis vector is set to (1,0,0).
             @return The rotation expressed as an AxisAngle
        """
      
        """ generated source for method toAxisAngle """
        a = angle()
        if a == 0:
            return AxisAngle(Vector3(1, 0, 0), 0)
        else:
            v = Vector3(self._x, self._y, self._z)
            return AxisAngle(v.normalize(), a)

 
    def axis(self):
        """
             Return the unit vector of the rotation axis.<p>
             If the angle is zero, the axis vector is set to (1,0,0).
             @return The normalized axis vector
        """
      
        """ generated source for method axis """
        a = angle()
        if a == 0:
            return Vector3(1, 0, 0)
        else:
            return Vector3(self._x, self._y, self._z).mNormalize()

 
    def angle(self):
        """
             Return the rotation angle (radians) about the axis vector.<p>
             The result is in the range 0 to 2*PI.
             The quaternion need not be normalized.
             @return The rotation angle in radians
        """
      
        """ generated source for method angle """
        r = sqrt(self._x * self._x + self._y * self._y + self._z * self._z)
        return 2 * atan2(r, self._w)

 
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
      
        """ generated source for method equals """
        if not (isinstance(obj, (Quaternion, ))):
            return False
        q = obj
        return (Double.doubleToLongBits(self._x) == Double.doubleToLongBits(q._x)) and (Double.doubleToLongBits(self._y) == Double.doubleToLongBits(q._y)) and (Double.doubleToLongBits(self._z) == Double.doubleToLongBits(q._z)) and (Double.doubleToLongBits(self._w) == Double.doubleToLongBits(q._w))

 
    # def hashCode(self):
    #     """
    #          Return the hash code of this quaternion.
    #          @return The hash code
    #     """
      
    #     """ generated source for method hashCode """
    #     result = 17
    #     f = Double.doubleToLongBits(self._x)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     f = Double.doubleToLongBits(self._y)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     f = Double.doubleToLongBits(self._z)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     f = Double.doubleToLongBits(self._w)
    #     result = 37 * result + int((f ^ (bsr(f, 32))))
    #     return result

 
    def epsilonEquals(self, q, epsilon):
        """
             Returns true if this quaternion is approximately equal to another.<p>
             The criterion is that the L-infinte distance between the two quaternions
             u and v is less than or equal to epsilon.
        @parameters
        ----------
        q The other quaternion
        @parameters
        ----------
        epsilon The maximum difference
        @return true if the quaternions are approximately equal
        """
      
        """ generated source for method epsilonEquals """
        dx = abs(self._x - q._x)
        dy = abs(self._y - q._y)
        dz = abs(self._z - q._z)
        dw = abs(self._w - q._w)
        return max(dx, max(dy, max(dz, dw))) <= epsilon

 
    def copy(self):
        """
             Return a copy of this quaternion.
             @return A copy of this quaternion
        """      
        """ generated source for method copy """
        return Quaternion(self)

 
    def clone(self):
        """
             Return a clone of this object.
             @return A clone of this quaternion
        """      
        """ generated source for method clone """
        try:
            return super(Quaternion, self).clone()
        except CloneNotSupportedException as e:
            raise Error("Assertion failed")

 
    def __str__(self):
        """
             Return a string representation of the quaternion.<p>
             The exact details of the representation are unspecified
             and subject to change.
             @return String representation of this object
        """
      
        """ generated source for method toString """
        return "[" + self._x + ", " + self._y + ", " + self._z + ", " + self._w + "]"

 
    def rotateVector(self, v):
        """
             Rotate a vector.<p>
             This returns <tt>Q.[0,V].Qinv</tt>, where <tt>[0,V]</tt> is a quaternion
             with scalar part 0 and vector part V.<p>
             
             If the quaternion Q represents the rotation of frame B with respect to 
             frame A, then <tt>Q.rotateVector(v)</tt> is an active rotation of a vector
             in frame A or a passive transformation of a vector from frame B to frame A.
             @parameters
        ----------
        v The vector to be rotated
        @return The rotated vector
        """
      
        """ generated source for method rotateVector """
        m2 = self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z
        if m2 == 0:
            raise RuntimeException("Zero quaternion")
        vx = v.getX()
        vy = v.getY()
        vz = v.getZ()
        ax = self._y * vz - self._z * vy
        ay = self._z * vx - self._x * vz
        az = self._x * vy - self._y * vx
        rx = 2 * (self._w * ax + self._y * az - self._z * ay) / m2 + vx
        ry = 2 * (self._w * ay + self._z * ax - self._x * az) / m2 + vy
        rz = 2 * (self._w * az + self._x * ay - self._y * ax) / m2 + vz
        return Vector3(rx, ry, rz)

 
    def rotateAxes(self, v):
        """
             Inverse rotation of a vector.<p>
             This returns <tt>Qinv.[0,V].Q</tt>, where [0,V] is a Quaternion 
             with scalar part 0 and vector part V. It is equivalent to 
             <tt>Q.inverse().rotateVector(v)</tt><p>
             
             If the quaternion Q represents the rotation of frame B with respect to 
             frame A, then <tt>Q.rotateAxes(v)</tt> is passive transformation of 
             a vector from frame A to frame B or an active rotation of a vector in 
             frame B.
             @parameters
        ----------
v The vector to be transformed
             @return The transformed vector
        """
      
        """ generated source for method rotateAxes """
        return self.conjugate().rotateVector(v)

    def rotateI(self):
        """ 
             Return the I vector rotated by this quaternion.<p>
             
             This is the X axis in the rotated frame.
             It is equivalent to rotateVector(new Vector3(1,0,0)).
             
             @return I vector rotated by this quaternion.
        """      

        m2 = self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z
        if m2 == 0:
            raise RuntimeException("Zero quaternion")
        rx = -2 * (self._y * self._y + self._z * self._z) / m2 + 1
        ry = 2 * (self._w * self._z + self._x * self._y) / m2
        rz = 2 * (self._x * self._z - self._w * self._y) / m2
        return Vector3(rx, ry, rz)

    def rotateJ(self):
        """
             Return the J vector rotated by this quaternion.<p>
             
             This is the Y axis in the rotated frame.
             It is equivalent to rotateVector(new Vector3(1,0,0)).
             
             @return J vector rotated by this quaternion.
        """      

        m2 = self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z
        if m2 == 0:
            raise RuntimeException("Zero quaternion")
        rx = 2 * (self._y * self._x - self._w * self._z) / m2
        ry = -2 * (self._z * self._z + self._x * self._x) / m2 + 1
        rz = 2 * (self._w * self._x + self._y * self._z) / m2
        return Vector3(rx, ry, rz)

 
    def rotateK(self):
        """
        Return the K vector rotated by this quaternion.<p>
             
             This is the Z axis in the rotated frame.
             It is equivalent to rotateVector(new Vector3(0,0,1)).
             
             @return K vector rotated by this quaternion.
        """      
        """ generated source for method rotateK """
        m2 = self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z
        if m2 == 0:
            raise RuntimeException("Zero quaternion")
        rx = 2 * (self._w * self._y + self._z * self._x) / m2
        ry = 2 * (self._z * self._y - self._w * self._x) / m2
        rz = -2 * (self._x * self._x + self._y * self._y) / m2 + 1
        return Vector3(rx, ry, rz)

 
    def isNormalized(self, epsilon):
        """
             Test whether the quaternion is normalized.<p>
             The quaternion is considered normalized if the square of its
             norm does not differ from one by more than 2*epsilon.
             @parameters
        ----------
        epsilon Allowed tolerance
        """
      
        """ generated source for method isNormalized """
        sq = self._w * self._w + self._x * self._x + self._y * self._y + self._z * self._z
        return abs(sq - 1) <= epsilon * 2

    def mPower(self, t):
        """ 
             Raise a quaternion to a scalar power, in-place.<p>
             
             This returns a quaternion with unit norm and hence does
             not raise the norm to the exponent.
             @parameters
        ----------
        t The exponent
             @return The resulting quaternion
        """
      
        """ generated source for method mPower """
        theta = t * self.angle() / 2
        v = self.axis()
        s = sin(theta)
        self._w = cos(theta)
        self._x = v.getX() * s
        self._y = v.getY() * s
        self._z = v.getZ() * s
        return self

    def sqrt(self):
        """
        Return the square root of this quaternion.<p>
             
        This method is faster than <tt>mPower(0.5)</tt>.
        It returns the positive sqrt for [0,0,0,1] and throws an exception for [0,0,0,-1].
             
        @throws RuntimeException if this quaternion normalized is [0,0,0,-1].

        """         
      
        """ generated source for method sqrt """
        q = self.normalize()
        q._w += 1
        return q.normalize()

    
    def slerp(self, q, alpha):
        """ 
             Spherical Linear Interpolation (SLERP) between two quaternions.<p>
             Equivalent to <tt>slerp(q, alpha, true)</tt>

             @parameters
        ----------
q The other quaternion
             @parameters
        ----------
alpha The interpolation factor
             @return The interpolated quaternion
        """
      
        """ generated source for method slerp """
        return self.slerp(q, alpha, True)

 
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
             @return The interpolated quaternion
        """
      
        """ generated source for method slerp_0 """
        qb = q.copy()
        #  If angle (in 4D) > 90 degrees, invert one of the quaternions,
        #  to give an acute angle, to rotate in the shortest direction.
        if shortest and self.dot(qb) < 0:
            qb.mMultiply(-1)
        return self.multiply(self.conjugate().mMultiply(qb).mPower(alpha))

    def lerp(self, q, alpha):
        """ generated source for method lerp """
        qb = q.copy()
        if self.dot(qb) < 0:
            qb.mMultiply(-1)
        beta = 1 - alpha
        x = self._x * beta + qb._x * alpha
        y = self._y * beta + qb._y * alpha
        z = self._z * beta + qb._z * alpha
        w = self._w * beta + qb._w * alpha
        return Quaternion(x, y, z, w)


    def mMultiply_0(self, k):
        """ generated source for method mMultiply_0 """
        self._x *= k
        self._y *= k
        self._z *= k
        self._w *= k
        return self

    def mAdd(self, q):
        """ generated source for method mAdd """
        self._x += q._x
        self._y += q._y
        self._z += q._z
        self._w += q._w
        return self

    def mSubtract(self, q):
        """ generated source for method mSubtract """
        self._x -= q._x
        self._y -= q._y
        self._z -= q._z
        self._w -= q._w
        return self




