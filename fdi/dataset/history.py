# -*- coding: utf-8 -*-


from .metadata import guess_value
from .dataset import CompositeDataset
from .arraydataset import ArrayDataset, Column
from .tabledataset import TableDataset
from .serializable import Serializable

import array
from collections import OrderedDict, UserDict

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

#    prjcls = PC.updateMapping()


def check_input(arg, serializable=True):
    """ Raise exception if needed when arg is not simple type or Serializable.
    """
    cls = arg.__class__
    nm = cls.__name__
    if issubclass(cls, (int, float, str, bool, bytes, complex,
                        list, dict, array.array, UserDict)):
        return arg

    if serializable:
        if issubclass(cls, tuple) or not issubclass(cls, Serializable):
            raise TypeError(
                'History parameter "%s" not found to be serializable by `json.dump()` or a subclass of `Serializable`.' % nm)
    return arg


class History(CompositeDataset):
    """ Public interface to the history dataset. Contains the
    main methods for retrieving a script and copying the history.
    """

    def __init__(self, **kwds):
        """
        mh: The copy constructor is better not be implemented. Use copy()
        instead. Remember: not only copies the datasets,
        but also changes the history ID in the metadata and
        relevant table entries to indicate that this a new
        independent product of which the history may change.

        Parameters
        ----------

        Returns
        -------

        """
        super(History, self).__init__(**kwds)

        self['args'] = ArrayDataset(
            data=[], description='Positional arguments given to the pipeline or task that generated this product.')
        self['kw_args'] = TableDataset(
            data=[['name', [], ''], ['value', [], '']],
            description='Keyword arguments given to the pipeline or task that generated this product.')

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern.

        Parameters
        ----------

        Returns
        -------

        """
        visitor.visit(self)

    def getScript(self):
        """ Creates a script from the history.

        Parameters
        ----------

        Returns
        -------

        """

        raise NotImplemented()

    def getTaskHistory(self):
        """ Returns a human readable formatted history tree.

        Parameters
        ----------

        Returns
        -------

        """
        raise NotImplemented()

    def add_input(self, args=None, keywords=None, info=None, *kwds):
        if args:
            for arg in args:
                carg = check_input(arg)
                self['args'].append(carg)
        if kwds:
            if keywords:
                keywords.update(kwds)
            else:
                keywords = kwds
        if keywords:
            for name, var in keywords.items():
                cvar = check_input(var)
                # append the parameter name column and value column
                self['kw_args'].addRow(row={'name': name,
                                            'value': cvar},
                                       rows=False)
        if info:
            for k, v in info.items():
                self.meta[k] = guess_value(v, parameter=True)

    def get_args(self):

        return self['args'], self['kw_args']

    def __getstate__(self):
        """ Can be encoded with serializableEncoder

        Parameters
        ----------

        Returns
        -------

        """
        return OrderedDict(
            _ATTR_meta=self._meta,
            **self.data)
