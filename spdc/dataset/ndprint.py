# -*- coding: utf-8 -*-
from collections.abc import Sequence

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


def ndprint(data, trans=True):
    """ makes a formated string of an N-dimensional array for printing.
    """
    if data is None:
        return 'None'
    dim = 0
    maxdim = 0
    s = ''

    t = data
    while issubclass(t.__class__, Sequence):
        maxdim += 1
        t = t[0]

    # 1D to transpose
    if maxdim == 1 and trans:
        data = [[x] for x in data]
        maxdim = 2
        trans = False

    def loop(d, trans):
        nonlocal s
        nonlocal maxdim
        nonlocal dim
        delta = ''

        if issubclass(d.__class__, Sequence):
            dim += 1
            # if dim > maxdim:
            #    maxdim = dim
            try:
                # transpose if wanted and at 3-D kevek
                d2 = list(zip(*d)) if trans and (maxdim - dim == 1) else d
            except Exception as e:
                msg = 'bad tabledataset for printing. ' + str(e)
                logger.error(msg)
                raise ValueError(msg)
            for x in d2:
                delta += loop(x, trans=trans)
                if dim == maxdim:
                    delta += ' '
                elif dim + 1 == maxdim:
                    delta += '\n'
                elif dim + 2 == maxdim:
                    delta += '\n\n'
                else:
                    t = '#=== dimension ' + str(maxdim - dim + 1) + '\n'
                    delta += t * (maxdim - dim + -2) + '\n'
            s += delta
            dim -= 1
        elif issubclass(d.__class__, (bytes, bytearray, memoryview)):
            delta = d.hex()
        else:
            delta = str(d)
        return delta
    return loop(data, trans)
