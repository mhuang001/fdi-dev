# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Quantifiable():
    """ A Quantifiable object is a numeric object that has a unit.
    $ x.unit = ELECTRON_VOLTS
    $ print x.unit
    eV [1.60218E-19 J]"""

    def __init__(self, unit=None, **kwds):
        """

        """
        self.setUnit(unit)
        super().__init__(**kwds)

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
