# -*- coding: utf-8 -*-
from .odict import ODict
from .quantifiable import Quantifiable
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable

from collections.abc import Container
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class DataContainer(Annotatable, Quantifiable, Copyable, DeepEqual):
    """ A DataContainer is a composite of data and description.
    mh: note that There is no metadata.
    Implemented partly from AbstractDataWrapper.
    """

    def __init__(self, data=None, **kwds):
        """

        data: a Container. Default is None.
        """
        #print(__name__ + str(kwds))
        super(DataContainer, self).__init__(**kwds)

        if data is None or issubclass(data.__class__, Container):
            self.setData(data)
        else:
            raise TypeError('DataContainer needs a Container to initialize, not ' +
                            type(data).__name__)

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
            '{ %s <%s>, description = "%s" }' % \
            (str(self.getData()), str(self.unit), str(self.description))


class DataWrapperMapper():
    """ Object holding a map of data wrappers. """

    def getDataWrappers(self):
        """ Gives the data wrappers, mapped by name. """
        return self._sets
