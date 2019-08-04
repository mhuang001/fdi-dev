# -*- coding: utf-8 -*-
from copy import deepcopy


class Copyable():
    """ Interface for objects that can make a copy of themselves. """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def copy(self):
        """ Makes a deep copy of itself. """
        return deepcopy(self)
