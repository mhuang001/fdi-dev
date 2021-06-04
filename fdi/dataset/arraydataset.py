# -*- coding: utf-8 -*-

from .datawrapper import DataWrapper
from .typed import Typed
from .listener import ColumnListener
from .ndprint import ndprint
from ..utils.common import mstr, bstr, lls, exprstrs
from .dataset import GenericDataset
try:
    from poperties_NumericParameter import MetaDataProperties
except ImportError:
    class MetaDataProperties():
        pass

from collections.abc import Sequence
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class ArrayDataset(MetaDataProperties, DataWrapper, GenericDataset, Sequence, Typed):
    """  Special dataset that contains a single Array Data object.
    mh: If omit the parameter names during instanciation, e.g. ArrayDataset(a, b, c), the assumed order is data, unit, description.
    mh:  contains a sequence which provides methods count(), index(), remove(), reverse().
    A mutable sequence would also need append(), extend(), insert(), pop() and sort().
    """

    def __init__(self, data=None, unit=None, description='UNKNOWN', typ_=None, default=None, **kwds):
        """ Initializes an ArrayDataset.

        """
        self.setDefault(default)
        super(ArrayDataset, self).__init__(data=data, unit=unit,
                                           description=description, typ_=typ_, **kwds)  # initialize data, meta

    # def getData(self):
    #     """ Optimized """
    #     return self._data

    def setData(self, data):
        """
        """
        isitr = hasattr(data, '__iter__')  # and hasattr(data, '__next__')
        if not isitr and data is not None:
            # dataWrapper initializes data as None
            m = 'data in ArrayDataset must be a subclass of Sequence: ' + \
                data.__class__.__name__
            raise TypeError(m)
        d = None if data is None else \
            data if hasattr(data, '__getitem__') else list(data)
        super(ArrayDataset, self).setData(d)

    @property
    def default(self):
        return self.getDefault()

    @default.setter
    def default(self, default):
        self.setDefault(default)

    def getDefault(self):
        """ Returns the default related to this object."""
        return self._default

    def setDefault(self, default):
        """ Sets the default of this object.

        """
        self._default = default

    def __setitem__(self, *args, **kwargs):
        """ sets value at key.
        """
        self.getData().__setitem__(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        """ returns value at key.
        """
        return self.getData().__getitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        """ removes value and its key.
        """
        self.getData().__delitem__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        """ returns an iterator
        """
        return self.getData().__iter__(*args, **kwargs)

    def pop(self, *args, **kwargs):
        """ revomes and returns value
        """
        return self.getData().pop(*args, **kwargs)

    def append(self, *args, **kwargs):
        """ appends to data.
        """
        return self.getData().append(*args, **kwargs)

    def index(self, *args, **kwargs):
        """ returns the index of a value.
        """
        return self.getData().index(*args, **kwargs)

    def count(self, *args, **kwargs):
        """ returns size.
        """
        return self.getData().count(*args, **kwargs)

    def remove(self, *args, **kwargs):
        """ removes value at first occurrence.
        """
        self.getData().remove(*args, **kwargs)

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 widths=None, matprint=None, trans=True, **kwds):
        """ matprint: an external matrix print function
        trans: print 2D matrix transposed. default is True.
        """
        if matprint is None:
            matprint = ndprint

        cn = self.__class__.__name__
        if level > 1:

            vs, us, ts, ds, fs, gs, cs = exprstrs(self, '_data')
            return cn +\
                '{ %s (%s) <%s>, "%s", default %s, tcode=%s, meta=%s}' %\
                (vs, us, ts, ds, fs, cs, str(self.meta))

        s = '=== %s (%s) ===\n' % (cn, self.description if hasattr(
            self, 'descripion') else '')
        s += mstr(self.__getstate__(), level=level,
                  tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                  excpt=['description'], **kwds)

        d = cn + '-dataset =\n'
        ds = bstr(self.data, level=level, **kwds) if matprint is None else \
            matprint(self.data, trans=False, headers=[], tablefmt2='plain',
                     **kwds)
        d += lls(ds, 2000)
        return s + '\n' + d + '\n'

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        # s = OrderedDict(description=self.description, meta=self.meta, data=self.data)  # super(...).__getstate__()
        s = OrderedDict(description=self.description,
                        meta=self._meta,
                        data=None if self.data is None else self.data,
                        type=self._type,
                        unit=self._unit,
                        default=self._default,
                        typecode=self._typecode,
                        _STID=self._STID)

        return s


class Column(ArrayDataset, ColumnListener):
    """ A Column is a the vertical cut of a table for which all cells have the same signature. It contains raw ArrayData, and optionally a description and unit.
    example::

      table = TableDataset()
      table.addColumn("Energy",Column(data=[1,2,3,4],description="desc",unit='eV'))
    """
