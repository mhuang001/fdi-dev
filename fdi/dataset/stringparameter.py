# -*- coding: utf-8 -*-

from .metadata import Parameter
from .typecoded import Typecoded

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
                 default='',
                 valid=None,
                 typecode='B',
                 **kwds):
        self.setTypecode(typecode)
        super(StringParameter, self).__init__(
            value=value, description=description, typ_='string', default=default, valid=valid, typecode=typecode, **kwds)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            description=self.description,
            default=self._default,
            value=self._value if hasattr(self, '_value') else None,
            valid=self._valid,
            typecode=self._typecode,
            _STID=self._STID)
