# -*- coding: utf-8 -*-

from itertools import count
from collections import Sequence
import sys


class Indexed():
    """ Abstract class with an index table for efficient records look-up.

    """

    def __init__(self, indexPattern=None, **kwds):
        """

        indexPattern: specifies which columns to uae to do look up.
        """
        self._indexPattern = [0] if indexPattern is None else indexPattern
        self._tableOfContent = {}
        super().__init__(**kwds)  # initialize data, meta, unit

    def getColumnsToLookup(self):
        """ returns an iterator that gives a number of sequences to looking up over.

        Defau;t is a tuple of the ``data`` attributes of every columns specified by ``indexPattern``. To be overrided for different data model.
        """

        # list of Column's arrays
        return (x.data for x in self.getColumn(self._indexPattern))

    def updateToc(self, which=None, for_records=None):
        """ Build index in format specified in indexPattern for retrieving record.
    which: an iterator that gives a number of sequences to looking up over. Default is ``getColumnsToLookup()``.
        for_records: a list or a ``Slice`` of record (row) numbers. Those are changed records that caused updating. default is all records.
        """
        #import pdb
        # pdb.set_trace()

        cols = self.getColumnsToLookup() if which is None else which
        # length of array
        if for_records is None:
            # for all records
            itr = (zip(zip(*cols), count()))
        elif issubclass(for_records.__class__, Slice):
            # list of column's arrays for all slice records
            # range(sys.maxsize)[for_records] gives all valid numbers
            itr = (zip(zip(cols)[for_records],
                       range(sys.maxsize)[for_records]))
        else:
            # for_records is a list
            # list of column's arrays for all listed records
            itr = (zip(zip(cols[i] for i in for_records), for_records))

        self._tableOfContent.update(itr)

    @property
    def indexPattern(self):
        return self._indexPattern

    @indexPattern.setter
    def indexPattern(self, *key):
        """ set the key pattern used to retrieve records.

        *key: as a list of integers. taken as column numbers. future look-up will search and return the record where  a match is found in these columns. Example: a.indexPattern=[0,2] would setup to use the first and the third columns to make look-up keys. Default is the first column.
        """
        if len(key) == 0:
            self._indexPattern = []
            return

        tk = []
        msg = 'Need integers or tuple of integers to specify look-up indices.'
        for k in key:
            if type(key) == int:
                tk.append(k)
            elif issubclass(key.__class__, Sequence):
                for k2 in k:
                    if type(k2) == int:
                        tk.append(k2)
                    else:
                        raise TypeError(msg)
            else:
                raise TypeError(msg)

        self._indexPattern = tuple(tk)

    @property
    def toc(self):
        """ returns  the index table of content.
        """

        return self._tableOfContent

    @toc.setter
    def toc(self, table):
        """ sets the index table of content.

        """

        self._tableOfContent = table

    def clearToc(self):
        """ Clears the index table of content.
        """

        self._tableOfContent.clear()

    def vLlookUp(self, key, return_index=False):
        """ Override this to get records with the key.
        """

        raise NotImplementedError
        return ret

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            indexPattern=self._indexPattern,
            toc=self._tableOfContent
        )
