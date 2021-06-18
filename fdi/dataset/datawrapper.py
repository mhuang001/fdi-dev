# -*- coding: utf-8 -*-
from .odict import ODict
from .quantifiable import Quantifiable
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable

from collections.abc import Container, Sized
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class DataContainer(Annotatable, Copyable, DeepEqual, Container, Sized):
    """ A DataContainer is a composite of data and description.
    mh: note that There is no metadata.
    Implemented partly from AbstractDataWrapper.
    """

    def __init__(self, data=None, **kwds):
        """

        data: a Container. Default is None.
        """
        #print(__name__ + str(kwds))

        if data is None or issubclass(data.__class__, Container):
            self.setData(data)
        else:
            raise TypeError('DataContainer needs a Container to initialize, not ' +
                            type(data).__name__)
        super().__init__(**kwds)

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
        try:
            return self._data
        except AttributeError:
            od = ODict()
            self._data = od
            return od

    def hasData(self):
        """ Returns whether this data wrapper has data. """
        return self.getData() is not None and len(self.getData()) > 0

    def __contains__(self, x):
        """
        """
        try:
            return x in self._data
        except AttributeError:
            return False

    def __len__(self, *args, **kwargs):
        """ size of data
        """
        try:
            return self._data.__len__(*args, **kwargs)
        except AttributeError:
            return 0


class DataWrapper(DataContainer, Quantifiable):
    """ A DataWrapper is a composite of data, unit and description.
    mh: note that all data are in the same unit. There is no metadata.
    Implemented from AbstractDataWrapper.
    """

    def __init__(self, *args, **kwds):
        """ 
        """
        super().__init__(*args, **kwds)


class DataWrapperMapper():
    """ Object holding a map of data wrappers. """

    def __init__(self, *args, **kwds):
        """ 
        """
        super().__init__(*args, **kwds)

    def getDataWrappers(self):
        """ Gives the data wrappers, mapped by name. """
        return self._sets
