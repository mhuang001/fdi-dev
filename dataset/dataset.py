from collections import OrderedDict
from dataset.logdict import doLogging, logdict
if doLogging:
    import logging
    import logging.config

    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger(__name__)
    #logger.debug('level %d' %  (logger.getEffectiveLevel()))


from dataset.eq import Serializable, Annotatable, Copyable, DeepEqual
# from dataset.composite import
from dataset.metadata import Attributable, AbstractComposite, DataWrapper


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
        self.data = data
        self.unit = unit

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return dict(description=self.description,
                    meta=self.meta,
                    data=self.data,
                    unit=self.unit,
                    classID=self.classID,
                    version=self.version)


class TableModel():
    """ to interrogate a tabular data model
    """

    def __init__(self, **kwds):
        """

        """
        self.data = []
        super().__init__(**kwds)

    def getColumnClass(self, columnIndex):
        """ Returns the most specific superclass for all the cell
        values in the column.
        """
        return self.data[columnIndex]['class']

    def getColumnCount(self):
        """ Returns the number of columns in the model. """
        return len(self.data)

    def getColumnName(self, columnIndex):
        """ Returns the name of the column at columnIndex. """
        return self.data[columnIndex]['name']

    def getRowCount(self):
        """ Returns the number of rows in the model. """
        return self.data[columnIndex]

    def getValueAt(self, rowIndex, columnIndex):
        """ Returns the value for the cell at columnIndex and rowIndex. """
        return self.data[columnIndex]['column'][rowIndex]

    def isCellEdidata(self, rowIndex, columnIndex):
        """ Returns true if the cell at rowIndex and columnIndex
        is edidata. """
        return True

    def setValueAt(self, aValue, rowIndex, columnIndex):
        """Sets the value in the cell at columnIndex and rowIndex
        to aValue."""
        self.data[columnIndex]['column'][rowIndex] = aValue


class TableDataset(Dataset, DataWrapper, TableModel):
    """  Special dataset that contains a single Array Data object.
    """

    def __init__(self, data=None, **kwds):
        """
        """
        super().__init__(**kwds)  # initialize data, meta, unit
        self.data = [] if data is None else [OrderedDict(x) for x in data]

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return dict(description=self.description,
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
        super().__init__(**kwds)  # initialize sets, meta, unit

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return dict(description=self.description,
                    meta=self.meta,
                    sets=self.sets,
                    classID=self.classID,
                    version=self.version)
