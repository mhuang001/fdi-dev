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
from functools import lru_cache
from collections import OrderedDict
import logging
# create logger
logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def jexp(expr, *args, **kwds):
    return jex.parse(expr, *args, **kwds)


def getCacheInfo():
    info = {}
    for i in [jexp]:
        info[i] = i.cache_info()

    return info


class UnstrcturedDataset(Dataset, Copyable):
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
        # for `xmltodict`  `xml_attribs` default to ```True```.
        self.xml_attribs = kwds.pop('xml_attribs', True)
        self.attr_prefix = kwds.pop('attr_prefix', '')
        self.cdata_key = kwds.pop('cdata_key', 'text')

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

    def jsonPath(self, expr, val='simple', sep='/', indent=None, *args, **kwds):
        """ Make a JSONPath query on the data.

        :expr: JSONPath expression. Ref 'jsonpath_ng'

        :sep: '' or `None` for keeping `jsonpath_ng` format (e.g. `a.b.[3].d`; other string for substituting '.' to the given string, with '[' and ']' removed. Default is '/'.
        :val: 'context' for returning the `list` of `DatumInContext` of `find`; 'simple' (default) for list of simple types of values and summarizing `list` and `dict` values; other for a list of un-treated `DatumInContext.value`s.
        :indent: for `json.dumps`.
        Returns
        -------
        If `val` is ```context```, return  the `list` of `DatumInContext` of `jsonpath_ng.ext.parse().find()`.
        Else return a `list` of `full_path`-`value` pairs from the output of `find().`
        * If `val` is ```simple```, only node values of simple types are kept, `list` and `dict` types will show as '<list> length' and '<dict> [keys [... [length]]]', respectively.
        * If `val` is ```full```, the values of returned `list`s are  un-treated `DatumInContext.value`s.
        """
        jsonpath_expression = jexp(expr, *args, **kwds)
        match = jsonpath_expression.find(self.data)
        if val == 'context':
            return match
        res = []
        for x in match:
            # make key
            key = str(x.full_path)
            if sep == '' or sep is None:
                pass
            else:
                key = key.replace('.', sep).replace('[', '').replace(']', '')
            # make value
            vc = x.value.__class__
            if val == 'simple':
                if issubclass(vc, (list)):
                    value = f'<{vc.__name__}> {len(x.value)}'
                elif issubclass(vc, (dict)):
                    n = 5
                    ks = ', '.join(f'"{k}"' for k in
                                   itertools.islice(x.value.keys(), n))
                    l = len(x.value)
                    if l > n:
                        ks += f'{ks}...({l})'
                    value = f'<{vc.__name__}> {ks}'
                else:
                    value = x.value
            elif val == 'full':
                value = x.value
            else:
                raise ValueError(f'Invalid output type for jsonPath: {val}')
            res.append((key, value))
        return res

    def make_meta(self, print=False, **kwds):
        full = self.jsonPath('$..*', **kwds)
        for pv in full:
            self.__setattr__(p[0], p[1])
        self.data_pv = full

    def input(self, data, doctype=None, **kwds):
        """ Put data in the dataset.

        Depending on `doctype`:
        * Default is `None` for arbitrarily nested Pyton data structure.
        * Use 'json' to have the input string loaded by `json.loads`,
        * 'xml' by `xmltodict.parse`.
        """

        if doctype:
            self.doctype = doctype
        if data:
            # do not ask for self.type unless there is real data.
            if self.doctype == 'json':
                data = json.loads(data, **kwds)
            elif self.doctype == 'xml':
                xa = kwds.pop('xml_attribs', None)
                xa = self.xml_attribs if xa is None else xa
                ap = kwds.pop('attr_prefix', None)
                ap = self.attr_prefix if ap is None else ap
                ck = kwds.pop('cdata_key', None)
                ck = self.cdata_key if ck is None else ck

                data = xmltodict.parse(data,
                                       attr_prefix=ap,
                                       cdata_key=ck,
                                       xml_attribs=xa, **kwds)
            # set Escape if not set already
            if '_STID' in data:
                ds = data['_STID']
                if not ds.startswith('0'):
                    data['_STID'] = '0%s' % ds
        super().setData(data)
        # self.make_meta()

    def fetch(self, paths, exe=['is'], not_quoted=True):

        return fetch(paths, self, re='', exe=exe, not_quoted=not_quoted)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(
            meta=getattr(self, '_meta', None),
            data=self.getData())
