# -*- coding: utf-8 -*-

from .metadata import Parameter
from .typecoded import Typecoded

from collections import OrderedDict
from itertools import filterfalse
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
                 default='',
                 valid=None,
                 typecode='B',
                 **kwds):

        typ_ = kwds.pop('typ_', 'string')
        # collect args-turned-local-variables.
        args = OrderedDict(filterfalse(
            lambda x: x[0] in ('self', '__class__', 'kwds'),
            locals().items())
        )
        args.update(kwds)

        self.setTypecode(typecode)
        super().__init__(
            value=value, description=description, typ_=typ_, default=default, valid=valid, typecode=typecode)
        # Must overwrite the self._all_attrs set by supera()
        self._all_attrs = args

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            description=self.description,
            default=self._default,
            value=self._value if hasattr(self, '_value') else None,
            valid=self._valid,
            typecode=self._typecode)
