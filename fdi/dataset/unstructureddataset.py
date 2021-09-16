# -*- coding: utf-8 -*-

from .abstractcomposite import AbstractComposite
from .typed import Typed
from .copyable import Copyable
from .serializable import Serializable
from .odict import ODict
from .dataset import Dataset
from .listener import MetaDataListener
from ..utils.fetch import fetch

try:
    from .unstructureddataset_datamodel import Model
except ImportError:
    Model = {'metadata': {}}
import xmltodict

import json
import itertools
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)


class UnstrcturedDataset(AbstractComposite, Typed, Copyable, MetaDataListener):
    """ Container for data without pre-defined structure or organization.. """

    def __init__(self, data=None,
                 description=None,
                 typ_=None,
                 version=None,
                 zInfo=None,
                 alwaysMeta=True,
                 **kwds):
        """
        """

        self._list = []

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__', 'zInfo', 'kwds'),
                locals().items())
        )

        global Model
        if zInfo is None:
            zInfo = Model

        super().__init__(zInfo=zInfo, **metasToBeInstalled,
                         **kwds)  # initialize data, meta, unit
        # self.setData(data)

    def getData(self):
        """ Optimized for _data being an ``ODict`` implemented with ``UserDict``.

        """

        try:
            return self._data.data
        except AttributeError:
            d = super().getData()
            if hasattr(d, 'data'):
                return self._data.data
            else:
                return d

    def setData(self, data, **kwds):
        """ Put data in the dataset.

        Depending on `self.type_`: 
        * Default is `None` for arbitrarily nested Pyton data structure.
        * Use 'json' to have the input string loaded by `json.loads`,
        * 'xml' by `xmltodict.parse`. 
        """

        if self._type == 'json':
            data = json.loads(data, **kwds)
        if self._type == 'xml':
            data = xmltodict.parse(data, **kwds)
        super().setData(data)

    def fetch(self, paths, exe=['is'], not_quoted=True):

        return fetch(paths, self, re='', exe=exe, not_quoted=not_quoted)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            meta=getattr(self, '_meta', None),
            data=self.getData(),
            _STID=self._STID)
