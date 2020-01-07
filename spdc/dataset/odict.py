# -*- coding: utf-8 -*-
from collections import OrderedDict
#from .serializable import Serializable
import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False


def bstr(x, tostr=True, quote="'", **kwds):
    """ returns the best string representation. 
    if the object is a string, return single-quoted; if has toString(), use it; else returns str().
    """

    s = issubclass(x.__class__, str) if PY3 else issubclass(
        x.__class__, (str, unicode))

    if s:
        r = quote + x + quote
    elif tostr and hasattr(x, 'toString'):
        r = x.toString(**kwds)
    else:
        r = str(x)
    return r


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
