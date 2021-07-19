# -*- coding: utf-8 -*-

from .metadata import Parameter
from .typecoded import Typecoded

from .finetime import FineTime, FineTime1, utcobj

from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class DateParameter(Parameter, Typecoded):
    """ has a FineTime as the value.
    """

    def __init__(self,
                 value=None,
                 description='UNKNOWN',
                 default=0,
                 valid=None,
                 **kwds):
        """
         Set up a parameter whose value is a point in TAI time.

        """
        # 'Q' is unsigned long long (8byte) integer.
        typecode = 'Q'
        # this will set default then set value.
        super(DateParameter, self).__init__(
            value=value, description=description, typ_='finetime', default=default, valid=valid, typecode=typecode, **kwds)

    def setValue(self, value):
        """ accept any type that a FineTime does.
        """
        if value is not None and not issubclass(value.__class__, FineTime):
            value = FineTime(date=value)
        super().setValue(value)

    def setDefault(self, default):
        """ accept any type that a FineTime does.
        """
        if default is not None and not issubclass(default.__class__, FineTime):
            default = FineTime(date=default)
        super().setDefault(default)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           default=self._default,
                           value=self._value,
                           valid=self._valid,
                           typecode=self.typecode,
                           _STID=self._STID)


class DateParameter1(DateParameter):
    """ Like DateParameter but usese  FineTime1. """

    def setValue(self, value):
        """ accept any type that a FineTime1 does.
        """
        if value is not None and not issubclass(value.__class__, FineTime1):
            value = FineTime1(date=value)
        super().setValue(value)

    def setDefault(self, default):
        """ accept any type that a FineTime1 does.
        """
        if default is not None and not issubclass(default.__class__, FineTime1):
            default = FineTime1(date=default)
        super().setDefault(default)
