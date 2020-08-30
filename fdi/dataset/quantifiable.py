# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Quantifiable(object):
    """ A Quantifiable object is a numeric object that has a unit.
    $ x.unit = ELECTRON_VOLTS
    $ print x.unit
    eV [1.60218E-19 J]"""

    def __init__(self, unit=None, typecode=None, **kwds):
        """ Has a unit and a typecode (as in array.array.typecodes).

        """
        self.setUnit(unit)
        self.setTypecode(typecode)
        #print(__name__ + str(kwds))
        super(Quantifiable, self).__init__(**kwds)

    @property
    def unit(self):
        return self.getUnit()

    @unit.setter
    def unit(self, unit):
        self.setUnit(unit)

    def getUnit(self):
        """ Returns the unit related to this object."""
        return self._unit

    def setUnit(self, unit):
        """ Sets the unit of this object. """
        self._unit = unit

    @property
    def typecode(self):
        return self.getTypecode()

    @typecode.setter
    def typecode(self, typecode):
        self.setTypecode(typecode)

    def getTypecode(self):
        """ Returns the typecode related to this object."""
        return self._typecode

    def setTypecode(self, typecode):
        """ Sets the typecode of this object. """
        self._typecode = typecode
