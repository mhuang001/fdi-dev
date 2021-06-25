# -*- coding: utf-8 -*-
from .odict import ODict
from .eq import DeepEqual
from collections import Sized, Container, Iterator, OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

# from .listener import DatasetEventSender, DatasetListener
# from .metadata import DataWrapperMapper

# order of Container, Sized, Iterator must be the same as in DataContaier!


class Composite(DeepEqual, Container, Sized, Iterator):
    """ A container of named Datasets.

    This container can hold zero or more datasets, each of them
    stored against a unique name. The order of adding datasets
    to this Composite is important, that is:
    the keySet() method will return a set of labels of the datasets
    in the sequence as they were added.
    Note that replacing a dataset with the same name,
    will keep the order.
    """

    def __init__(self, **kwds):
        self._sets = ODict()
        super().__init__(**kwds)

    def containsKey(self, name):
        """ Returns true if this map contains a mapping for
        the specified name. """
        return name in self._sets

    def get(self, name):
        """ Returns the dataset to which this composite maps the
        specified name.
        If the attitute does not exist, return None. This is an OrderedDict behavior.
        """
        return self._sets.get(name)

    def set(self, name, dataset):
        """ Associates the specified dataset with the specified key
        in this map(optional operation). If the map previously
        contained a mapping for this key, the old dataset is
        replaced by the specified dataset.
        this composite does not permit null or empty keys.
        """

        if name == '' or name is None:
            msg = 'Bad dataset name.'
            logger.error(msg)
            raise ValueError(msg)

        self._sets[name] = dataset

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, dataset):
        self.set(name, dataset)

    def getSets(self):
        """ Provide access to the Map < String, Dataset > .
        mh: api from CompositeDataset
        """
        return self._sets

    def isEmpty(self):
        """ Returns true if this map contains no key - value mappings. """
        return len(self._sets) == 0

    def keys(self):
        """ Returns an iterator of the keys contained in this composite. """
        return self._sets.keys()

    def keySet(self):
        """ Returns a list view of the keys contained in this composite. """
        return list(self._sets.keys())

    def remove(self, name):
        """ Removes the mapping for this name from this composite.
        mh: returns None if name is None or item does not exist.
        """
        if name == '' or name is None or name not in self._sets:
            logger.debug('Cannot remove non-exist item \'' + name + "'")
            return None
        return self._sets.pop(name)

    def size(self):
        """ Returns the number of key - value mappings in this map. """
        return len(self._sets)

    def __len__(self):
        """ Returns the number of key - value mappings in this map. """
        return len(self._sets)

    def __repr__(self):
        return self.__class__.__name__ + '(' + (self._sets.__repr__() if hasattr(self, '_sets') else 'None') + ')'

    def toString(self, level=0, matprint=None, trans=True, **kwds):
        return self.__class__.__name__ + \
            self._sets.toString(level=level,
                                tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                                matprint=matprint, trans=trans, **kwds)

    def __contains__(self, x):
        """ mh: enable 'x in composite' """
        return x in self._sets

    def items(self):
        """ Enable pairs = [(v, k) for (k, v) in d.items()]. """
        return self._sets.items()

    def values(self):
        """ Returns an iterator of the parameters contained in this composite.

        Enables pairs = zip(d.values(), d.keys()) 
        """
        return self._sets.values()

    def __iter__(self):
        return self._sets.__iter__()

    def __next__(self):
        return self._sets.__next__()
