# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Typecoded():
    """ Has internal store type specified as TypeCode. ref doc of `drray.Array`.

    """

    def __init__(self, typecode=None, **kwds):
        """ Has a typecode.

        Typecode is defined in `array.array`
        """

        self.setTypecode(typecode)
        #print(__name__ + str(kwds))
        super().__init__(**kwds)

    @ property
    def typecode(self):
        return self.getTypecode()

    @ typecode.setter
    def typecode(self, typecode):
        self.setTypecode(typecode)

    def getTypecode(self):
        """ Returns the typecode related to this object."""
        return self._typecode

    def setTypecode(self, typecode):
        """ Sets the typecode of this object. """
        self._typecode = typecode
