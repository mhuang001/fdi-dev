# -*- coding: utf-8 -*-

from .abstractcomposite import AbstractComposite
from .typed import Typed
from .attributable import Attributable
from .copyable import Copyable
from .serializable import Serializable
from .odict import ODict
from .dataset import Dataset
from .listener import MetaDataListener

try:
    from .unstructureddataset_datamodel import Model
except ImportError:
    Model = {'metadata': {}}
import xmltodict

import mmap

import json
from copy import copy
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)


class UnstructuredDataset(Dataset, Copyable):
    """ Container for data without pre-defined structure or organization..

    `MetaDataListener` must stay to the left of `AbstractComposite`.

    For `xmltodict`  `xml_attribs` default to ```False```. 
    """

    def __init__(self, data=None,
                 description=None,
                 typ_=None,
                 doctype=None,
                 version=None,
                 zInfo=None,
                 alwaysMeta=True,
                 **kwds):
        """
        Accepts keyword args to `xmltodict`, e.g. `xml_attribs`, `attr_prefix` and `cdata_key`.
        """

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = copy(locals())
        metasToBeInstalled.pop('__class__', None)
        metasToBeInstalled.pop('kwds', None)
        metasToBeInstalled.pop('self', None)
        metasToBeInstalled.pop('zInfo', None)

        self._list = []

        global Model
        if zInfo is None:
            zInfo = Model
        # for `xmltodict`  `xml_attribs` default to ```True```.
        self.xml_attribs = kwds.pop('xml_attribs', True)
        self.attr_prefix = kwds.pop('attr_prefix', '')
        self.cdata_key = kwds.pop('cdata_key', 'value')

        super().__init__(zInfo=zInfo, **metasToBeInstalled,
                         **kwds)  # initialize typ_, meta, unit
        self.data_pv = {}
        self.put(data=data, doctype=doctype)

    def getData(self):
        """ Optimized for _data being initialized to be `_data` by `DataWrapper`.

        """

        try:
            return self._data
        except AttributeError:
            return self._data.data

    def make_meta(self, print=False, **kwds):
        full = self.jsonPath('$..*', **kwds)
        for pv in full:
            self.__setattr__(p[0], p[1])
        self.data_pv = full

    def put(self, data, doctype=None, **kwds):
        """ Put data in the dataset.

        Depending on `doctype`:
        * Default is `None` for arbitrarily nested Pyton data structure.
        * Use 'json' to have the input string loaded by `json.loads`,
        * 'xml' by `xmltodict.parse`.
        """

        if doctype:
            self.doctype = doctype
        if data:
            stid = b'_STID' if issubclass(data.__class__, bytes) else '_STID'
            # do not ask for self.type unless there is real data.
            if self.doctype == 'json':
                if issubclass(data.__class__, mmap.mmap):
                    data = bytearray(data)
                loaded = json.loads(data, **kwds)
            elif self.doctype == 'xml':
                xa = kwds.pop('xml_attribs', None)
                xa = self.xml_attribs if xa is None else xa
                ap = kwds.pop('attr_prefix', None)
                ap = self.attr_prefix if ap is None else ap
                ck = kwds.pop('cdata_key', None)
                ck = self.cdata_key if ck is None else ck

                loaded = xmltodict.parse(data,
                                         attr_prefix=ap,
                                         cdata_key=ck,
                                         xml_attribs=xa, **kwds)
            else:
                # Others are loaded as data structures
                loaded = data
                #raise ValueError('Cannot process %s type.' % str(doctype))
            # set Escape if not set already
            if hasattr(loaded, '__iter__') and stid in loaded:
                ds = loaded[stid]
                if not ds.startswith('0'):
                    loaded[stid] = '0%s' % ds
        else:
            loaded = data
        super().setData(loaded)
        # self.make_meta()

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            meta=getattr(self, '_meta', None),
            data=self.getData())
