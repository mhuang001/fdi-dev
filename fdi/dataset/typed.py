# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Typed(object):
    """ An object of specifiable kinds. """

    def __init__(self, typ_=None, **kwds):
        """ Has a type.

        """

        self.setType(typ_)
        #print(__name__ + str(kwds))
        super(Typed, self).__init__(**kwds)

    @property
    def type(self):
        """ for property getter
        """
        return self.getType()

    @type.setter
    def type(self, typ_):
        """ Must be in ParameterTypes.
        """
        self.setType(typ_)

    def getType(self):
        """ Returns the actual type that is allowed for the value
        of this Parameter."""
        return self._type

    def setType(self, typ_):
        """ Replaces the current type of this parameter.

        """
        self._type = typ_
