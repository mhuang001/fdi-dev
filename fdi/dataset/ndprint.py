# -*- coding: utf-8 -*-
from tabulate import tabulate
import logging
import sys
from itertools import zip_longest

if sys.version_info[0] + 0.1 * sys.version_info[1] >= 3.3:
    from collections.abc import Sequence
    seqlist = Sequence
else:
    from .collectionsMockUp import SequenceMockUp as Sequence
    import types
    seqlist = (tuple, list, Sequence, str)
    # ,types.XRangeType, types.BufferType)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def ndprint0(data, trans=True, table=True):
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
    while issubclass(t.__class__, seqlist) and not issubclass(t.__class__, (str, bytes, bytearray, memoryview)):
        context.maxdim += 1
        t = t[0]

    def loop(d, trans):
        # nonlocal s
        # nonlocal maxdim
        # nonlocal dim
        dbg = False
        delta = ''
        padding = ' ' * context.dim * 4
        if issubclass(d.__class__, seqlist) and not issubclass(d.__class__, (str, bytes, bytearray, memoryview)):
            context.dim += 1
            padding = ' ' * context.dim * 4
            if dbg:
                print(padding + 'loop: d=%s dim=%d maxdim=%d %r' %
                      (str(d), context.dim, context.maxdim, trans))
            # if context.dim > context.maxdim:
            #    context.maxdim = context.dim
            try:
                if trans:
                    if context.maxdim == 1:
                        # transpose a 1D matrix
                        d2 = ([x] for x in d)
                        context.maxdim = 2
                        # this 1d trans is one-off
                        trans = False
                    elif (context.maxdim - context.dim == 1):
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
            for x in d2:
                delta += loop(x, trans=trans)
                if context.dim == context.maxdim:
                    # the fastest dim is written horizontally
                    delta += ' '
                elif context.dim + 1 == context.maxdim:
                    # higher dimensions are written vertically
                    delta += '\n'
                elif context.dim + 2 == context.maxdim:
                    # an extra blank line  is added at the end of the 3rd dimension
                    delta += '\n\n'
                else:
                    # dimensions higher than 3 have these marks
                    t = '#=== dimension ' + \
                        str(context.maxdim - context.dim + 1) + '\n'
                    delta += t * (context.maxdim - context.dim + -2) + '\n'
            context.s += delta
            context.dim -= 1
        elif issubclass(d.__class__, (bytes, bytearray, memoryview)):
            delta = d.hex()
        else:
            delta = str(d)
        if dbg:
            print(padding + 'delta %s /delta dim=%d' %
                  (delta, context.dim))
            print(padding + 's ' + context.s + ' /s')
        return delta
    return loop(data, trans)


def ndprint(data, trans=True, **kwds):
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
    while issubclass(t.__class__, seqlist) and not issubclass(t.__class__, (str, bytes, bytearray, memoryview)):
        context.maxdim += 1
        t = t[0]

    def loop(d, trans, **kwds):
        # nonlocal s
        # nonlocal maxdim
        # nonlocal dim
        dbg = False
        delta = ''
        padding = ' ' * context.dim * 4

        if context.maxdim == 0:
            tf = kwds['tablefmt3'] if 'tablefmt3' in kwds else 'plain'
            return tabulate([[d]], tablefmt=tf)
        elif context.maxdim == 1:
            tf = kwds['tablefmt3'] if 'tablefmt3' in kwds else 'plain'
            d2 = [[x] for x in d] if trans else [d]
            return tabulate(d2, tablefmt=tf)
        else:
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
                tf = kwds['tablefmt2'] if 'tablefmt2' in kwds else 'rst'
                hd = kwds['headers'] if 'headers' in kwds else []
                # d2 is a properly transposed 2D array
                # this is where TableDataset prints its tables
                delta += tabulate(d2, headers=hd, tablefmt=tf)
                # an extra blank line  is added at the end of the 3rd dimension
                delta += '\n\n'
            else:
                for x in d2:
                    delta += loop(x, trans=trans, **kwds)
                    # dimensions higher than 3 have these marks
                    t = '#=== dimension ' + \
                        str(context.maxdim - context.dim + 1) + '\n'
                    delta += t * (context.maxdim - context.dim + -2) + '\n'
            context.s += delta
            context.dim -= 1
        if dbg:
            print(padding + 'delta %s /delta dim=%d' %
                  (delta, context.dim))
            print(padding + 's ' + context.s + ' /s')
        return delta
    return loop(data, trans, **kwds)
