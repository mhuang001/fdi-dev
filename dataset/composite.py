from collections import OrderedDict

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.eq import DeepEqual
#from dataset.listener import DatasetEventSender, DatasetListener
#from dataset.metadata import DataWrapperMapper


class Composite(DeepEqual):
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
        self.sets = OrderedDict()
        super().__init__(**kwds)

    def containsKey(self, name):
        """ Returns true if this map contains a mapping for
        the specified name. """
        return name in self.sets

    def get(self, name):
        """ Returns the dataset to which this composite maps the
        specified name.
        mh: changed name to get_ to use super class get"""
        return self.sets.get(name)

    def set(self, name, dataset):
        """ Associates the specified dataset with the specified key
        in this map(optional operation). If the map previously
        contained a mapping for this key, the old dataset is
        replaced by the specified dataset.
        this composite does not permit null keys or values,
        and the specified key or value is null."""

        if name == '' or name is None or dataset is None:
            logger.error('Noooo')
            return
        self.sets[name] = dataset

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, dataset):
        self.set(name, dataset)

    def isEmpty(self):
        """ Returns true if this map contains no key - value mappings. """
        return len(self.sets) == 0

    def keySet(self):
        """ Returns a set view of the keys contained in this composite. """
        return list(self.sets.keys())

    def remove(self, name):
        """ Removes the mapping for this name from this composite. """
        if name == '' or name is None or name not in self.sets:
            logger.error('Noooo')
            return None
        return self.sets.pop(name)

    def size(self):
        """ Returns the number of key - value mappings in this map. """
        return len(self.sets)

    def __repr__(self):
        ks = self.keySet()
        return self.__class__.__name__ + \
            str(ks)

    def toString(self):
        s = ''
        for (k, v) in self.sets.items():
            s = s + str(k) + ' = ' + str(v) + ', '
        return self.__class__.__name__ + \
            '[' + s + ']'

    def __contains__(self, x):
        """ mh: enable 'x in composite' """
        return x in self.sets

    def items(self):
        """ Enable pairs = [(v, k) for (k, v) in d.items()]. """
        return self.sets.items()

    def values(self):
        """ Enable pairs = zip(d.values(), d.keys()) """
        return self.sets.values

    def __iter__(self):
        return self.sets.__iter__()

    def __next__(self):
        return self.sets.__next__()
