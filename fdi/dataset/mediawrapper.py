# -*- coding: utf-8 -*-

from .datawrapper import DataWrapper
from .typed import Typed
from .typecoded import Typecoded
from .listener import ColumnListener
from .ndprint import ndprint
from ..utils.common import mstr, bstr, lls, exprstrs, findShape
from .dataset import GenericDataset, make_title_meta_l0
from .arraydataset import ArrayDataset

try:
    from .mediawrapper_datamodel import Model
except ImportError:
    Model = {'metadata': {}}


from collections.abc import Sequence, Iterable
from collections import OrderedDict
import itertools


class MediaWrapper(ArrayDataset):
    """ A MediaWrapper contains raw, usually binary, data in specific format.

    """

    def __init__(self, data=None,
                 unit=None,
                 description=None,
                 typ_='image/png',
                 source=None,
                 typecode=None,
                 version=None,
                 zInfo=None,
                 alwaysMeta=True,
                 ** kwds):
        """ Initializes media data wrapped in ArrayDataset.

        typ_: www style string that follows `Content-Type: `. Default is `imagw/png`.
        """

        # collect MDPs from args-turned-local-variables.
        metasToBeInstalled = OrderedDict(
            itertools.filterfalse(
                lambda x: x[0] in ('self', '__class__', 'zInfo', 'kwds'),
                locals().items())
        )

        global Model
        if zInfo is None:
            zInfo = Model

        # print('@1 zInfo', id(self.zInfo['metadata']), id(self), id(self.zInfo),
        #      self.zInfo['metadata']['version'], list(metasToBeInstalled.keys()))
        # must be the first line to initiate meta
        super().__init__(zInfo=zInfo, **metasToBeInstalled, **kwds)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """

        # s = OrderedDict(description=self.description, meta=self.meta, data=self.data)  # super(...).__getstate__()
        s = OrderedDict(
            _ATTR_meta=getattr(self, '_meta', None),
            _ATTR_data=getattr(self, 'data', None))

        return s
        # type=self.type,
        # unit=self.unit,
        # typecode=self.typecode,
        # version=self.version,
        # FORMATV=self.FORMATV,
