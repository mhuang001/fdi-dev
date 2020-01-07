# -*- coding: utf-8 -*-
from copy import deepcopy


class Copyable(object):
    """ Interface for objects that can make a copy of themselves. """

    def copy(self):
        """ Makes a deep copy of itself. """
        return deepcopy(self)
