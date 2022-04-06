# -*- coding: utf-8 -*-

from ..dataset.arraydataset import ArrayDataset, Column
from ..dataset.tabledataset import TableDataset
from ..dataset.datatypes import Vector
from ..dataset.finetime import FineTime
from ..dataset.metadata import Parameter
from ..dataset.attributable import Reserved_Property_Names
from .common import bstr, lls

from itertools import chain, islice, repeat
import logging
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from pprint import pprint
import array
import time
import io
import statistics

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


"""
Aaron Hall
https://stackoverflow.com/a/59109706
"""

SIMPLE_TYPES = (int, float, complex, str, bytes, bool, type(None),
                FineTime, Vector)
# prefix components:
PREFIXES = {'line': (
    # space
    '    ',
    # branch
    '│   ',
    # pointers
    # tee =
    '├── ',
    # last
    '└── '
),
    'ascii': (
    # space
    '    ',
    # branch
    '|   ',
    # pointers
    # tee =
    '|__ ',
    # last
    '\__ '
), }


def tree(data_object, level=0, style='line', prefix='', seen=None):
    """A recursive generator, given an object object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters.

    :style: can be ```line``` pr ```ascii```.
    """

    space, branch, tee, last = PREFIXES[style]
    if seen is None:
        seen = []
    elif id(data_object) in seen:
        return
    seen.append(id(data_object))
    # data is a Sequence
    if issubclass(data_object.__class__, Sequence):
        contents = list((n, v) for n, v in enumerate(data_object)
                        if not issubclass(v.__class__, SIMPLE_TYPES))
        if len(contents) == 0:
            return
    elif hasattr(data_object, '__getstate__'):
        # state variables. Change names "_ATTR_xxx" to "xxx". Filter out Parameter
        contents = list(((n[6:] if n.startswith('_ATTR_') else n), v)
                        for n, v in data_object.__getstate__().items() if
                        level > 0 or not issubclass(v.__class__, Parameter))
    elif issubclass(data_object.__class__, Mapping):
        # data is MutableMapping of simple values
        contents = list((n, v) for n, v in
                        data_object.items() if
                        not (n.startswith('_') or n in Reserved_Property_Names
                             ))
    elif hasattr(data_object, '__dict__'):
        # or properties
        contents = list((n, v) for n, v in
                        vars(data_object).items() if
                        not (n.startswith('_') or n in Reserved_Property_Names
                             ))
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, name_value in zip(pointers, contents):
        v = name_value[1]
        vc = v.__class__
        shp = (' %s' % str(v.shape)) if hasattr(v, 'shape') else ''
        typ = '%s' % (str(v.type) if hasattr(v, 'type') else vc.__name__)
        # format output line
        ts = '<%s>%s' % (typ, shp)
        line = prefix + pointer + str(name_value[0])
        yield '%s%s%s' % (line, ' ' * max(1, 60-len(line)-len(ts)), ts)

        if issubclass(vc, (str, bytes)) or \
           issubclass(vc, (ArrayDataset)) and hasattr(v, 'typecode'):
            pass
        elif issubclass(vc, (Mapping, Sequence)) or hasattr(v, '__dict__'):
            # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from tree(v, level=level, style=style, prefix=prefix+extension, seen=seen)
