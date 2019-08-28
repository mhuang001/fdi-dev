# -*- coding: utf-8 -*-
from collections import OrderedDict
#from .serializable import Serializable


def bstr(x, tostr=True, quote="'", **kwds):
    """ returns the best string representation. if the object is a string, return single-quoted; if has toString(), use it; else returns str().
    """
    return quote + x + quote if issubclass(x.__class__, str) else x.toString(**kwds) if tostr and hasattr(x, 'toString') else str(x)


class ODict(OrderedDict):
    """ OrderedDict with a better __repre__.
    """

    def __repr__(self):

        s = ''.join([bstr(k, False) + ':' + bstr(v, False) +
                     ', ' for k, v in self.items()])
        return 'OD{' + s[:-2] + '}'

    def toString(self, matprint=None, trans=True):
        d = ''
        for n, v in self.items():
            d += '\n# [ ' + n + ' ]\n'
            d += bstr(v, matprint=matprint, trans=trans)

        return d
