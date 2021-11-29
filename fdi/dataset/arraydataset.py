# -*- coding: utf-8 -*-

from .datawrapper import DataWrapper
from .typed import Typed
from .typecoded import Typecoded
from .listener import ColumnListener
from .ndprint import ndprint
from .shaped import Shaped
from ..utils.common import mstr, bstr, lls, exprstrs, findShape
from .dataset import GenericDataset, make_title_meta_l0
try:
    from .arraydataset_datamodel import Model
except ImportError:
    Model = {'metadata': {}}


from collections.abc import Sequence, Iterable
from collections import OrderedDict
import itertools

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

MdpInfo = Model['metadata']


class ArrayDataset(GenericDataset, Iterable, Shaped):
    """  Special dataset that contains a single Array Data object.

    mh: If omit the parameter names during instanciation, e.g. ArrayDataset(a, b, c), the assumed order is data, unit, description.
    mh:  contains a sequence which provides methods count(), index(), remove(), reverse().
    A mutable sequence would also need append(), extend(), insert(), pop() and sort().

        Parameters
        ----------
    :data: the payload data of this dataset. Default is None,
        Returns
        -------
    """

    def __init__(self, data=None,
                 unit=None,
                 description=None,
                 typ_=None,
                 typecode=None,
                 version=None,
                 zInfo=None,
                 alwaysMeta=True,
                 ** kwds):
        """ Initializes an ArrayDataset.

        Default ```None``` will initialize MetaData Parameters to their default values.
        If ``data`` is not None and has shape (``len`` applies), ``shape`` MDP is set to the actual ``data`` shape. 
        """

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__',
                                   'zInfo', 'kwds'),
                locals().items())
        )

        global Model
        if zInfo is None:
            zInfo = Model

        # print('@1 zInfo', id(self.zInfo['metadata']), id(self), id(self.zInfo),
        #      self.zInfo['metadata']['version'], list(metasToBeInstalled.keys()))
        # must be the first line to initiate meta
        super().__init__(zInfo=zInfo, **metasToBeInstalled, **kwds)

    # def getData(self):
    #     """ Optimized """
    #     return self._data

    def setData(self, data):
        """
        """
        isitr = hasattr(data, '__iter__')  # and hasattr(data, '__next__')
        if not isitr and data is not None:
            # dataWrapper initializes data as None
            m = 'data in ArrayDataset must be an iterator, not ' + \
                data.__class__.__name__
            raise TypeError(m)
        d = None if data is None else \
            data if hasattr(data, '__getitem__') else list(data)
        # no passive shape-updating. no
        super(ArrayDataset, self).setData(d)
        self.updateShape()

    def __setitem__(self, *args, **kwargs):
        """ sets value at key.
        """
        self.getData().__setitem__(*args, **kwargs)
        self.updateShape()

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
        ret = self.getData().pop(*args, **kwargs)
        self.updateShape()
        return ret

    def append(self, *args, **kwargs):
        """ appends to data.
        """
        self.getData().append(*args, **kwargs)
        self.updateShape()

    def extend(self, *args, **kwargs):
        """ extend data.
        """
        self.getData().extend(*args, **kwargs)
        self.updateShape()

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
        self.updateShape()

    def __repr__(self):
        return self.toString(level=2)

    def toString(self, level=0,
                 tablefmt='grid', tablefmt1='simple', tablefmt2='simple',
                 width=0, param_widths=None, matprint=None, trans=True,
                 center=-1, heavy=True, **kwds):
        """ matprint: an external matrix print function
        trans: print 2D matrix transposed. default is True.
        """
        if matprint is None:
            matprint = ndprint

        cn = self.__class__.__name__
        if level > 1:

            s = cn + '(' + \
                self.meta.toString(
                    level=level, heavy=heavy,
                    tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                    width=width, param_widths=param_widths,
                    **kwds)
            # set wiidth=0 level=2 to inhibit \n
            vs, us, ts, ds, fs, gs, cs, ex = exprstrs(
                self, '_data', width=0, level=level)
            # '{ %s (%s) <%s>, "%s", default %s, tcode=%s}' %\
            # (vs, us, ts, ds, fs, cs)
            return '%s data= %s)' % (s, vs)

        s, last = make_title_meta_l0(self, level=level, width=width, heavy=heavy,
                                     tablefmt=tablefmt, tablefmt1=tablefmt1,
                                     tablefmt2=tablefmt2, center=center,
                                     excpt=['description'])
        width = len(last)-1
        if level == 0:
            d = 'DATA'.center(width) + '\n' + '----'.center(width) + '\n'
        else:
            d = ''

        ds = bstr(self.data, level=level, **kwds) if matprint is None else \
            matprint(self.data, trans=False, headers=[], tablefmt2='plain',
                     **kwds)
        d += lls(ds, 1000)
        return f'{s}\n{d}\n{last}\n'

    string = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """

        # s = OrderedDict(description=self.description, meta=self.meta, data=self.data)  # super(...).__getstate__()
        s = OrderedDict(
            _ATTR_meta=getattr(self, '_meta', None),
            _ATTR_data=getattr(self, 'data', None))

        return s
        # type=self.type,
        # unit=self.unit,
        # typecode=self.typecode,
        # version=self.version,
        # FORMATV=self.FORMATV,


class Column(ArrayDataset, ColumnListener):
    """ A Column is a the vertical cut of a table for which all cells have the same signature.

    A Column contains raw ArrayData, and optionally a description and unit.
    example::

      table = TableDataset()
      table.addColumn("Energy",Column(data=[1,2,3,4],description="desc",unit='eV'))
    """

    def __init__(self,  *args, typ_='Column', **kwds):
        super().__init__(*args, typ_=typ_, **kwds)
