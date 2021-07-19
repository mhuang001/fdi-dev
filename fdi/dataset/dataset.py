# -*- coding: utf-8 -*-

from ..utils.common import mstr, bstr
from .listener import MetaDataListener
from .serializable import Serializable
from .typed import Typed
from .odict import ODict
from .attributable import Attributable
from .abstractcomposite import AbstractComposite
from .datawrapper import DataContainer, DataWrapper
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable


from collections import OrderedDict
import logging
import sys

if sys.version_info[0] + 0.1 * sys.version_info[1] >= 3.3:
    PY33 = True
    from collections.abc import Container, Sequence, Mapping
    seqlist = Sequence
    maplist = Mapping
else:
    assert 0, 'python 3'
    PY33 = False
    from .collectionsMockUp import ContainerMockUp as Container
    from .collectionsMockUp import SequenceMockUp as Sequence
    from .collectionsMockUp import MappingMockUp as Mapping
    seqlist = (tuple, list, Sequence, str)
    # ,types.XRangeType, types.BufferType)
    maplist = (dict, Mapping)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

# from .composite import


class Dataset(Attributable, DataContainer, Serializable, MetaDataListener):
    """ Attributable and annotatable information data container
    that can be be part of a Product.

    developer notes:
    The intent is that developers do not derive from this interface

    directly. Instead, they should inherit from one of the generic
    datasets that this package provides:

    mh: GenericDataset,
    ArrayDataset.
    TableDataset or
    CompositeDataset.
    """

    def __init__(self, **kwds):
        """

        """
        super(Dataset, self).__init__(**kwds)

    def accept(self, visitor):
        """ Hook for adding functionality to object
        through visitor pattern."""
        visitor.visit(self)

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """

        s = OrderedDict(description=self.description,
                        meta=self._meta,
                        data=self.data,
                        _STID=self._STID)  # TODO
        return s


class GenericDataset(Dataset, Typed, DataWrapper):
    """ mh: Contains one typed data item with a unit and a typecode.
    """

    def __init__(self,                 **kwds):
        """
        """
        super(GenericDataset, self).__init__(
            **kwds)  # initialize data, meta, unit

    def __iter__(self):
        for x in self.getData():
            yield x

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 param_widths=None, width=0, matprint=None, trans=True, **kwds):
        """ matprint: an external matrix print function
        trans: print 2D matrix transposed. default is True.
        """
        cn = self.__class__.__name__
        if level > 1:
            return cn + \
                '{ %s, description = "%s", meta = %s }' % \
                (str(self.data), str(self.description), self.meta.toString(
                    tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                    level=level, width=width, param_widths=param_widths,
                    matprint=matprint, trans=trans, **kwds))

        s = '=== %s (%s) ===\n' % (cn, self.description if hasattr(
            self, 'descripion') else '')
        s += mstr(self.__getstate__(), level=level,
                  tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                  excpt=['description'], **kwds)

        d = cn + '-dataset =\n'
        d += bstr(self.data, level=level,
                  tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                  **kwds) if matprint is None else \
            matprint(self.data, level=level, trans=False, headers=[], tablefmt2='plain',
                     **kwds)
        return s + '\n' + d + '\n'


class CompositeDataset(AbstractComposite, Dataset):
    """  An CompositeDataset is a Dataset that contains zero or more
    named Datasets. It allows to build arbitrary complex dataset
    structures.

    It also defines the iteration ordering of its children, which is
    the order in which the children were inserted into this dataset.
    """

    def __init__(self, **kwds):
        """
        """
        super(CompositeDataset, self).__init__(
            **kwds)  # initialize _sets, meta, unit

    def __getstate__(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           meta=self.meta,
                           _sets=self._sets,
                           _STID=self._STID)
