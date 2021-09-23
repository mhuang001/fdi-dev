# -*- coding: utf-8 -*-

from .abstractcomposite import AbstractComposite
from .typed import Typed
from .attributable import Attributable
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
import jsonpath_ng.ext as jex

import json
import itertools
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)


class UnstrcturedDataset(Dataset, Copyable):
    """ Container for data without pre-defined structure or organization..

    `MetaDataListener` must stay to the left of `AbstractComposite`.
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
        """

        self._list = []

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__',
                                   'data', 'zInfo', 'kwds'),
                locals().items())
        )

        global Model
        if zInfo is None:
            zInfo = Model

        super().__init__(zInfo=zInfo, **metasToBeInstalled,
                         **kwds)  # initialize typ_, meta, unit
        self.data_pv = {}
        self.input(data=data, doctype=doctype)

    def getData(self):
        """ Optimized for _data being initialized to be `_data` by `DataWrapper`.

        """

        try:
            return self._data
        except AttributeError:
            return self._data.data

    def jsonPath(self, expre, *args, **kwds):
        jsonpath_expression = jex.parse(expre, *args, **kwds)
        match = jsonpath_expression.find(self.data)
        return match

    def make_meta(self, print=False, **kwds):
        full = self.jsonPath('$..*', **kwds)
        pvs = list((str(x.full_path), x.value)
                   for x in full if
                   not issubclass(x.value.__class__, (list, dict)))
        for x in pvs:
            dpath = x[0].replace('.', '/').replace('[', '').replace('', '')
            dval = x[1]
            self.data_pv[dpath] = dval

        __import__('pdb').set_trace()
        self.__setattr__(dpath, dval)

    def input(self, data, doctype=None, **kwds):
        """ Put data in the dataset.

        Depending on `doctype`:
        * Default is `None` for arbitrarily nested Pyton data structure.
        * Use 'json' to have the input string loaded by `json.loads`,
        * 'xml' by `xmltodict.parse`.
        """

        if doctype:
            self.doctype=doctype
        if data:
            # do not ask for self.type unless there is real data.
            if self.doctype == 'json':
                data=json.loads(data, **kwds)
            elif self.doctype == 'xml':
                data=xmltodict.parse(data, **kwds)
            # set Escape if not set already
            if '_STID' in data:
                ds = data['_STID']
                if not ds.startswith('0'):
                    data['_STID'] = '0%s' % ds
        super().setData(data)
        #self.make_meta()

    def fetch(self, paths, exe=['is'], not_quoted=True):

        return fetch(paths, self, re='', exe=exe, not_quoted=not_quoted)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            meta=getattr(self, '_meta', None),
            data=self.getData(),
            _STID=self._STID)
