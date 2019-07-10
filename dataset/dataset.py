from collections import OrderedDict

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.annotatable import Annotatable
from dataset.copyable import Copyable
from dataset.eq import DeepEqual
# from dataset.composite import
from dataset.metadata import Attributable, AbstractComposite, DataWrapper
from dataset.odict import ODict
from dataset.serializable import Serializable
from dataset.listener import ColumnListener


class Dataset(Attributable, Annotatable, Copyable, Serializable, DeepEqual):
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
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)


class ArrayDataset(Dataset, DataWrapper):
    """  Special dataset that contains a single Array Data object.
    """

    def __init__(self, data=None, unit=None, **kwds):
        """
        """
        super().__init__(**kwds)  # initialize data, meta, unit
        self._data = data
        self.unit = unit

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", meta = %s, data = "%s", unit = "%s"}' % \
            (str(self.description), str(self.meta), str(self._data), str(self.unit))

    def toString(self):
        s = '{description = "%s", meta = %s, data = "%s", unit = "%s"}' % \
            (str(self.description), self.meta.toString(),
             str(self._data), str(self.unit))
        return s

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     meta=self.meta,
                     data=self.getData(),
                     unit=self.unit,
                     classID=self.classID,
                     version=self.version)


class Column(ArrayDataset, ColumnListener):
    """ A Column is a the vertical cut of a table for which all cells have the same signature. It contains raw ArrayData, and optionally a description and unit.

    table = TableDataset()
    table.addColumn("Energy",Column(data=[1,2,3,4],description="desc",unit='eV'))
    """
    pass


class TableModel():
    """ to interrogate a tabular data model
    """

    def __init__(self, **kwds):
        """

        """
        # self.data = []
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


class TableDataset(Dataset, DataWrapper, TableModel):
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

    def __init__(self, data=None, **kwds):
        """
        """
        super().__init__(**kwds)  # initialize data, meta, unit
        self.setData(data)

    def setData(self, data):
        """ set name-column pairs if any of ['name'], .name,
        .__next__() is valid for each item in data
        """
        # logging.debug(data.__class__)
        if data is not None and len(data) != 0:
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
            #k,v = zip(*l)
            i = [id(x) for x in v]
            idx = i.index(id(key))
        else:
            idx = key
        return idx

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

    def __setitem__(self, key, value):
        """
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
        idx = self.indexOf(key)
        return idx if issubclass(key.__class__, Column) else self.col(idx)[1]

    def removeColumn(self, key):
        """
        """
        if issubclass(key.__class__, str):
            name = key
        else:
            name = self.col(key)[0]
        del(self.data[name])

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
