# -*- coding: utf-8 -*-

from .typecoded import Typecoded

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Quantifiable(Typecoded):
    """ A Quantifiable object is a numeric object that has a unit.
    $ x.unit = ELECTRON_VOLTS
    $ print x.unit
    eV [1.60218E-19 J]"""

    def __init__(self, unit=None, typecode=None, **kwds):
        """ Has a unit and a typecode (as in array.array.typecodes).

        Parameters
        ---------

        Returns
        -------

        """
        #print(__name__ + str(kwds))
        super(Quantifiable, self).__init__(typecode=typecode, **kwds)
        self.setUnit(unit)

    @property
    def unit(self):
        """
        Parameters
        ----------

        Returns
        -------

        """
        return self.getUnit()

    @unit.setter
    def unit(self, unit):
        """
        Parameters
        ----------

        Returns
        -------

        """
        self.setUnit(unit)

    def getUnit(self):
        """ Returns the unit related to this object.

        Parameters
        ----------

        Returns
        -------
        """
        return self._unit

    def setUnit(self, unit):
        """ Sets the unit of this object. 

        Parameters
        ----------

        Returns
        -------
        """
        self._unit = unit
