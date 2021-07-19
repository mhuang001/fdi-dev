# -*- coding: utf-8 -*-

from .metadata import Parameter
from .quantifiable import Quantifiable
from .datatypes import Vector, Vector2D, Quaternion

from collections.abc import Sequence
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


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
        super(NumericParameter, self).__init__(
            value=value, description=description, typ_=typ_, default=default, unit=unit, valid=valid, typecode=typecode, **kwds)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           type=self._type,
                           default=self._default,
                           value=self._value,
                           valid=self._valid,
                           unit=self._unit,
                           typecode=self._typecode,
                           _STID=self._STID)

    def setValue(self, value):
        """ accept any type that a Vector does.
        """
        if value is not None and issubclass(value.__class__, Sequence):
            d = list(value)
            if len(d) == 2:
                value = Vector2D(d)
            elif len(d) == 3:
                value = Vector(d)
            elif len(d) == 4:
                value = Quaternion(d)
            else:
                raise ValueError(
                    'Sequence of only 2 to 4 elements for NumericParameter')
        super().setValue(value)

    def setDefault(self, default):
        """ accept any type that a Vector does.
        """
        if default is not None and issubclass(default.__class__, Sequence):
            d = list(default)
            if len(d) == 2:
                default = Vector2D(d)
            elif len(d) == 3:
                default = Vector(d)
            elif len(d) == 4:
                default = Quaternion(d)
            else:
                raise ValueError(
                    'Sequence of only 2 to 4 elements for NumericParameter')
        super().setDefault(default)
