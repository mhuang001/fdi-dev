# -*- coding: utf-8 -*-

from .serializable import Serializable
from .eq import DeepEqual, xhash
from ..utils.common import bstr

from collections import OrderedDict, UserDict
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
        Parameters
        ----------

        Returns
        -------
        """

        super().__init__(*args, **kwds)
        self.__missing__ = None
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

    def toString(self, level=0, keyval=None, **kwds):
        """

        Parameters
        ----------
        :level:  default=0,
        :keyval: default=`None`. If set to a string, `ODict` class name is not shown and a label of given string is shown with each key as 'label key:\n'.
        :tablefmt: ='rst', tablefmt1='simple', tablefmt2='simple',
                 matprint=None, trans=True, heavy=True
        Returns
        -------
        """
        global OD_toString_Nest

        # return 'OD' + str(type(self.data))+'*'+str(self.data)
        # return 'OD' + str(self.data)
        # return ydump(self.data)

        OD_toString_Nest += 1
        label = '' if keyval is None else keyval
        d = '' if keyval else '<OD '
        for n, v in self.data.items():
            d += f'{label} "{n}":\n' if level < 2 else ' '
            s = bstr(v, level=level, **kwds)
            d = d + s
        OD_toString_Nest -= 1
        return d + '' if keyval else '>'

    string = toString

    def get(self, name):
        """ Raise a ``KeyError`` to change the default behavior of colections.Mapping to quietly return a None when a key is not found in the dict.
        """

        return self.data[name]
        # res = super().__getitem__(name)
        # if res is not None or name in self.data:
        #     return res
        # msg = '%s is not found in %s.' % (name, self)
        # logger.debug(msg)
        # raise KeyError(msg)

    def __getitem__(self, name):
        """
        For collections.abc.MutableMapping.

        Parameters
        ----------

        Returns
        -------

        """
        return self.data[name]

    def __setitem__(self, name, value):
        """
        For collections.abc.MutableMapping.

        Parameters
        ----------

        Returns
        -------

        """
        self.data[name] = value

    def __delitem__(self, name):
        """
        For collections.abc.MutableMapping.

        Parameters
        ----------

        Returns
        -------

        """
        del self.data[name]

    # def __repr__(self):
    #     """ returns string representation with details set according to debuglevel.
    #     """
    #     # return 'OD'+super().__repr__()
    #     level = int(logger.getEffectiveLevel()/10) - 1
    #     return self.toString(level=level)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder
        Parameters
        ----------

        Returns
        -------

        """
        return OrderedDict(
            **self.data
        )

    def hash(self):

        return xhash(hash_list=self.data.items())
