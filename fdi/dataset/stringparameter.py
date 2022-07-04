# -*- coding: utf-8 -*-

from .metadata import Parameter
from .typecoded import Typecoded

from copy import copy
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class StringParameter(Parameter, Typecoded):
    """ has a unicode string as the value, a typecode for length and char.
    """

    def __init__(self,
                 value=None,
                 description='UNKNOWN',
                 default=None,
                 valid=None,
                 typecode='B',
                 **kwds):

        typ_ = kwds.pop('typ_', 'string')
        # collect args-turned-local-variables.
        args = copy(locals())
        args.pop('__class__', None)
        args.pop('kwds', None)
        args.pop('self', None)
        args.update(kwds)

        self.setTypecode(typecode)
        super().__init__(
            value=value, description=description, typ_=typ_, default=default, valid=valid, typecode=typecode)
        # Must overwrite the self._all_attrs set by supera()
        self._all_attrs = args

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            description=self.description if hasattr(
                self, 'description') else '',
            default=self._default,
            value=self._value if hasattr(self, '_value') else None,
            valid=self._valid,
            typecode=self._typecode)
