# -*- coding: utf-8 -*-
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class Copyable():
    """ Interface for objects that can make a copy of themselves. """

    def __init__(self, **kwds):
        """

        Parameters
        ----------

        Returns
        -------
        """

        super().__init__(**kwds)

    def copy(self):
        """ Makes a deep copy of itself.
        Parameters
        ----------

        Returns
        -------
        """
        return deepcopy(self)
