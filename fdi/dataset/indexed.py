# -*- coding: utf-8 -*-

from itertools import count
from collections.abc import Sequence
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
        return [self.data[i] for i in self._indexPattern]

    def updateToc(self, which=None, for_records=None):
        """ Build index in format specified in indexPattern for retrieving record.
        which: an iterator that gives a number of sequences to looking up over. Default is ``getColumnsToLookup()``.
        for_records: a list or a ``Slice`` of record (row) numbers. Those are changed records that caused updating. default is all records.
        """

        # always rebuild all TODO:
        for_records = None
        self._tableOfContent = {}

        cols = self.getColumnsToLookup() if which is None else which

        ip = self._indexPattern
        one = len(ip) == 1
        if for_records is None:
            # for all records
            itr = zip(cols[0], count()) if one else zip(zip(*cols), count())
        elif issubclass(for_records.__class__, slice):
            # list of column's arrays for all slice records
            # range(sys.maxsize)[for_records] gives all valid record index numbers
            if one:
                itr = zip(cols[0][for_records],
                          range(sys.maxsize)[for_records])
            else:
                itr = zip(zip(*(c[for_records] for c in cols)),
                          range(sys.maxsize)[for_records])
        else:
            # for_records is a list
            # list of column's arrays for all listed records
            if one:
                itr = zip((cols[0][i] for i in for_records), for_records)
            else:
                itr = zip((tuple(c[i] for c in cols)
                           for i in for_records), for_records)

        self._tableOfContent.update(itr)

    @ property
    def indexPattern(self):
        return self._indexPattern

    @ indexPattern.setter
    def indexPattern(self, *key):
        """ set the key pattern used to retrieve records.

        *key: as a list of integers. taken as column numbers. future look-up will search and return the record where  a match is found in these columns. Example: a.indexPattern=[0,2] would setup to use the first and the third columns to make look-up keys. Default is the first column.
        """

        lk = len(key)
        if lk == 0:
            self._indexPattern = None
            return
        # more than on column number
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

        self._indexPattern = tk

    @ property
    def toc(self):
        """ returns  the index table of content.
        """

        return self._tableOfContent

    @ toc.setter
    def toc(self, table):
        """ sets the index table of content.

        """

        self._tableOfContent = table

    def clearToc(self):
        """ Clears the index table of content.
        """

        self._tableOfContent.clear()

    def vLookUp(self, key, return_index=True, multiple=False):
        """ Similar to Excel VLOOKUP, return all records (rows) that match the key.
        key: taken as a dictionary key unless ``multiple`` is True.
        return_index: if True (default) return index in the array of columns.
        multiple: if True (default is False) loop through key as a sequence of keys and return a sequece.
        """

        if multiple:
            if return_index:
                toc = self._tableOfContent
                return [toc[k] for k in key]
            else:
                toc = self._tableOfContent
                cols = self.data
                # return [[c[toc[k]] for c in cols] for k in key]
                return list(zip(*([c[toc[k]] for k in key] for c in cols)))
        else:
            if return_index:
                return self._tableOfContent[key]
            else:
                rec_ind = self._tableOfContent[key]
                return [c[rec_ind] for c in self.data]

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            indexPattern=self._indexPattern,
            toc=self._tableOfContent
        )
