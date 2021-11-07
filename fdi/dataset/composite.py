# -*- coding: utf-8 -*-

from .datawrapper import DataContainer
from .odict import ODict
from .eq import DeepEqual
from .serializable import Serializable
from .invalid import INVALID

from collections import Sized, Container, Iterator, OrderedDict, UserDict
from collections.abc import MutableMapping
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

# from .listener import DatasetEventSender, DatasetListener
# from .metadata import DataWrapperMapper

# order of Container, Sized, Iterator must be the same as in DataContaier!


# class Composite(DeepEqual, UserDictAdapter, Serializable):  # ):

class Composite(DataContainer, Serializable, MutableMapping):
    """ A container of named Datasets.

    This container can hold zero or more datasets, each of them
    stored against a unique name. The order of adding datasets
    to this Composite is important, that is:
    the keySet() method will return a set of labels of the datasets
    in the sequence as they were added.
    Note that replacing a dataset with the same name,
    will keep the order.

    :class:`DeepEqual` must stay to the left of :class:`MutableMapping` so its `__eq__` will get to run. `Serializable` becomes a parent for having `__setstate__`.

    :data: default `None` will init with a `dict`.
    """

    def __init__(self, data=None, **kwds):
        """

        Parameters
        ----------

        Returns
        -------

        """
        # pass data to parent
        super().__init__({} if data is None else data, **kwds)

    def containsKey(self, name):
        """ Returns true if this map contains a mapping for
        the specified name.

        Parameters
        ----------

        Returns
        -------

        """
        return self.__contains__(name)

    def get(self, name, default=INVALID):
        """ Returns the dataset to which this composite maps the
        specified name.

        If the attrbute does not exist and `default` unspecified, raise a KeyError.

        Parameters
        ----------
        :default: assigne to None or anything for missing `name`.
        Returns
        -------

        """
        if name in self.data:
            return self.data[name]
        elif default is INVALID:
            raise KeyError(name + 'not found')
        else:
            return default

    def set(self, name, dataset):
        """ Associates the specified dataset with the specified key
        in this map(optional operation). If the map previously
        contained a mapping for this key, the old dataset is
        replaced by the specified dataset.
        this composite does not permit null or empty keys.

        Parameters
        ----------

        Returns
        -------

        """
        self.data[name] = dataset

    def __getitem__(self, name):
        """
        Parameters
        ----------

        Returns
        -------

        """
        return self._data[name]

    def __delitem__(self, name):
        """
        Parameters
        ----------

        Returns
        -------

        """
        del self.data[name]

    def __setitem__(self, name, dataset):
        """
        Parameters
        ----------

        Returns
        -------

        """

        if 'refs' in self._data and name != 'refs' and not (name in self._data):
            refs = self._data.pop('refs')
            self._data[name] = dataset
            self._data['refs'] = refs
        else:
            self._data[name] = dataset

    def getSets(self):
        """ Provide access to the Map < String, Dataset > .
        mh: api from CompositeDataset

        Parameters
        ----------

        Returns
        -------

        """
        return self.data

    def isEmpty(self):
        """ Returns true if this map contains no key - value mappings.
        Parameters
        ----------

        Returns
        -------

        """
        return len(self.data) == 0

    def keySet(self):
        """ Returns a list view of the keys contained in this composite. 

        Parameters
        ----------

        Returns
        -------

        """
        return list(self.data.keys())

    # convenience method name.
    getDatasetNames = keySet

    def remove(self, name):
        """ Removes the mapping for this name from this composite.
        mh: returns None if name is None or item does not exist.

        Parameters
        ----------

        Returns
        -------

        """
        if name == '' or name is None or name not in self.data:
            logger.debug('Cannot remove non-exist item \'' + name + "'")
            return None
        del self._data[name]

    def size(self):
        """ Returns the number of key - value mappings in this map. 
        Parameters
        ----------

        Returns
        -------

        """
        return len(self.data)

    def getDefault(self):
        """ Convenience method that returns the first dataset \
        belonging to this composite. """

        ls = list(self.values())
        return ls[0] if len(ls) > 0 else None

    def __iter__(self):
        for i in self.data:
            yield i

    def __repr__(self):
        return self.__class__.__name__ + '(' + (self.data.__repr__() if hasattr(self, 'data') else 'None') + ')'

    def toString(self, level=0, matprint=None, trans=True, **kwds):
        """

        Parameters
        ----------

        Returns
        -------

        """
        o = ODict(self.data)
        return self.__class__.__name__ + \
            o.toString(level=level,
                       tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                       matprint=matprint, trans=trans, **kwds)

    string = toString


class UserDictAdapter(UserDict):
    """ Adapter class to make UserDict cooperative to multiple inheritance and take data keyword arg.

    REf. https://rhettinger.wordpress.com/2011/05/26/super-considered-super/
    """

    def __init__(self, data=None, *args, **kwds):
        """

        Parameters
        ----------
        :data: initialize UserDict.

        Returns
        -------

        """
        # pass data to UserDict as the first positional arg
        super().__init__(data, *args, **kwds)
