import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.annotatable import Annotatable
from dataset.copyable import Copyable
from dataset.eq import DeepEqual
from dataset.datawrapper import DataWrapper
# from dataset.composite import
from dataset.metadata import Attributable, AbstractComposite
from dataset.odict import ODict
from dataset.serializable import Serializable
from dataset.listener import ColumnListener, DatasetBaseListener, MetaDataListener


class Dataset(Attributable, Annotatable, Copyable, Serializable, DeepEqual, MetaDataListener):
    """ Attributable and annotatable information data container
    that can be be part of a Product.

    developer notes:
    The intent is that developers do not derive from this interface
    directly. Instead, they should inherit from one of the generic
    datasets that this package provides:

    ArrayDataset.
    TableDataset or
    CompositeDataset.
    """

    def __init__(self, **kwds):
        """

        """
        super().__init__(**kwds)

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)


class GeneralDataset(Dataset, DataWrapper):
    def __init__(self, **kwds):
        """
        """
        super().__init__(**kwds)  # initialize data, meta, unit

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

    def toString(self):
        s = '{description = "%s", meta = %s, data = "%s", unit = "%s"}' % \
            (str(self.description), self.meta.toString(),
             str(self._data), str(self.unit))
        return s

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # s = ODict(description=self.description, meta=self.meta)  # super().serializable()
        # s.update(ODict(data=self.getData()))
        s = ODict(description=self.description,
                  meta=self.meta,
                  data=self.data,
                  classID=self.classID,
                  version=self.version)
        return s


class ArrayDataset(GeneralDataset):
    """  Special dataset that contains a single Array Data object.
    mh: assumed to contain a mutable sequence which should provide methods append(), count(), index(), extend(), insert(), pop(), remove(), reverse() and sort()
    """

    def __init__(self, unit=None, **kwds):
        """
        """
        super().__init__(**kwds)  # initialize data, meta
        if not issubclass(self.data.__class__, list) and self.data is not None:
            # dataWrapper initializes data as None
            logging.error(
                'data in ArrayDataset must be a subclass of list: ' + self.data.__class__.__name__)
            raise TypeError()

        self.unit = unit

    def __setitem__(self, key, value):
        """
        """
        d = self.getData()
        if key < len(d):
            d[key] = value
        else:
            d.append(value)

    def __getitem__(self, key):
        """ return value at key.
        """
        d = self.getData()
        l = len(d)

        if issubclass(key.__class__, int) and key < l:
            return d[key]
        elif issubclass(key.__class__, slice):
            r = self.copy()
            r.data = d[key]
            return r
        else:
            raise ValueError('index %d out of range 0..%d' % (key, l))

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", meta = %s, data = "%s", unit = "%s"}' % \
            (str(self.description), str(self.meta), str(self.data), str(self.unit))

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # s = ODict(description=self.description, meta=self.meta, data=self.data)  # super().serializable()
        s = ODict(description=self.description,
                  meta=self.meta,
                  data=self.data,
                  classID=self.classID,
                  version=self.version)
        s.update(ODict(unit=self.unit))
        return s


class Column(ArrayDataset, ColumnListener):
    """ A Column is a the vertical cut of a table for which all cells have the same signature. It contains raw ArrayData, and optionally a description and unit.

    table = TableDataset()
    table.addColumn("Energy",Column(data=[1,2,3,4],description="desc",unit='eV'))
    """
    pass


class TableModel(DataWrapper):
    """ to interrogate a tabular data model
    """

    def __init__(self, **kwds):
        """

        """
        super().__init__(**kwds)

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
    A TableDataset is a tabular collection of Columns. It is optimized to work on array data as specified in the herschel.ia.numeric package.
    The column-wise approach is convenient in many cases. For example, one has an event list, and each algorithm is adding a new field to the events (i.e. a new column, for example a quality mask).

    Although mechanisms are provided to grow the table row-wise, one should use these with care especially in performance driven environments as this orthogonal approach (adding rows rather than adding columns) is expensive.

    Examples of actual ArrayData objects can be found in the herschel.ia.numeric package, and therefore they will not be discussed here.

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
        super().__init__(**kwds)  # initialize data, meta, unit

    def setData(self, data):
        """ set name-column pairs if any of ['name'], .name,
        .__next__() is valid for each item in data
        """
        # logging.debug(data.__class__)
        if data is not None:
            d = ODict()
            if issubclass(data.__class__, list):
                for x in data:
                    if 'name' in x and 'column' in x:
                        d[x['name']] = x['column']
                    elif hasattr(x, 'name') and hasattr('column', x):
                        d[x.name] = x.column
                    elif issubclass(x.__class__, dict):
                        k = x.keys()[0]
                        d[k] = x[k]
                    elif issubclass(x.__class__, tuple):
                        d[x[0]] = x[1]
                    else:
                        raise ValueError
            elif issubclass(data.__class__, dict):
                for k, v in data.items():
                    d[k] = v
            else:
                raise ValueError

            # logging.debug(d)
            super().setData(d)
        else:
            super().setData(ODict())

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
        mh: row is a dict with names ass keys
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
        return self.__class__.__name__ +\
            '{ description = "%s", meta = %s, data = "%s", unit = "%s"}' %\
            (str(self.description), str(self.meta), str(self.data), str(self.unit))

    def toString(self):
        s = '{description = "%s", meta = %s, data = "%s", unit = "%s"}' %\
            (str(self.description), self.meta.toString(),
             str(self.data), str(self.unit))
        return s

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     meta=self.meta,
                     data=self.data,
                     classID=self.classID,
                     version=self.version)


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
        super().__init__(**kwds)  # initialize _sets, meta, unit

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     meta=self.meta,
                     _sets=self._sets,
                     classID=self.classID,
                     version=self.version)
