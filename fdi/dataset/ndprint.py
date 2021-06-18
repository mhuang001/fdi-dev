# -*- coding: utf-8 -*-

from ..utils.common import bstr

from tabulate import tabulate
import logging
import sys
from itertools import zip_longest

if sys.version_info[0] + 0.1 * sys.version_info[1] >= 3.3:
    from collections.abc import ValuesView, KeysView, Sequence

    seqlist = (ValuesView, KeysView, Sequence)
else:
    from .collectionsMockUp import SequenceMockUp as Sequence
    import types
    seqlist = (tuple, list, Sequence, str)
    # ,types.XRangeType, types.BufferType)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def ndprint(data, trans=True, maxElem=50, **kwds):
    """ makes a formated string of an N-dimensional array for printing.
    The fastest changing index is the innerest list. E.g.
    A 2 by 3 matrix is [[1,2],[3,4],[5,6]] written as
    1 2
    3 4
    5 6
    But if the matrix is a table, the cells in a column change the fastest,
    and the columns are written vertically. So to print a matrix as a table,
    whose columns are the innerest list, set trans = True (default) then
    the matrix needs to be printed transposed:
    1 3 5
    2 4 6
    """
    if data is None:
        return 'None'
    try:
        if len(data) == 0:
            return str(data)
    except TypeError:
        pass

    # dim, maxdim, and s are to be used as nonlocal variables in run()
    # to overcome python2's lack of nonlocal type this method is usded
    # https://stackoverflow.com/a/28433571
    class context:
        # current dimension as we descend.
        # dim=1 is the slowest changing (outer-most) dimension.
        # dim=maxdim is the fastest changing (inner-most) dimension.
        dim = 0
        # dimension of input data
        maxdim = 0
        # output string
        s = ''

    # print("start " + str(data) + ' ' + str(trans))
    t = data
    try:
        while not issubclass(t.__class__, (str, bytes, bytearray, memoryview)):
            tmp = list(t)
            # if we reach this line, tmp has a valid value
            #t[0] = tmp
            t = tmp[0]
            context.maxdim += 1
    except TypeError as e:
        # print(e)
        pass

    def loop(data, trans, **kwds):
        # nonlocal s
        # nonlocal maxdim
        # nonlocal dim

        dbg = False
        delta = ''
        padding = ' ' * context.dim * 4

        if context.maxdim == 0:
            tf = kwds['tablefmt3'] if 'tablefmt3' in kwds else 'plain'
            return tabulate([[bstr(data)]], tablefmt=tf)
        elif context.maxdim == 1:
            tf = kwds['tablefmt3'] if 'tablefmt3' in kwds else 'plain'
            d2 = [[bstr(x)] for x in data] if trans else [[bstr(x)
                                                           for x in data]]
            return tabulate(d2, tablefmt=tf)
        else:
            d = list(data)
            context.dim += 1
            padding = ' ' * context.dim * 4
            if dbg:
                print(padding + 'loop: d=%s dim=%d maxdim=%d %r' %
                      (str(d), context.dim, context.maxdim, trans))
            # if context.dim > context.maxdim:
            #    context.maxdim = context.dim
            try:
                if trans:
                    if context.maxdim - context.dim == 1:
                        # transpose using list(zip) technique if maxdim > 1
                        d2 = list(zip_longest(*d, fillvalue='-'))
                    else:
                        d2 = d
                else:
                    d2 = d
            except Exception as e:
                msg = 'bad tabledataset for printing. ' + str(e)
                logger.error(msg)
                raise ValueError(msg)
            if dbg:
                print(padding + 'd2 %s' % str(d2))
            if context.dim + 1 == context.maxdim:
                tf = kwds['tablefmt2'] if 'tablefmt2' in kwds else 'simple'
                hd = kwds['headers'] if 'headers' in kwds else []
                # d2 is a properly transposed 2D array
                dlimited = [x[:maxElem] for x in d2[:maxElem]]
                # this is where TableDataset prints its tables
                delta += tabulate(dlimited, headers=hd, tablefmt=tf)
                # an extra blank line  is added at the end of the 3rd dimension
                delta += '\n\n'
            else:
                nelem = 0
                for x in d2:
                    delta += loop(x, trans=trans, **kwds)
                    # dimensions higher than 3 have these marks
                    t = '#=== dimension ' + \
                        str(context.maxdim - context.dim + 1) + '\n'
                    delta += t * (context.maxdim - context.dim + -2) + '\n'
                    nelem += 1
                    if nelem >= maxElem:
                        break
            context.s += delta
            context.dim -= 1
        if dbg:
            print(padding + 'delta %s /delta dim=%d' %
                  (delta, context.dim))
            print(padding + 's ' + context.s + ' /s')
        return delta
    ret = loop(data, trans, **kwds)
    return ret
