# -*- coding: utf-8 -*-

from .metadata import Parameter
from .typecoded import Typecoded

from .finetime import FineTime, FineTime1, utcobj

from collections import OrderedDict
from copy import copy
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
                 default=None,
                 valid=None,
                 typecode=None,
                 **kwds):
        """
         Set up a parameter whose value is a point in TAI time.

        :value:
        :typecode: time format for the underlying FineTime object
        """

        # collect args-turned-local-variables.
        args = copy(locals())
        args.pop('__class__', None)
        args.pop('kwds', None)
        args.pop('self', None)
        args.update(kwds)

        # 'Q' is unsigned long long (8byte) integer.
        typecode = typecode if typecode else 'Q'
        if typecode == 'Q':
            typecode = FineTime.DEFAULT_FORMAT
        # this will set default then set value.
        super().__init__(
            value=value, description=description, typ_='finetime', default=default, valid=valid, typecode=typecode)
        # Must overwrite the self._all_attrs set by supera()
        self._all_attrs = args

    def setValue(self, value):
        """ accept any type that a FineTime does, with current typecode overriding format of the underlying FineTime
        """
        if value is not None and not issubclass(value.__class__, FineTime):
            # override format with typecode
            if hasattr(self, 'typecode'):
                tc = self.typecode
                t = FineTime(date=value, format=tc)
            else:
                t = FineTime(date=value)
        else:
            t = value
        super().setValue(t)

    def setDefault(self, default):
        """ accept any type that a FineTime does.
        """
        if default is not None and not issubclass(default.__class__, FineTime):
            default = FineTime(date=default)
        super().setDefault(default)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description if hasattr(self, 'description') else '',
                           default=self._default if hasattr(
                               self, '_default') else None,
                           value=self._value if hasattr(
                               self, '_value') else None,
                           valid=self._valid if hasattr(
                               self, '_valid') else None,
                           typecode=self.typecode if hasattr(self, 'typecode') else '')


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
