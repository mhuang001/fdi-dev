# -*- coding: utf-8 -*-

from ..dataset.arraydataset import ArrayDataset, Column
from ..dataset.tabledataset import TableDataset
from ..dataset.attributable import Reserved_Property_Names

from itertools import chain, islice, repeat
import logging
from collections import OrderedDict
from collections.abc import MutableMapping, Sequence
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


# prefix components:
space = '    '
branch = '│   '
# pointers:
tee = '├── '
last = '└── '


def tree(data_path, prefix='', seen=None):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """
    print(data_path.__class__)
    # __import__('pdb').set_trace()

    if seen is None:
        seen = []
    elif id(data_path) in seen:
        return
    seen.append(id(data_path))
    if issubclass(data_path.__class__, Sequence):
        contents = list((n, v) for n, v in enumerate(data_path)
                        if not issubclass(v.__class__, SIMPLE_TYPES))
        if len(contents) == 0:
            return
    else:
        contents = []
        # properties
        if hasattr(data_path, '__dict__'):
            contents += list((n, v) for n, v in
                             vars(data_path).items() if
                             not (n.startswith('_') or n in Reserved_Property_Names))
        # state variables
        if hasattr(data_path, '__getstate__'):
            contents += list(((n[6:] if n.startswith('_ATTR_') else n), v)
                             for n, v in data_path.__getstate__().items())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, name_value in zip(pointers, contents):
        v = name_value[1]
        vc = v.__class__
        shp = '%s' % (str(v.shape) if hasattr(v, 'shape') else '')
        typ = '%s' % (str(v.type) if hasattr(v, 'type') else vc.__name__)
        yield prefix + pointer + '%s <%s> %s' % (name_value[0], typ, shp)

        if issubclass(vc, (str, bytes)) or \
           issubclass(vc, (ArrayDataset)) and hasattr(v, 'typecode'):
            pass
        elif issubclass(vc, (MutableMapping, Sequence)):
            # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from tree(v, prefix=prefix+extension, seen=seen)
