import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.annotatable import Annotatable
from dataset.copyable import Copyable
from dataset.eq import DeepEqual
from dataset.quantifiable import Quantifiable
from dataset.odict import ODict


class DataWrapper(Annotatable, Quantifiable, Copyable, DeepEqual):
    """ A DataWrapper is a composite of data, unit and description.
    mh: note that all data are in the same unit. There is no metadata.
    Implemented from AbstractDataWrapper.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._data = ODict()

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
        """ Returns the data in this """
        return self._data

    def hasData(self):
        """ Returns whether this data wrapper has data. """
        return len(self.getData()) > 0

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", data = "%s", unit = "%s"}' % \
            (str(self.description), str(self.getData()), str(self.unit))


class DataWrapperMapper():
    """ Object holding a map of data wrappers. """

    def getDataWrappers(self):
        """ Gives the data wrappers, mapped by name. """
        return self._sets
