# -*- coding: utf-8 -*-

from .metadata import Parameter
from .quantifiable import Quantifiable
from .datatypes import Vector, Vector2D, Vector3D, Quaternion

from collections.abc import Sequence
from collections import OrderedDict
from copy import copy
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class NumericParameter(Parameter, Quantifiable):
    """ A Parameter that has a number as the value, a unit, and a typecode.
    """

    def __init__(self,
                 value=None,
                 description='UNKNOWN',
                 typ_='',
                 default=None,
                 unit=None,
                 valid=None,
                 typecode=None,
                 **kwds):
        """ Set up a parameter whose value is a or a list of numbers.

        typ_: type of the parameter value.
        """

        # collect args-turned-local-variables.
        args = copy(locals())
        args.pop('__class__', None)
        args.pop('kwds', None)
        args.pop('self', None)
        args.update(kwds)

        super().__init__(
            value=value, description=description, typ_=typ_, default=default, unit=unit, valid=valid, typecode=typecode)
        # Must overwrite the self._all_attrs set by supera()
        self._all_attrs = args

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           type=self._type,
                           default=self._default,
                           value=self._value,
                           valid=self._valid,
                           unit=self._unit,
                           typecode=self._typecode)

    def setValue(self, value):
        """ accept any type that a Vector does.
        """
        if value is not None and issubclass(value.__class__, Sequence):
            if self.type in ('vector', 'vector2d', 'vector3d', 'quaternion'):
                d = list(value)
                len_d = len(d)
                if len_d == 2:
                    value = Vector2D(d)
                elif len_d == 3:
                    value = Vector3D(d)
                elif len_d == 4 and getattr(self, '_type', None) == 'quaternion':
                    value = Quaternion(d)
                else:
                    value = Vector(d)
        super().setValue(value)

    def setDefault(self, default):
        """ accept any type that a Vector does.

        'Accept sequence of only 0 to 4 elements for NumericParameter and Vectors.')

        """
        if default is not None and issubclass(default.__class__, Sequence):
            # MUST NOT depend on self.type being existing
            if getattr(self, '_type', None) in ('vector', 'vector2d', 'vector3d', 'quaternion'):
                d = list(default)
                len_d = len(d)
                if len_d == 2:
                    default = Vector2D(d)
                elif len_d == 3:
                    default = Vector3D(d)
                elif len_d == 4 and getattr(self, '_type', None) == 'quaternion':
                    default = Quaternion(d)
                else:
                    pass
                    # raise ValueError(
                    #        'Sequence of only 0 to 4 elements for NumericParameter and Vectors.')
        super().setDefault(default)


class BooleanParameter(Parameter):
    """ A Parameter that has a boolean as the value.
    """

    def __init__(self,
                 value=None,
                 description='UNKNOWN',
                 default=None,
                 valid=None,
                 **kwds):
        """ Set up a parameter whose value is a boolean

        """

        typ_ = kwds.pop('typ_', 'boolean')
        # collect args-turned-local-variables.
        args = copy(locals())
        args.pop('__class__', None)
        args.pop('kwds', None)
        args.pop('self', None)
        args.update(kwds)

        super().__init__(
            value=value, description=description, typ_=typ_, default=default, valid=valid)
        # Must overwrite the self._all_attrs set by supera()
        self._all_attrs = args

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           type=getattr(self, '_type', ''),
                           default=getattr(self, '_default', ''),
                           value=getattr(self, '_value', ''),
                           valid=getattr(self, '_valid', ''),)

    def setValue(self, value):
        """ accept any type that `bool` does.
        """
        b = None if value is None else bool(value)
        super().setValue(b)

    def setDefault(self, default):
        """ accept any type that `bool` Vector does.
        """
        b = None if default is None else bool(default)
        super().setDefault(b)
