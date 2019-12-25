# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .annotatable import Annotatable
from .copyable import Copyable
from .eq import DeepEqual
from .quantifiable import Quantifiable
from .odict import ODict


class DataContainer(Annotatable, Quantifiable, Copyable, DeepEqual):
    """ A DataContainer is a composite of data and description.
    mh: note that There is no metadata.
    Implemented partly from AbstractDataWrapper.
    """

    def __init__(self, data=None, **kwds):
        super().__init__(**kwds)
        self.setData(data)

    @property
    def data(self):
        return self.getData()

    @data.setter
    def data(self, newData):
        self.setData(newData)

    def setData(self, data):
        """ Replaces the current DataData with specified argument. 
        mh: subclasses can override this to add listener whenevery data is
        replaced
        """
        self._data = data

    def getData(self):
        """ Returns the data in this dw"""
        return self._data

    def hasData(self):
        """ Returns whether this data wrapper has data. """
        return self.getData() is not None and len(self.getData()) > 0

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", data = "%s"}' % \
            (str(self.description), str(self.getData()))


class DataWrapper(DataContainer):
    """ A DataWrapper is a composite of data, unit and description.
    mh: note that all data are in the same unit. There is no metadata.
    Implemented from AbstractDataWrapper.
    """

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", data = "%s", unit = "%s"}' % \
            (str(self.description), str(self.getData()), str(self.unit))


class DataWrapperMapper():
    """ Object holding a map of data wrappers. """

    def getDataWrappers(self):
        """ Gives the data wrappers, mapped by name. """
        return self._sets
