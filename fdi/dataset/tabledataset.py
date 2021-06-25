# -*- coding: utf-8 -*-

from .indexed import Indexed
from .ndprint import ndprint
from .odict import ODict
from ..utils.common import mstr, bstr, lls, exprstrs
from .dataset import Dataset
from .indexed import Indexed

try:
    from .tabledataset_datamodel import Model
except ImportError:
    Model = {'metadata': {}}


import sys
from collections.abc import Sequence
from collections import OrderedDict
import itertools

if sys.version_info[0] + 0.1 * sys.version_info[1] >= 3.3:
    PY33 = True
    from collections.abc import Container, Sequence, Mapping
    seqlist = Sequence
    maplist = Mapping
else:
    assert 0, 'python 3'
    PY33 = False
    from .collectionsMockUp import ContainerMockUp as Container
    from .collectionsMockUp import SequenceMockUp as Sequence
    from .collectionsMockUp import MappingMockUp as Mapping
    seqlist = (tuple, list, Sequence, str)
    # ,types.XRangeType, types.BufferType)
    maplist = (dict, Mapping)

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class TableModel(object):
    """ to interrogate a tabular data model
    """

    def __init__(self, **kwds):
        """

        """
        super(TableModel, self).__init__(**kwds)

    def getColumnClass(self, columnIndex):
        """ Returns the class for the first cell
        values in the column.
        """
        return self.getColumn(columnIndex)[0].__class__

    def getColumnCount(self):
        """ Returns the number of columns in the model. """
        return len(self.getData())

    def getColumnName(self, columnIndex):
        """ Returns the name of the column at columnIndex.

        returns a set of columns if key  is a slice.
        """

        return self.getColumnNames()[columnIndex]

    def getColumnNames(self):
        """ Returns the column names. """
        return list(self.getData().keys())

    def getRowCount(self):
        """ Returns the number of rows in the model. """
        return len(self.getColumn(0))

    def getValueAt(self, rowIndex, columnIndex):
        """ Returns the value for the cell at columnIndex and rowIndex. """
        return self.getColumn(columnIndex).data[rowIndex]

    def isCellEditable(self, rowIndex, columnIndex):
        """ Returns true if the cell at rowIndex and columnIndex
        is editable. """
        return True

    def setValueAt(self, value, rowIndex, columnIndex):
        """Sets the value in the cell at columnIndex and rowIndex
        to Value.
        """
        self.getColumn(columnIndex).data[rowIndex] = value


MdpInfo = Model['metadata']


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

    def __init__(self, data=None,
                 zInfo=None,
                 alwaysMeta=True,
                 **kwds):
        """
        """

        self._list = []

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__', 'zInfo', 'kwds'),
                locals().items())
        )

        global Model
        if zInfo is None:
            zInfo = Model

        super().__init__(zInfo=zInfo, **metasToBeInstalled,
                         **kwds)  # initialize data, meta, unit
        # self.setData(data)

    def getData(self):
        """ Optimized for _data being an ``ODict`` implemented with ``UserDict``.

        """

        try:
            return self._data.data
        except AttributeError:
            d = super().getData()
            if hasattr(d, 'data'):
                return self._data.data
            else:
                return d

    def setData(self, data):
        """ sets name-column pairs from data.

        Valid formd include: {str:Column, ...} or [(str, [num, ...], str)]
        or [(str, Column), ...] or [[num ...],  [num ...], ...]

        [{'name':str,'column':Column}] form is deprecated.

        Existing data will be discarded except when the provided data is a list of lists, where existing column names and units will remain but data replaced, and extra data items will form new columns named 'column'+index (index counting from 1) with unit None.
        """
        # logging.debug(data.__class__)

        if data is None:
            super(TableDataset, self).setData(ODict())
            return

        current_data = self.getData()
        # list of keys of current data
        curdk = list(current_data.keys()) if current_data else []
        super(TableDataset, self).setData(ODict())
        if issubclass(data.__class__, seqlist):
            from .arraydataset import Column
            for ind, x in enumerate(data):
                if issubclass(x.__class__, maplist) \
                   and 'name' in x and 'column' in x:
                    raise DeprecationWarning(
                        'Do not use [{"name":name, "column":column}...]. Use {name:column, ...} instead.')
                if issubclass(x.__class__, (list, tuple)):
                    # check out string-started columns
                    if len(x) > 1 and issubclass(x[0].__class__, str) and not issubclass(x[1].__class__, str):
                        if issubclass(x[1].__class__, (list, tuple)):
                            u = x[2] if len(x) > 2 else ''
                            self.setColumn(x[0], Column(data=x[1], unit=x[2]))
                        elif issubclass(x[1].__class__, Column):
                            self.setColumn(x[0], x[1])
                        else:
                            raise '[[str, [], str]...], [[str, []]...], [[str, Column]...] needed.'
                    else:
                        if current_data is None or len(current_data) <= ind:
                            # update the data of the ind-th column
                            self.setColumn('', Column(data=x, unit=None))
                        else:
                            colname = curdk[ind]
                            current_data[colname].data = x
                            self.setColumn(colname, current_data[colname])
                else:
                    raise ValueError(
                        'Cannot extract name and column from list member ' + str(x))
        elif issubclass(data.__class__, maplist):
            for k, v in data.items():
                self.setColumn(k, v)
        else:
            raise TypeError('must be a Sequence or a Mapping. ' +
                            data.__class__.__name__ + ' found.')

    def addColumn(self, name, column, col_des=False):
        """ Adds the specified column to this table, and attaches a name
        to it. If the name is null, a dummy name "column"+column_count+1 is created, such that it can be accessed by getColumn(str).

        If column name exists the corresponding column is substituted.

        Parameters:
        name - column name.
        column - column to be added.
        col_des - if True (default) and column descripion is 'UNKNOWN', set to column name.
        """

        d = self.getData()
        if d is None:
            d = ODict()

        if name == '' or name is None:
            idx = self.getColumnCount()
            name = 'column' + str(idx+1)
            self._list.append(column.getData())
        else:
            try:
                self._list[self.indexOf(name)] = column.getData()
            except ValueError as e:
                self._list.append(column.getData())
        if col_des and column.getDescription() == 'UNKNOWN':
            column.setDescription(name)
        d[name] = column

    def removeColumn(self, key):
        """ Removes the columns specified by ``key``.

        ref. ``getColumnMap`` on ``key`` usage.
        """

        for name in self.getColumnMap(key).keys():
            self._list.pop(self.indexOf(name))
            del(self.data[name])

    def indexOf(self, key):
        """ Returns the index of specified column.

        if the key is a Column,
        it looks for equal references (same column objects), not for
        equal values.
        If the key is a string, Returns the index of specified Column name.
        """
        from .arraydataset import Column
        if issubclass(key.__class__, str):
            ks = list(self.getData().keys())
            k = key
        elif issubclass(key.__class__, Column):
            ks = list(id(v) for v in self.getData().values())
            k = id(key)
        else:
            raise "key must be string or Column, not %s." % type(key).__name__

        return ks.index(k)

    def addRow(self, row, rows=False):
        """ Adds the specified map as a new row to this table.

        row: mh: row is a dict with names as keys and row data as value.
        rows: append each element in row if the row data is a list.
        """

        d = self.getData()
        if len(row) < len(d):
            msg = 'row width d% should be %d.' % (len(row), len(d))
            raise ValueError(msg)

        for c in d.keys():
            if rows:
                d[c].data.extend(row[c])
            else:
                d[c].data.append(row[c])

    def getRowMap(self, rowIndex):
        """ Returns a dict of column-names as the keys and the objects located at a particular row(s) as the values.

        rowIndex: return the following as the value for each key-value pair:
* int: the int-th row's elements;
* ``Slice`` object, a list of rows from slicing the column. Example ``a.getRow(Slice(3,,))``;
* list of integers: they are used as the row index to select the rows.
* list of booleans: rows where the corresponding boolean is True are chosen.
        """
        cl = rowIndex.__class__
        d = self.getData()
        if issubclass(cl, (int, slice)):
            return {n: c.getData()[rowIndex] for n, c in d.items()}
        if issubclass(cl, list):
            if type(rowIndex[0]) == int:
                return {n: [c.getData()[i] for i in rowIndex] for n, c in d.items()}
            if type(rowIndex[0]) == bool:
                # if len(rowIndex) != len(n):
                # logger.info('%s Selection length %d should be %d.' %
                #        (name, len(rowIndex), len(n)))
                return {n: [x for x, s in zip(c.getData(), rowIndex) if s] for n, c in d.items()}
        else:
            raise ValueError(
                'RowIndex must be an int, a slice, or a list of ints or bools.')

    def getRow(self, rowIndex):
        """ Returns a list containing the objects located in a particular row, or a list of rows.

        rowIndex: ref ``getRowMap()``
* int: return the int-th row in a list of elements;
* ``Slice`` object, list of integers, list of booleans: return a list of rows each represented by a tuple. Example ``a.getRow(Slice(3,,))``, ``[2,4]``, ``[True, False...]``.
        """

        it = self.getRowMap(rowIndex).values()
        if issubclass(rowIndex.__class__, int):
            # return a list of row elements
            return list(it)
        # return transposed in a list
        return list(zip(*it))

    def select(self, selection):
        """ Select a number of rows from this table dataset and
        return a new TableDataset object containing only the selected rows.

        selection:  to form a new Tabledataset with ref ``getRowMap()``
        """

        d = ODict()
        if issubclass(selection.__class__, int):
            for name, data in self.getRowMap(selection).items():
                d[name] = Column(
                    data=[data], unit=self.getColumn(name).getUnit())
                return TableDataset(data=d)

        from .arraydataset import Column
        for name, data in self.getRowMap(selection).items():
            d[name] = Column(data=data, unit=self.getColumn(name).getUnit())
        return TableDataset(data=d)

    def removeRow(self, rowIndex):
        """ Removes a row with specified index from this table.

        rowIndex: int or a ``Slice`` object. Example ``a.removeRow(Slice(3,,))``.
        return: removed row data.
        """
        if issubclass(rowIndex.__class__, slice):
            ret = []
            for x in self.getData().values():
                ret.append(x.data[rowIndex])
                del x.data[rowIndex]
            return ret

        return [x.data.pop(rowIndex) for x in self.getData().values()]

    @ property
    def rowCount(self):
        return self.getRowCount()

    @ rowCount.setter
    def rowCount(self, newRowCount):
        self.setRowCount(newRowCount)

    def setRowCount(self, rowCount):
        """ cannot do this.
        """
        raise ValueError('Cannot set row count.')

    @ property
    def columnCount(self):
        return self.getColumnCount()

    @ columnCount.setter
    def columnCount(self, newColumnCount):
        self.setColumnCount(newColumnCount)

    def setColumnCount(self, columnCount):
        """ cannot do this.
        """
        raise ValueError('Cannot set column count.')

    @ property
    def list(self):
        return self._list

    @ list.setter
    def list(self, l):
        raise NotImplemented

    def getColumnMap(self, key=None):
        """ Returns a dict of column-names as the keys and the column(s) as the values.

        key: return the following as the value for each key-value pair:
* int: name-value where value is the int-th column.
* ``Slice`` object, a list of name-columns from slicing the column index. Example ``a.getColumn(Slice(3,,))``;
* Sequence of integers/strings: they are used as the column index/name to select the columns.
* Sequence of booleans: columns where the corresponding boolean is True are chosen.
Default is to return all columns.
        """
        d = self.getData()
        try:
            if d is None or key is None or len(d) == 0:
                return d
        except TypeError:
            pass

        cl = key.__class__
        if issubclass(cl, int):
            t = list(d.items())[key]
            return {t[0]: t[1]}       # {str:Column}
        if issubclass(cl, slice):
            return ODict(list(d.items())[key])  # {str:Column, ...}
        if issubclass(cl, str):
            return {key: d[key]}      # {str:Column}

        if issubclass(cl, Sequence):
            if type(key[0]) == int:
                # {str:Column, ...}
                return ODict(list(d.items())[i] for i in key)
            if type(key[0]) == str:
                return {n: d[n] for n in key}  # {str:Column, ...}
            if type(key[0]) == bool:
                # {str:Column, ...}
                return ODict(x for x, s in zip(d.items(), key) if s)
        else:
            raise ValueError(
                '``key`` must be an int, a string, a slice, or a list of ints, strings, or bools.')

    def getColumn(self, key):
        """ Returns the particular column, or a list of columns.

        key: ref ``getColumnMap()``
* int/str: return the int-th/named column;
* ``Slice`` object, list of columns of sliced column indices;
* list of integers/strings: return a list of columns corresponding to the given column index/name, or where key is True. Example ``a.getColumn(Slice(3,,))``, ``[2, 4]``, ``['time', ``energy']``.
* list of booleans: return a list of columns  where key is True. Example ``[True, False...]``.
        """

        it = self.getColumnMap(key).values()
        if len(it) == 0:
            return []
        if issubclass(key.__class__, (int, str)):
            # return a list of row elements
            return list(it)[0]
        # return transposed in a list
        return list(it)

    def setColumn(self, key, value):
        """ Replaces a column in this table with specified name to specified column if key is a string and exists, or if the key is an integer in 0 to the number of columns, insert at column-index=key, with the name 'column'+key, else add a new coolumn.
        """

        if self.getData() is None:
            key = ''
        elif type(key) == int:
            nms = self.getColumnNames()
            if 0 <= key and key < len(nms):
                key = nms[key]
            else:
                key = ''
        self.addColumn(name=key, column=value)

    def items(self):
        """ for k,v in tabledataset.items()
        """
        return self.getData().items()

    def __getitem__(self, key):
        """ return colmn if given key.

        ref. ``getColumn()``.
        """
        return self.getColumn(key)

    def __setitem__(self, key, value):
        """
        """
        self.setColumn(key, value)

    def __repr__(self):
        return self.toString(level=2)

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 width=0, param_widths=None, matprint=None, trans=True, **kwds):
        """
        tablefmt2: format of 2D data, others see `MetaData.toString`.
        """
        if matprint is None:
            matprint = ndprint

        cn = self.__class__.__name__
        s = '=== %s (%s) ===\n' % (cn, self.description if hasattr(
            self, 'descripion') else '')
        if level > 1:
            s = cn + '('
            s += self.meta.toString(
                level=level,
                tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                width=width, param_widths=param_widths,
                **kwds)
            return s + 'data= {' + \
                ', '.join('"%s": %s' % (k, v.toString(
                    level=level,
                    tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt,
                    width=width, param_widths=param_widths, **kwds))
                    for k, v in self.getColumnMap().items()) + \
                '})'
        else:
            s += mstr(self.__getstate__(), level=level,
                      tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                      excpt=['description'], **kwds)
        stp = 2 if level > 1 else 20 if level == 1 else None
        cols = self.getData().values()

        coldata = [list(itertools.islice(x.data, stp)) for x in cols]
        d = cn + '-dataset =\n'
        nmun = zip((str(x) for x in self.getData().keys()),
                   (str(x.unit) for x in cols))
        hdr = list('%s\n(%s)' % nu for nu in nmun)
        d += matprint(coldata, trans=trans, headers=hdr,
                      tablefmt=tablefmt, tablefmt1=tablefmt1,
                      tablefmt2=tablefmt2, **kwds)
        collen = self.getRowCount()
        if level and stp < collen:
            d += '(Only display %d rows of %d for level=%d.)' % (stp, collen, level)
        return s + '\n' + d + '\n'

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           meta=self.meta,
                           data=self.getData(),
                           _STID=self._STID)


class IndexedTableDataset(Indexed, TableDataset):
    """ TableDataset with an index table for efficient row look-up.

    """

    def __init__(self, **kwds):
        """
        """
        self._indexCols = [0]
        self._rowIndexTable = {}
        super().__init__(**kwds)  # initialize data, meta, unit

    def getColumnsToLookup(self):
        """ returns an iterator that gives a number of sequences to looking up over.
        """

        # list of Column's arrays
        return [x.data for x in self.getColumn(self._indexPattern)]

    def setData(self, data):
        """  sets name-column pairs from data and updates index if needed

        """

        d = self.getData()
        if d:
            reindex = False
            lcd = len(d)
            if issubclass(data.__class__, seqlist):
                for ind, x in enumerate(data):
                    if lcd > ind:
                        if reindex == False and ind in self._indexPattern:
                            reindex = True
        else:
            reindex = True
        super().setData(data)
        if reindex:
            self.updateToc()

    def vLookUp(self, key, return_index=True, multiple=False):
        """ Similar to Excel VLOOKUP, return all records (rows) that match the key.
        key: taken as a dictionary key unless ``multiple`` is True.
        return_index: if True (default) return index in the array of columns.
        multiple: if True (default is False) loop through key as a sequence of keys and return a sequece.
        """

        if multiple:
            if return_index:
                toc = self._tableOfContent
                return [toc[k] for k in key]
            else:
                toc = self._tableOfContent
                # return [[c[toc[k]] for c in self._list] for k in key]
                return list(zip(*((c[toc[k]] for k in key) for c in self._list)))
        else:
            if return_index:
                return self._tableOfContent[key]
            else:
                rec_ind = self._tableOfContent[key]
                return [c[rec_ind] for c in self._list]

    def hashx(self):
        s = self.__getstate__().values()
        l = []
        return super().hash(hash_list=self.data.values())

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return Indexed.__getstate__(self).update(description=self.description,
                                                 meta=self.meta,
                                                 data=self.getData(),
                                                 _STID=self._STID)
