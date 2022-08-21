# -*- coding: utf-8 -*-

import jsonpath_ng.ext as jex

from functools import lru_cache
import itertools
from collections import UserDict


JEXP = jex.parse('$..*')


def flatten_compact(roots, num=False, style='short', sep='.', path_list=False):
    """ Colapse datapaths of elements of an object.

    Duplicated paths will only have the last one. For example::

    for n, c in {'group1.val': a10['col1'], 'group1.err': a10['col2'],
                 'no-group.val': a10['col1'],
                 'group2.val': a10['col1'], 'group2.err': a10['col2'],
                 'group2.seq': a10['col2'],
                 'group2.wgt': Column(data=['', 0.32, -9876543210], unit='g'),
                 }.items():
        v.addColumn(n, c)

will make one-level datapath::

    col1
    col2
    group1.val
    group1.err
    no-group.val
    group2.val
    group2.err
    group2.seq
    group2.wgt

shown in a tree::

    |__ 'col1'                                     <Column> (3,)
    |__ 'col2'                                     <Column> (3,)
    |__ 'group1.val'                               <Column> (3,)
    |__ 'group1.err'                               <Column> (3,)
    |__ 'no-group.val'                             <Column> (3,)
    |__ 'group2.val'                               <Column> (3,)
    |__ 'group2.err'                               <Column> (3,)
    |__ 'group2.seq'                               <Column> (3,)
    \__ 'group2.wgt'                               <Column> (3,)


Flatten_compact  ```print('\n'self.join(flatten_compact([v]).keys()))```::

    col1
    col2
    g.val
    g.err
    n.val
    g.seq
    g.wgt

The 'group' part  look good in a table header::

    +-----------------+-----------------+--------+----------------------------------------+
    |                 |     group1      |  no-   |                 group2                 |
    |                 |                 | group  |                                        |
    +--------+--------+--------+--------+--------+--------+--------+--------+-------------+
    |   col1 |   col2 |    val |    err |    val |    val |    err |    seq | wgt         |
    |   (eV) |  (cnt) |   (eV) |  (cnt) |   (eV) |   (eV) |  (cnt) |  (cnt) | (g)         |
    +========+========+========+========+========+========+========+========+=============+
    |    1   |    0   |    1   |    0   |    1   |    1   |    0   |    0   |             |
    +--------+--------+--------+--------+--------+--------+--------+--------+-------------+
    |    4.4 |   43.2 |    4.4 |   43.2 |    4.4 |    4.4 |   43.2 |   43.2 | 0.32        |
    +--------+--------+--------+--------+--------+--------+--------+--------+-------------+
    | 5400   | 2000   | 5400   | 2000   | 5400   | 5400   | 2000   | 2000   | -9876543210 |
    +--------+--------+--------+--------+--------+--------+--------+--------+-------------+


    :roots: where. A list of maps.
    :num: preceed keys with sequence numbers.
    :style: for keys, `short`: use shortened path e.g. ```abc.def.hgi``` ```a.d.hgi```. `last2`: use the right-most 2 segments, `full` for untrated paths, anything else to use only the last one.
    :sep: separater used in output. Default is '.'.
    :path_list: a list of path segments in place of value. Defalut `False`.
    :return: dict(flatten_compact_path:(list of path|val)
    """
    res = dict()

    for root in roots:
        match = JEXP.find(root)
        n = 0
        hdrs = dict()

        for node in match:
            if not issubclass(node.value.__class__, (dict, list, UserDict)):
                # abc/def/ghi ->a.d.ghi
                fp = str(node.full_path).split('.')
                npre = (str(n)+'_') if num else ''
                if style == 'short':
                    # first char
                    key = ''.join((x[:1] + sep) for x in fp[:-1])
                elif style == 'full':
                    key = ''.join((x + sep) for x in fp[:-1])
                elif style == 'last2':
                    # last two segments
                    key = (fp[-2] + sep) if len(fp) > 1 else ''
                else:
                    key = ''
                hdrs[npre + key + fp[-1]] = fp if path_list else node.value
                n += 1
        res.update(hdrs)
    return res


@ lru_cache(maxsize=128)
def jexp(expr, *args, **kwds):
    return jex.parse(expr, *args, **kwds)


def getCacheInfo():
    info = {}
    for i in [jexp]:
        info[i] = i.cache_info()

    return info


def jsonPath(data, expr, val='simple', sep='/', indent=None, *args, **kwds):
    """ Make a JSONPath query on the data.

    :expr: JSONPath expression. Ref 'jsonpath_ng'

    :sep: '' or `None` for keeping `jsonpath_ng` format (e.g. `a.b.[3].d`; other string for substituting '.' to the given string, with '[' and ']' removed. Default is '/'.
    :val: 'context' for returning the `list` of `DatumInContext` of `find`; 'simple' (default) for list of simple types of values and summarizing `list` and `dict` values; other for a list of un-treated `DatumInContext.value`s; 'paths' for a list of paths only.
    :indent: for `json.dumps`.
    Returns
    -------
    If `val` is ```context```, return  the `list` of `DatumInContext` of `jsonpath_ng.ext.parse().find()`.
    Else return a `list` of `full_path`-`value` pairs from the output of `find().`
    * If `val` is ```simple```, only node values of simple types are kept, `list` and `dict` types will show as '<list> length' and '<dict> [keys [... [length]]]', respectively.
    * If `val` is ```full```, the values of returned `list`s are  un-treated `DatumInContext.value`s.
    """

    jsonpath_expression = jexp(expr, *args, **kwds)
    match = jsonpath_expression.find(data)
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
        if val == 'paths':
            res.append(key)
            continue
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
            raise ValueError(
                'Invalid output type for jsonPath: %s' % str(val))
        res.append((key, value))
    return res
