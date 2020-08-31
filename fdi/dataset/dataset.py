# -*- coding: utf-8 -*-
from .ndprint import ndprint
from .listener import ColumnListener, MetaDataListener
from .serializable import Serializable
from .odict import ODict, bstr
from .attributable import Attributable
from .abstractcomposite import AbstractComposite
from .datawrapper import DataWrapper, DataContainer
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable
from .metadata import exprstrs
from .typed import Typed

from collections import OrderedDict
import logging
import sys
if sys.version_info[0] + 0.1 * sys.version_info[1] >= 3.3:
    PY33 = True
    from collections.abc import Container, Sequence, Mapping
    seqlist = Sequence
    maplist = Mapping
else:
    PY33 = False
    from .collectionsMockUp import ContainerMockUp as Container
    from .collectionsMockUp import SequenceMockUp as Sequence
    from .collectionsMockUp import MappingMockUp as Mapping
    seqlist = (tuple, list, Sequence, str)
    # ,types.XRangeType, types.BufferType)
    maplist = (dict, Mapping)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

# from .composite import


class Dataset(Attributable, Annotatable, Copyable, Serializable, DeepEqual, MetaDataListener):
    """ Attributable and annotatable information data container
    that can be be part of a Product.

    developer notes:
    The intent is that developers do not derive from this interface

    directly. Instead, they should inherit from one of the generic
    datasets that this package provides:

    mh: GenericDataset,
    ArrayDataset.
    TableDataset or
    CompositeDataset.
    """

    def __init__(self, **kwds):
        """

        """
        super(Dataset, self).__init__(**kwds)

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def toString(self):
        """
        """

        s = '# ' + self.__class__.__name__ + '\n' +\
            '# description = "%s"\n# meta = %s\n' % \
            (str(self.description), bstr(self.meta))
        return s


class GenericDataset(Dataset, DataContainer, Container):
    """ mh: Contains one data item.
    """

    def __init__(self, **kwds):
        """
        """
        super(GenericDataset, self).__init__(
            **kwds)  # initialize data, meta, unit

    def __iter__(self):
        for x in self.data:
            yield x

    def __contains__(self, x):
        """
        """
        return x in self.data

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ %s, description = "%s", meta = %s }' % \
            (str(self.data), str(self.description), str(self.meta))

    def toString(self, matprint=None, trans=True):
        """ matprint: an external matrix print function
        trans: print 2D matrix transposed. default is True.
        """
        s = '# ' + self.__class__.__name__ + '\n' +\
            '# description = "%s"\n# meta = %s\n# unit = "%s"\n# data = \n\n' % \
            (str(self.description), self.meta.toString(),
             str(self.unit))
        d = bstr(self.data) if matprint is None else matprint(self.data)
        return s + d + '\n'

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # s = OrderedDict(description=self.description, meta=self.meta)  # super(...).serializable()
        # s.update(OrderedDict(data=self.getData()))
        s = OrderedDict(description=self.description,
                        meta=self.meta,
                        data=self.data,
                        classID=self.classID)
        return s


class ArrayDataset(DataWrapper, GenericDataset, Sequence, Typed):
    """  Special dataset that contains a single Array Data object.
    mh: If omit the parameter names during instanciation, e.g. ArrayDataset(a, b, c), the assumed order is data, unit, description.
    mh:  contains a sequence which provides methods count(), index(), remove(), reverse().
    A mutable sequence would also need append(), extend(), insert(), pop() and sort().
    """

    def __init__(self, data=None, unit=None, description='UNKNOWN', typ_=None, default=None, **kwds):
        """
        """
        self.setDefault(default)
        super(ArrayDataset, self).__init__(data=data, unit=unit,
                                           description=description, typ_=typ_, **kwds)  # initialize data, meta

    def setData(self, data):
        """
        """
        if not issubclass(data.__class__, seqlist) and data is not None:
            # dataWrapper initializes data as None
            m = 'data in ArrayDataset must be a subclass of Sequence: ' + \
                data.__class__.__name__
            raise TypeError(m)
        super(ArrayDataset, self).setData(data)

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

    def __len__(self, *args, **kwargs):
        """ size of data
        """
        return self.getData().__len__(*args, **kwargs)

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

    def __repr__(self):
        vs, us, ts, ds, fs, gs, cs = exprstrs(self, '_data')
        return self.__class__.__name__ +\
            '{ %s (%s) <%s>, "%s", dflt %s, tcode=%s, meta=%s}' %\
            (vs, us, ts, ds, fs, cs, str(self.meta))

    def toString(self, matprint=None, trans=True):
        if matprint is None:
            matprint = ndprint
        s = super(ArrayDataset, self).toString(matprint=matprint, trans=trans)

        return s

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # s = OrderedDict(description=self.description, meta=self.meta, data=self.data)  # super(...).serializable()
        s = OrderedDict(description=self.description,
                        meta=self.meta,
                        data=self.data,
                        type=self._type,
                        default=self._default,
                        typecode=self._typecode,
                        classID=self.classID)
        s.update(OrderedDict(unit=self.unit))
        return s


class Column(ArrayDataset, ColumnListener):
    """ A Column is a the vertical cut of a table for which all cells have the same signature. It contains raw ArrayData, and optionally a description and unit.
    example::

      table = TableDataset()
      table.addColumn("Energy",Column(data=[1,2,3,4],description="desc",unit='eV'))
    """
    pass


class TableModel(DataContainer):
    """ to interrogate a tabular data model
    """

    def __init__(self, **kwds):
        """

        """
        super(TableModel, self).__init__(**kwds)

    def getColumnClass(self, columnIndex):
        """ Returns the most specific superclass for all the cell
        values in the column.
        """
        return self.col(columnIndex)[1][0].__class__

    def getColumnCount(self):
        """ Returns the number of columns in the model. """
        return len(self.data)

    def getColumnName(self, columnIndex):
        """ Returns the name of the column at columnIndex. """
        return self.col(columnIndex)[0]

    def getRowCount(self):
        """ Returns the number of rows in the model. """
        return len(self.col(0)[1].data)

    def getValueAt(self, rowIndex, columnIndex):
        """ Returns the value for the cell at columnIndex and rowIndex. """
        return self.col(columnIndex)[1].data[rowIndex]

    def isCellEdidata(self, rowIndex, columnIndex):
        """ Returns true if the cell at rowIndex and columnIndex
        is edidata. """
        return True

    def setValueAt(self, aValue, rowIndex, columnIndex):
        """Sets the value in the cell at columnIndex and rowIndex
        to aValue."""
        self.col(columnIndex)[1].data[rowIndex] = aValue

    def col(self, columIndex):
        """ returns a tuple of (name, column) at the column index.
        """
        return list(self.data.items())[columIndex]


class TableDataset(Dataset, TableModel):
    """  Special dataset that contains a single Array Data object.
    A TableDataset is a tabular collection of Columns. It is optimized to work on array data..
    The column-wise approach is convenient in many cases. For example, one has an event list, and each algorithm is adding a new field to the events (i.e. a new column, for example a quality mask).

    Although mechanisms are provided to grow the table row-wise, one should use these with care especially in performance driven environments as this orthogonal approach (adding rows rather than adding columns) is expensive.

    General Note:

    For reasons of flexibility, memory consumption and performance, this class is not checking whether all columns are of the same length: this is the responsibility of the user/developer. See also the library documentation for more information about this.

    Note on column names:

    If a column is added without specifying a name, the name ColumnX is created, where X denotes the index of that column.
    Column name duplicity is not allowed.

    Developers:

    See "Writing special datasets or products" at the developer's documentation also.


    Please see also this selection example.
    """

    def __init__(self, **kwds):
        """
        """
        super(TableDataset, self).__init__(
            **kwds)  # initialize data, meta, unit

    def setData(self, data):
        """ sets name-column pairs from [{'name':str,'column':Column}]
        or {str:Column} or [[num]] or [(str, [], 'str')]
        form of data, Existing data will be discarded except when the provided data is a list of lists, where existing column names and units will remain but data replaced, and extra data items will form new columns named 'col[index]' (index counting from 1) with unit None.
        """
        # logging.debug(data.__class__)
        # raise Exception()
        if data is not None:
            # d will be {<name1 str>:<column1 Column>, ... }
            d = ODict()
            replace = True
            if issubclass(data.__class__, seqlist):
                try:
                    curd = self.getData()
                except Exception:
                    curd = None
                # list of keys of current data
                curdk = list(self.getData().keys()) if curd else []
                ind = 0
                for x in data:
                    if 'name' in x and 'column' in x:
                        if issubclass(x['column'].__class__, Column):
                            col = x['column']
                        else:
                            col = Column(data=x['column'], unit=x['unit'])
                        d[x['name']] = col
                    elif issubclass(x.__class__, str) and issubclass(data[x].__class__, Column):
                        d[x] = data[x]
                    elif issubclass(x.__class__, list):
                        if curd is None:
                            d['col' + str(ind + 1)] = Column(data=x, unit=None)
                        elif len(curd) <= ind:
                            curd['col' + str(ind + 1)
                                 ] = Column(data=x, unit=None)
                        else:
                            curd[curdk[ind]].data = x
                            replace = False
                    elif issubclass(x.__class__, tuple):
                        if len(x) == 3:
                            d[x[0]] = Column(data=x[1], unit=x[2])
                        else:
                            raise ValueError(
                                'column tuples must be  (str, List), or (str, List, str)')
                    else:
                        raise ValueError(
                            'cannot extract name and column at list member ' + str(x))
                    ind += 1
            elif issubclass(data.__class__, maplist):
                for k, v in data.items():
                    d[k] = v
            else:
                raise TypeError('must be a Sequence or a Mapping. ' +
                                data.__class__.__name__ + ' found.')

            # logging.debug(d)
            if replace:
                super(TableDataset, self).setData(d)
        else:
            super(TableDataset, self).setData(ODict())

    def addColumn(self, name, column):
        """ Adds the specified column to this table, and attaches a name
        to it. If the name is null, a dummy name is created, such that
        it can be accessed by getColumn(str).

        Duplicated column names are not allowed.

        Parameters:
        name - column name.
        column - column to be added.
        """
        idx = self.getColumnCount()
        if name == '' or name is None:
            name = 'column' + str(idx)
        self.data[name] = column

    def removeColumn(self, key):
        """
        """
        if issubclass(key.__class__, str):
            name = key
        else:
            name = self.col(key)[0]
        del(self.data[name])

    def indexOf(self, key):
        """ Returns the index of specified column; if the key is a Column,
        it looks for equal references (same column objects), not for
        equal values.
        If the key is a string, Returns the index of specified Column name.
        mh: Or else returns the key itself.
        """
        if issubclass(key.__class__, str):
            k = list(self.data.keys())
            idx = k.index(key)
        elif issubclass(key.__class__, Column):
            v = list(self.data.values())
            # k,v = zip(*l)
            i = [id(x) for x in v]
            idx = i.index(id(key))
        else:
            idx = key
        return idx

    def addRow(self, row):
        """ Adds the specified map as a new row to this table.
        mh: row is a dict with names as keys
        """
        if len(row) < len(self.data):
            logging.error('row is too short')
            raise Exception('row is too short')
        for c in self.data:
            self.data[c].data.append(row[c])

    def getRow(self, rowIndex):
        """ Returns a list containing the objects located at a particular row.
        """
        return [self.getColumn(x)[rowIndex] for x in self]

    def removeRow(self, rowIndex):
        """ Removes a row with specified index from this table.
        mh: returns removed row.
        """
        return [self.getColumn(x).pop(rowIndex) for x in self]

    @property
    def rowCount(self):
        return self.getRowCount()

    @rowCount.setter
    def rowCount(self, newRowCount):
        self.setRowCount(newRowCount)

    def setRowCount(self, rowCount):
        """ cannot do this.
        """
        raise Exception

    @property
    def columnCount(self):
        return self.getColumnCount()

    @columnCount.setter
    def columnCount(self, newColumnCount):
        self.setColumnCount(newColumnCount)

    def setColumnCount(self, columnCount):
        """ cannot do this.
        """
        raise Exception

    def select(self, selection):
        """ Select a number of rows from this table dataset and
        return a new TableDataset object containing only the selected rows.
        """
        if not issubclass(selection.__class__, list):
            raise ValueError('selection is not a list')
        r = TableDataset()
        for name in self:
            u = self.data[name].unit
            c = Column(unit=u, data=[])
            if len(selection) == 0:
                pass
            elif isinstance(selection[0], int):
                for i in selection:
                    c.data.append(self.data[name][i])
            elif isinstance(selection[0], bool):
                i = 0
                for x in selection:
                    if x:
                        c.data.append(self.data[name][i])
                    i += 1
            else:
                raise ValueError('not bool, int')
            r.addColumn(name, c)
        return r

    def getColumn(self, key):
        """ return colmn if given string as name or int as index.
        returns name if given column.
        """
        idx = self.indexOf(key)
        return idx if issubclass(key.__class__, Column) else self.col(idx)[1]

    def setColumn(self, key, value):
        """ Replaces a column in this table with specified name to specified column if key exists, or else add a new coolumn.
        """
        d = self.getData()
        if key in d:
            d[key] = value
        else:
            self.addColumn(name=key, column=value)

    def __getitem__(self, key):
        """ return colmn if given string as name or int as index.
        returns name if given column.
        """
        return self.getColumn(key)

    def __setitem__(self, key, value):
        """
        """
        self.setColumn(key, value)

    def __iter__(self):
        for x in self.data:
            yield x

    def __contains__(self, x):
        """
        """
        return x in self.data

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", meta = %s, data = "%s"}' % \
            (str(self.description), str(self.meta), str(self.data))

#    def atoString(self):
#        s = '{description = "%s", meta = %s, data = "%s"}' %
#            (str(self.description), self.meta.toString(),
#             self.data.toString())
#        return s

    def toString(self, matprint=None, trans=True):
        if matprint is None:
            matprint = ndprint
        s = super(TableDataset, self).toString()
        cols = list(self.data.values())
        d = '# data = \n\n'
        d += '# ' + ' '.join([str(x) for x in self.data.keys()]) + '\n'
        d += '# ' + ' '.join([str(x.unit) for x in cols]) + '\n'
        d += matprint(cols, trans=trans)
        return s + d + '\n'

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           meta=self.meta,
                           data=self.data,
                           classID=self.classID)


class CompositeDataset(AbstractComposite, Dataset):
    """  An CompositeDataset is a Dataset that contains zero or more
    named Datasets. It allows to build arbitrary complex dataset
    structures.

    It also defines the iteration ordering of its children, which is
    the order in which the children were inserted into this dataset.
    """

    def __init__(self, **kwds):
        """
        """
        super(CompositeDataset, self).__init__(
            **kwds)  # initialize _sets, meta, unit

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           meta=self.meta,
                           _sets=self._sets,
                           classID=self.classID)
