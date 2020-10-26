# -*- coding: utf-8 -*-
from collections import OrderedDict, UserDict
from collections.abc import Collection
from .serializable import Serializable
from ..utils.common import bstr
from ..utils.ydump import ydump

from pprint import pformat
import logging
import pdb

logger = logging.getLogger(__name__)

# Depth of nesting of ODict.toString()
OD_toString_Nest = 0


class ODict(UserDict, Serializable):
    """ OrderedDict with a better __repr__.
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

    def __repr1__(self):
        it = [bstr(k, False) + ':' + bstr(v, False)
              for k, v in self.data.items()]
        s = ', '.join(it)
        if len(s) > 70:
            s = ',\n\t'.join(it)
            return 'OD{\n\t' + s + '\t\n}'
        return 'OD{' + s + '}'

    def toString(self, level=0, matprint=None, trans=True, **kwds):
        global OD_toString_Nest

        # return 'OD' + str(type(self.data))+'*'+str(self.data)
        # return 'OD' + str(self.data)
        # return ydump(self.data)

        OD_toString_Nest += 1
        d = ''
        for n, v in self.data.items():
            d += '\n# ' + '    ' * OD_toString_Nest + '[ ' + n + ' ]\n'
            s = bstr(v, level=level, matprint=matprint, trans=trans, **kwds)
            d += s
        OD_toString_Nest -= 1
        return d

    def __repr__(self):
        """ returns string representation with details set according to debuglevel.
        """
        # return 'OD'+super().__repr__()
        level = int(logger.getEffectiveLevel()/10) - 1
        return self.toString(level=level)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return dict(data=self.data,
                    classID=self.classID
                    )
