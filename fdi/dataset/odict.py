# -*- coding: utf-8 -*-
from collections import OrderedDict, UserDict
from collections.abc import Collection
from .serializable import Serializable
import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False


def bstr(x, tostr=True, quote="'", level=0, **kwds):
    """ returns the best string representation.
    if the object is a string, return single-quoted; if has toString(), use it; else returns str().
    """

    s = issubclass(x.__class__, str) if PY3 else issubclass(
        x.__class__, (str, unicode))

    if s:
        r = quote + x + quote
    elif tostr and hasattr(x, 'toString'):
        r = x.toString(level=level, **kwds)
    else:
        r = str(x)
    return r


class ODict(UserDict, Serializable):
    """ OrderedDict with a better __repre__.
    """

    def __init__(self, *args, **kwds):
        """

        """
        # print(args)
        #data = OrderedDict(*args, **kwds)
        super().__init__(*args, **kwds)
        #UserDict.__init__(self, data)
        Serializable.__init__(self)

    # @property
    # def listoflists(self):
    #     return self.getListoflists()

    # @listoflists.setter
    # def listoflists(self, value):
    #     self.setListoflists(value)

    # def getListoflists(self):
    #     """ Returns a list of lists of key-value pairs where if the key is a tuple or frozenset, it is converted to a list.
    #     """
    #     ret = []
    #     for k, v in self.items():
    #         if issubclass(k.__class__, str):
    #             kk = k
    #         else:
    #             kk = list(k) if issubclass(k.__class__, (Collection)) else k
    #         ret.append([kk, v])
    #     return ret

    # def setListoflists(self, value):
    #     """ Sets the listoflists of this object. """
    #     def c2t(c):
    #         print(c)

    #         lst = [c2t(x) if issubclass(x.__class__, list) else x for x in c]
    #         print('== ', lst)
    #         return tuple(lst)
    #     d = dict(c2t(x) for x in value)
    #     self.clear()
    #     self.update(d)
    #     if 0:
    #         for item in value:
    #             kk = tuple(item[0])
    #             self[kk] = item[1]

    def __repr__(self):
        it = [bstr(k, False) + ':' + bstr(v, False)
              for k, v in self.items()]
        s = ', '.join(it)
        if len(s) > 70:
            s = ',\n\t'.join(it)
            return 'OD{\n\t' + s + '\t\n}'
        return 'OD{' + s + '}'

    def toString(self, matprint=None, trans=True, level=0):
        d = ''
        for n, v in self.items():
            d += '\n# [ ' + n + ' ]\n'
            d += bstr(v, matprint=matprint, trans=trans, level=level)

        return d

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return dict(data=self.data,
                    classID=self.classID
                    )
