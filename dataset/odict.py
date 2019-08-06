# -*- coding: utf-8 -*-
from collections import OrderedDict
#from .serializable import Serializable


class ODict(OrderedDict):
    """ OrderedDict with a better __repre__.
    """

    def __repr__(self):

        def q(x):
            return "'" + x + "'" if issubclass(x.__class__, str) else str(x)
        s = ''.join([q(k) + ':' + q(v) + ', ' for k, v in self.items()])
        return 'OD{' + s[:-2] + '}'

    def toString(self):
        return self.__repr__()
