# -*- coding: utf-8 -*-
from collections import OrderedDict, UserDict
from collections.abc import Collection
from .serializable import Serializable
from .eq import DeepEqual, xhash
from ..utils.common import bstr
from ..utils.ydump import ydump

from pprint import pformat
import logging

logger = logging.getLogger(__name__)

# Depth of nesting of ODict.toString()
OD_toString_Nest = 0


class ODict(UserDict, Serializable, DeepEqual):
    """ Ordered dict that is not a subclass of dict and with a better __str__.
    """

    def __init__(self, *args, **kwds):
        """

        """
        # print(args)
        # data = OrderedDict(*args, **kwds)
        super().__init__(*args, **kwds)
        # UserDict.__init__(self, data)
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

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 matprint=None, trans=True, **kwds):
        global OD_toString_Nest

        # return 'OD' + str(type(self.data))+'*'+str(self.data)
        # return 'OD' + str(self.data)
        # return ydump(self.data)

        OD_toString_Nest += 1
        d = '<ODict '
        for n, v in self.data.items():
            #d += '    ' * OD_toString_Nest + '[ ' + str(n) + ' ]= '
            d += '"' + str(n) + '":' + '\n' if level == 0 else ' '
            s = bstr(v, level=level,
                     tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                     matprint=matprint, trans=trans, **kwds)
            d = d + s
        OD_toString_Nest -= 1
        return d + '>'

    # def __repr__(self):
    #     """ returns string representation with details set according to debuglevel.
    #     """
    #     # return 'OD'+super().__repr__()
    #     level = int(logger.getEffectiveLevel()/10) - 1
    #     return self.toString(level=level)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            data=self.data,
            _STID=self._STID
        )

    def serializable(self):
        """ Can be encoded with serializableEncoder """

        return OrderedDict(
            **self.data,
            _STID=self._STID
        )

    def hash(self):

        return xhash(hash_list=self.data.items())
