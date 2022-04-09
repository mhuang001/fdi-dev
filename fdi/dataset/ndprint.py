# -*- coding: utf-8 -*-

from ..utils.common import bstr, wls
from .metadata import tabulate

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


def padstr(s, w, just='left', pad=' '):

    if just == 'center':
        return s.center(w, pad)
    elif just == 'right':
        return s.rjust(w, pad)
    else:
        return s.ljust(w, pad)


def ndprint(data, trans=True, mdim=None, maxElem=sys.maxsize, tablefmt3='plain', **kwds):
    """ makes a formated string of an N-dimensional array for printing.
    The fastest changing index is the innerest list. E.g.
    A 2 by 3 matrix is [[1,2],[3,4],[5,6]] written as::

    1 2
    3 4
    5 6

But if the matrix is a table, the cells in a column change the fastest,
    and the columns are written vertically. So to print a matrix as a table,
    whose columns are the innerest list, set trans = True (default) then
    the matrix needs to be printed transposed::

    1 3 5
    2 4 6

    Parameters
    ----------
    :tablefmt3: control 2d array printing. Default 'plain'.
    :dim: Max dimension of the data. If given `None` guess will be made. This helps to disambiguit if there are iterables in the elements. DEfault ```None```.

    Returns
    -------
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
    if mdim is not None:
        context.maxdim = mdim
    else:
        t = data
        try:
            while not issubclass(t.__class__, (str, bytes, bytearray, memoryview)):
                tmp = list(t)
                # if we reach this line, tmp has a valid value
                if len(tmp) == 0:
                    break
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
            tf = tablefmt3
            return tabulate.tabulate([[bstr(data)]], tablefmt=tf)
        elif context.maxdim == 1:
            tf = tablefmt3
            d2 = [[bstr(x)] for x in data] if trans else [[bstr(x)
                                                           for x in data]]
            return tabulate.tabulate(d2, tablefmt=tf)
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
                raise
            if dbg:
                print(padding + 'd2 %s' % str(d2))
            if context.dim + 1 == context.maxdim:
                tf = kwds.get('tablefmt2', 'simple')
                hd = kwds.get('headers', [])
                # d2 is a properly transposed 2D array
                dlimited = [x[:maxElem] for x in d2[:maxElem]]

                # this is where TableDataset prints its tables
                # if tf in ['simple', 'rst', 'grid'] and
                if len(hd) > 1 and issubclass(hd[0].__class__, tuple):
                    _tab = tabulate.tabulate(
                        dlimited, headers=list(h[1] for h in hd), tablefmt=tf)
                    minp = 0  # tabulate.MIN_PADDING
                    #print(tabulate.EVENTUAL_WIDTHS, tabulate.MIN_PADDING)
                    # first rst cell cannot be blank
                    if tf == 'rst':
                        if hd[0][0] == '':
                            hd[0] = ('..', hd[0][1])
                    last = hd[0][0]

                    # width of each group
                    w = tabulate.EVENTUAL_WIDTHS[0]
                    # group strings and widths
                    hd2, w2 = [], []

                    for i in range(1, len(hd)):
                        this = hd[i][0]
                        # column width
                        wc = tabulate.EVENTUAL_WIDTHS[i]
                        # skip thid for plain
                        if this == last and tf != 'plain':
                            # extra 2 for every internal gaps grouped
                            w += wc + 2 + \
                                (1 if tf in [
                                    'grid', 'fancy_grid', 'orgtbl', 'psql'] else 0)
                        else:
                            # padstr(last, w, just='center'))
                            # if tf == 'simple' else last)
                            hd2.append(wls(last, w))
                            w2.append(w)
                            w = wc
                        last = this
                    hd2.append(padstr(last, w, just='center'))
                    w2.append(w)
                    saveb = tabulate.PRESERVE_WHITESPACE
                    tabulate.PRESERVE_WHITESPACE = True

                    dummy = [['X'*n for n in w2]]
                    if tf in ['simple', 'plain', 'orgtbl']:
                        _header = tabulate.tabulate(dummy, headers=hd2,
                                                    stralign='center',
                                                    tablefmt=tf)
                        _header = _header.rsplit('\n', 1)[0]
                        delta += _header + '\n' + _tab
                    elif tf in ['rst']:
                        _header = tabulate.tabulate(dummy, headers=hd2,
                                                    stralign='center',
                                                    tablefmt='simple')
                        par = _tab.split('\n', 1)
                        par.insert(1, _header.rsplit('\n', 1)[0])
                        _tab = '\n'.join(par)
                        delta += '\n' + _tab
                    elif tf in ['grid', 'fancy_grid', 'psql']:
                        _header = tabulate.tabulate(dummy, headers=hd2,
                                                    stralign='center',
                                                    tablefmt=tf)
                        _header = _header.rsplit('\n', 3)[0]
                        delta += _header + '\n' + _tab
                    elif tf in ['x']:
                        _header = tabulate.tabulate(dummy, headers=hd2,
                                                    stralign='center',
                                                    tablefmt=tf)
                        _header = _header.rsplit('\n', 2)[0]
                        delta += _header + '\n' + _tab
                    else:
                        _header = tabulate.tabulate(dummy, headers=hd2,
                                                    stralign='center',
                                                    tablefmt=tf)
                        _header = _header  # .rsplit('\n', 3)[0]
                        delta += _header + _tab

                    tabulate.PRESERVE_WHITESPACE = saveb

                else:
                    if len(hd):
                        _header = [h[1] for h in hd] if issubclass(
                            hd[0].__class__, tuple) else hd
                    else:
                        _header = hd
                    delta += tabulate.tabulate(dlimited,
                                               headers=_header, tablefmt=tf)
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
