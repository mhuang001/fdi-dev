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
        self.unit = unit
        super().__init__(**kwds)

    def getUnit(self):
        """ Returns the unit related to this object."""
        return self.unit

    def setUnit(self, unit):
        """ Sets the unit of this object. """
        self.unit = unit
