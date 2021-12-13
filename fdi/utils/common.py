# -*- coding: utf-8 -*-

from .masked import masked
from .ydump import ydump
from .. import dataset

import hashlib
import array
import traceback
import pprint
import copy
import pwd
import logging
from functools import lru_cache
from itertools import zip_longest, accumulate
from collections.abc import Sequence, Mapping
import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False


# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def str2md5(string):
    return hashlib.md5(string.encode('utf8')).hexdigest()


def trbk(e):
    """ trace back
    """
    ls = [x for x in traceback.extract_tb(e.__traceback__).format()] if hasattr(
        e, '__traceback__') else ['']
    return ' '.join(ls) + ' ' + \
        (e.child_traceback if hasattr(e, 'child_traceback') else '')


def trbk2(e):
    tb = traceback.TracebackException.from_exception(e)
    return ''.join(tb.stack.format())


def bstr(x, length=0, tostr=True, quote="'", level=0,
         tablefmt='rst', tablefmt1='simple', tablefmt2='rst',
         width=0, heavy=True, yaml=False,
         **kwds):
    """ returns the best string representation.
    if the object is a string, return single-quoted; if has toString(), use it; else returns str(). Length limited by lls(lls)
    """

    s = issubclass(x.__class__, str) if PY3 else issubclass(
        x.__class__, (str, unicode))

    if s:
        r = quote + x + quote
    elif tostr and hasattr(x, 'toString') and not issubclass(x.__class__, type):
        r = x.toString(level=level,
                       tablefmt=tablefmt, tablefmt1=tablefmt1,
                       tablefmt2=tablefmt2, width=width, heavy=heavy,
                       **kwds)
    elif issubclass(x.__class__, (bytes, bytearray, memoryview)):
        r = x.hex()
    else:
        r = ydump(x) if yaml else str(x)
    return lls(r, length=length)


def lls(s, length=80):
    """ length-limited string.

    Returns the str if len <= length or length <=3. Returns 'begin...end' if not.
    """
    st = str(s)
    if len(st) <= length or length <= 3:
        return st
    else:
        l = int(0.8*(length-3))
        return '%s...%s' % (st[:l], st[3 + l - length:])


""" https://stackoverflow.com/a/2718268
LHan = [[0x2E80, 0x2E99],    # Han # So  [26] CJK RADICAL REPEAT, CJK RADICAL RAP
        [0x2E9B, 0x2EF3],    # Han # So  [89] CJK RADICAL CHOKE, CJK RADICAL C-SIMPLIFIED TURTLE
        [0x2F00, 0x2FD5],    # Han # So [214] KANGXI RADICAL ONE, KANGXI RADICAL FLUTE
        0x3005,              # Han # Lm       IDEOGRAPHIC ITERATION MARK
        0x3007,              # Han # Nl       IDEOGRAPHIC NUMBER ZERO
        [0x3021, 0x3029],    # Han # Nl   [9] HANGZHOU NUMERAL ONE, HANGZHOU NUMERAL NINE
        [0x3038, 0x303A],    # Han # Nl   [3] HANGZHOU NUMERAL TEN, HANGZHOU NUMERAL THIRTY
        0x303B,              # Han # Lm       VERTICAL IDEOGRAPHIC ITERATION MARK
        [0x3400, 0x4DB5],    # Han # Lo [6582] CJK UNIFIED IDEOGRAPH-3400, CJK UNIFIED IDEOGRAPH-4DB5
        [0x4E00, 0x9FC3],    # Han # Lo [20932] CJK UNIFIED IDEOGRAPH-4E00, CJK UNIFIED IDEOGRAPH-9FC3
        [0xF900, 0xFA2D],    # Han # Lo [302] CJK COMPATIBILITY IDEOGRAPH-F900, CJK COMPATIBILITY IDEOGRAPH-FA2D
        [0xFA30, 0xFA6A],    # Han # Lo  [59] CJK COMPATIBILITY IDEOGRAPH-FA30, CJK COMPATIBILITY IDEOGRAPH-FA6A
        [0xFA70, 0xFAD9],    # Han # Lo [106] CJK COMPATIBILITY IDEOGRAPH-FA70, CJK COMPATIBILITY IDEOGRAPH-FAD9
        [0x20000, 0x2A6D6],  # Han # Lo [42711] CJK UNIFIED IDEOGRAPH-20000, CJK UNIFIED IDEOGRAPH-2A6D6
        [0x2F800, 0x2FA1D]]  # Han # Lo [542] CJK COMPATIBILITY IDEOGRAPH-2F800, CJK COMPATIBILITY IDEOGRAPH-2FA1D
"""


@lru_cache(maxsize=128)
def wcw(char):
    # cached width function
    from ..dataset.metadata import wcwidth
    return wcwidth.wcwidth(char)


def wls(st, width=15, fill=None, unprintable='#'):
    """ generates a string comtaining width-limited strings separated with '\n'.

    Identifies Line-breaks with `str.splitlines` https://docs.python.org/3.6/library/stdtypes.html#str.splitlines
    Removes trailing line-breaks.

    :st: input string.
    :width: if > 0  returns the str with '\n' inserted every width chars. Or else return the input ``st``. Default is 15. A CJK characters occupies 2 in widths.
    :unprintable: substitute unprintable characters with is. default is '#'.
    """
    if width <= 0 or len(st) == 0:
        return st
    line = []
    for s in st.splitlines():
        lens = len(s)
        # starting index for current line based on the last line
        lasti = 0
        # display length starting from the beginning of the last line.
        l = 0
        for i, c in enumerate(s):
            w = wcw(c)
            l0 = l
            if w == -1:
                # change unprintable
                # ref https://wcwidth.readthedocs.io/en/latest/api.html
                c = unprintable
                w = wcw(c)
                l += w
            else:
                l += w
            #print(i, c, l, lasti, s)
            if l == width:
                line.append(c)
                line.append('\n')
                lasti, l = i+1, 0
            elif l > width:
                if width < 2:
                    # print wide characters even they are too wide for width==1
                    line.append(c)
                    line.append('\n')
                    lasti = i+1
                    l = 0
                else:
                    # set line pointer to this char
                    if fill:
                        line.append((width-l0) * fill)
                    line.append('\n')
                    line.append(c)
                    lasti = i
                    l = w
            else:
                line.append(c)
        if len(line) == 0 or line[-1] != '\n':
            if fill:
                line.append((width-l) * fill)
            line.append('\n')
        # print(line)
    return ''.join(line[:-1])


def mstr(obj, level=0, width=1, excpt=None, indent=4, depth=0,
         tablefmt='rst', tablefmt1='simple', tablefmt2='rst',
         **kwds):
    """ Makes a presentation string at a detail level.

    'tablefmt' is needed to be passed in recursive calls under some conditions it is used.
    """
    excp = ['_STID', 'data', '_sets']
    if excpt:
        excp.extend(excpt)
    ind = ' '*indent

    if level == 0:
        if not hasattr(obj, 'items'):
            return bstr(obj, level=level, **kwds)
        if issubclass(obj.__class__, dataset.metadata.MetaData):
            return obj.toString(level=level,
                                tablefmt=tablefmt, tablefmt1=tablefmt1,
                                tablefmt2=tablefmt2,
                                **kwds)
        s = ['%s= {%s}' % (mstr(k, level=level, excpt=excp,
                                indent=indent, depth=depth+1, quote='',
                                tablefmt=tablefmt, tablefmt1=tablefmt1,
                                tablefmt2=tablefmt2,
                                **kwds),
                           mstr(v, level=level, excpt=excp,
                                indent=indent, depth=depth+1,
                                tablefmt=tablefmt, tablefmt1=tablefmt1,
                                tablefmt2=tablefmt2,
                                **kwds))
             for k, v in obj.items() if k not in excp]
        if len(''.join(s)) < 70:
            sep = ', '
        else:
            sep = ',\n' + ind*depth
            if depth > 0:
                s[0] = '\n' + ind*depth + s[0]
        return sep.join(s)
    elif level == 1:
        if not hasattr(obj, 'items'):
            # returns value of value if possible. limit to 40 char
            obj = obj.getValue() if hasattr(obj, 'getValue') else obj
            return bstr(obj, length=80, level=level, **kwds)
        if issubclass(obj.__class__, dataset.metadata.MetaData):
            return obj.toString(level=level, **kwds) + '\n'
        else:
            pat = '%s= {%s}' if depth == 0 else '%s= %s'
            data = obj

        s = [pat % (mstr(k, level=level, excpt=excp,
                         tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                         indent=indent, depth=depth+1, quote='', **kwds),
                    mstr(v, level=level, excpt=excp,
                         tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                         indent=indent, depth=depth+1, **kwds))
             for k, v in data.items() if k not in excp]
        sep = ',\n' if depth == 0 else ', '
        return sep.join(s)
    else:
        if not hasattr(obj, 'items'):
            return mstr(obj, level=1,
                        tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                        **kwds)
        s = ['%s' % (mstr(k, level=level, excpt=excp, quote='',
                          tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                          **kwds))
             for k, v in obj.items() if k not in excp]
        return ', '.join(s)


def binhexstring(val, typ_, width=0, v=None, p=None, level=0, **kwds):
    """ returns val in binary, hex, or string according to typ_.

    val; list of validity descriptor entries.
    typ_: parameter type in ``DataTypes``.
    """
    if typ_ == 'hex':
        func = hex
    elif typ_ == 'binary':
        func = bin
    else:
        func = str
    breakline = True
    if not issubclass(val.__class__, list):
        return func(val)
    if v == '_valid' and p:
        validity = p.validate(val)

    lst = []
    # number of bits of mask
    highest = 0
    masks = []
    for t in val:
        if v == '_valid':
            # val is for '_valid' [[], [], []..]
            rule, name = t[0], t[1]
            if issubclass(rule.__class__, (tuple, list)):
                # range or binary with mask. (1,95) (0B011, 011)
                if rule[0] < rule[1]:
                    # not binary masked
                    seg = "(%s, %s): %s" % (func(rule[0]), func(rule[1]), name)
                else:
                    # binary masked. validity is a list of tuple/lists
                    # validity[mask] is (val, state, mask height, mask width)
                    mask, valid_val = rule[0], rule[1]
                    masked_val, mask_height, mask_width = masked(
                        p._value, mask)
                    masks.append(
                        (mask, format(valid_val, '#0%db' % (mask_width+2)), name))
                    if mask_height > highest:
                        highest = mask_height
                    seg = None
            elif issubclass(rule.__class__, str):
                seg = "'%s': %s" % (rule, name)
            else:
                seg = "%s: %s" % (func(rule), name)
            if seg:
                lst.append(seg)
        else:
            # val is a 1+ dimension array
            lst.append(lls(t, 19))
            if len(lst) > 8:
                lst.append('... tot. %d in dim1' % len(val))
                break
    if highest > 0:
        # like '110000: 0b10 name1', '001111: 0b0110 name2']
        fmt = '0%db' % (highest)
        lst += [format(i[0], fmt) + ' ' + i[1] + ': ' + i[2] for i in masks]

    if width and breakline:
        return '\n'.join(lst)
    else:
        return '[%s]' % ', '.join(lst)


""" Must be lowercased """
Ommitted_Valid_Rule_Names = ['valid', 'default', '', 'range']


def attrstr(p, v, missingval='', ftime=False, state=True, width=1, **kwds):
    """
    generic string representation of an attribute of a parameter or dataset.

    p: parameter object.
    v: name of parameter attribute. '_valid', '_type', '_default', '_value' (for Parameter) or '_data' (dataset)
    missingval: string used when the parameter does not have the attribute.
    ftime: True means that attribute value will be FineTime if _type is 'finetime'.
    state: The state validity of the parameter is returned in place of value, if the state is not in Ommitted_Valid_Rule_Names -- 'valid', 'range', '' or 'default'.
    """

    ts = getattr(p, '_type') if hasattr(p, '_type') else missingval
    if ts is None:
        ts = 'None'

    # try:
    # except (KeyError, AttributeError):
    #    return missingval
    if not hasattr(p, v):
        return missingval

    val = getattr(p, v)
    if val is None:
        return 'None'
    if v in ['_type', 'description', '_unit', '_typecode']:
        return val
    if v == '_default':
        if ts.startswith('finetime'):
            vs = val.toString(width=width, **kwds)
        else:
            # for default and value/data, print list horizontally
            width = 0
            vs = binhexstring(val, ts, width=width, **kwds)
    elif v == '_valid':
        if ts.startswith('finetime'):
            # print('***', v, ts)
            vs = binhexstring(val, 'string', width=width, v=v, **kwds)
        else:
            vs = binhexstring(val, ts, width=width, v=v, p=p, **kwds)
    else:
        # v is '_value/data'
        if ts.startswith('finetime'):
            if state:
                vv, vdesc = p.validate(val)
                if vdesc.lower() not in Ommitted_Valid_Rule_Names:
                    vs = '%s (%s)' % (
                        vdesc, val.toString(width=width, **kwds))
                else:
                    vs = val.toString(width=width, **kwds)
            else:
                vs = val.toString(width=width, **kwds)
        elif not state or not hasattr(p, 'validate'):
            # for  value/data, print list horizontally
            width = 0
            vs = binhexstring(val, ts, width=width, v=v, **kwds)
        elif hasattr(p, 'validate'):
            # v is _value/data of parameter of non-finetime to be displayed with state
            validity = p.validate(val)
            if issubclass(validity.__class__, tuple):
                # not binary masked
                vv, vdesc = validity
                if vdesc.lower() not in Ommitted_Valid_Rule_Names:
                    vs = '%s (%s)' % (
                        vdesc, binhexstring(val, ts, v=v, **kwds))
                else:
                    vs = binhexstring(val, ts, v=v, **kwds)
            else:
                # binary masked. validity is a list of tuple/lists
                # validity is (val, state, mask height, mask width)
                sep = '\n' if width else ', '
                vs = sep.join(r[1] if r[1] == 'Invalid' else'%s (%s)' %
                              (r[1], format(r[0], '#0%db' % (r[3]+2))) for r in validity)
    return vs


def attrstr1(p, v, missingval='', ftime=False, state=True, width=1, **kwds):
    """
    generic string representation of an attribute of a parameter or dataset.

    p: parameter object.
    v: name of parameter attribute. '_valid', '_type', '_default', '_value' (for Parameter) or '_data' (dataset)
    missingval: string used when the parameter does not have the attribute.
    ftime: True means that attribute value will be FineTime if _type is 'finetime'.
    state: The state validity of the parameter is returned in place of value, if the state is not in Ommitted_Valid_Rule_Names -- 'valid', 'range', '' or 'default'.
    """

    ts = getattr(p, '_type') if hasattr(p, '_type') else missingval
    if ts is None:
        ts = 'None'
    if hasattr(p, v):
        val = getattr(p, v)
        if val is None:
            return 'None'
        val_cls = val.__class__
        # from ..dataset.finetime import FineTime
        # if issubclass(val_cls, FineTime):
        if ftime:
            # v is '_valid', '_default' or '_value/data'
            if ts.startswith('finetime'):
                # print('***', v, ts)
                if v == '_valid':
                    s = binhexstring(val, 'string', v=v, **kwds)
                elif v == '_default':
                    s = val.toString(width=width, **kwds)
                elif state:
                    vv, vdesc = p.validate(val)
                    if vdesc.lower() not in Ommitted_Valid_Rule_Names:
                        s = '%s (%s)' % (
                            vdesc, val.toString(width=width, **kwds))
                    else:
                        s = val.toString(width=width, **kwds)
                else:
                    s = val.toString(width=width, **kwds)
                vs = s
            elif not state or v == '_valid' or v == '_default' or not hasattr(p, 'validate'):
                if v != '_valid':
                    # for default and value/data, print list horizontally
                    width = 0
                vs = binhexstring(val, ts, width=width, v=v, **kwds)
            elif hasattr(p, 'validate'):
                # v is _value/data of parameter of non-finetime to be displayed with state
                validity = p.validate(val)
                if issubclass(validity.__class__, tuple):
                    # not binary masked
                    vv, vdesc = validity
                    if vdesc.lower() not in Ommitted_Valid_Rule_Names:
                        vs = '%s (%s)' % (
                            vdesc, binhexstring(val, ts, v=v, **kwds))
                    else:
                        vs = binhexstring(val, ts, v=v, **kwds)
                else:
                    # binary masked. validity is a list of tuple/lists
                    # validity is (val, state, mask height, mask width)
                    sep = '\n' if width else ', '
                    vs = sep.join('%s (%s)' %
                                  (r[1], format(r[0], '#0%db' % r[3])) for r in validity)
        else:
            # must be string
            vs = val
    else:
        vs = missingval
    return vs


def exprstrs(param, v='_value', extra=False, **kwds):
    """ Generates a set of strings for param.toString().

    :param: Parameeter or xDstaset.
    :extra: Whether to include less often used attributes suc as ```fits_keyword```.
    """
    if issubclass(param.__class__, dataset.metadata.Parameter):
        extra_attrs = copy.copy(param._all_attrs)
    elif issubclass(param.__class__, (dataset.arraydataset.ArrayDataset,
                                      dataset.tabledataset.TableDataset,
                                      dataset.unstructureddataset.UnstrcturedDataset)):
        extra_attrs = dict((n, v['default'])
                           for n, v in param.zInfo['metadata'].items())
    else:
        extra_attrs = {}
    ts = attrstr(param, '_type', **kwds)
    if 'typ_' in extra_attrs:
        extra_attrs.pop('typ_', '')
    else:  # Dataset
        extra_attrs.pop('type', '')
    vs = attrstr(param, v, ftime=True, **kwds)
    extra_attrs.pop('value', '')
    fs = attrstr(param, '_default', ftime=True, **kwds)
    extra_attrs.pop('default', '')
    ds = attrstr(param, 'description', **kwds)
    extra_attrs.pop('description')
    gs = attrstr(param, '_valid', ftime=True, **kwds)
    extra_attrs.pop('valid', '')
    us = attrstr(param, '_unit', **kwds)
    extra_attrs.pop('unit', '')
    cs = attrstr(param, '_typecode', **kwds)
    extra_attrs.pop('typecode', '')

    return (vs, us, ts, ds, fs, gs, cs, extra_attrs)


def pathjoin(*p):
    """ join path segments with given separater (default '/').
    Useful when '\\' is needed.
    """
    sep = '/'
    r = sep.join(p).replace(sep+sep, sep)
    # print(p, r)
    return r


bldins = str.__class__.__module__


def fullname(obj):
    """ full class name with module name.

    https://stackoverflow.com/a/2020083/13472124
    """
    t = type(obj) if not isinstance(obj, type) else obj
    module = t.__module__
    if module is None or module == bldins:
        return t.__name__  # Avoid reporting __builtin__
    else:
        return module + '.' + t.__name__


def getObjectbyId(idn, lgbv):
    """ lgb is from deserializing caller's globals().values()
    locals().values() and built-ins
    """
    v = lgbv
    for obj in v:
        if id(obj) == idn:
            return obj
    raise ValueError("Object not found by id %d." % (idn))


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # python 3.6 doc
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def t2l(v):
    """ convert tuples to lists in nested data structures
    """
    # print(v)
    if issubclass(v.__class__, (list, tuple)):
        y = [t2l(x) if issubclass(
            x.__class__, tuple) else x for x in v]
        # print('== ', y)
        return y
    return v


def l2t(v):
    """ convert lists to tuples in nested data structures
    """
    # print(v)
    if issubclass(v.__class__, (list, tuple)):
        y = tuple(l2t(x) if issubclass(
            x.__class__, list) else x for x in v)
        # print('== ', y)
        return y
    return v


def ld2tk(v):
    """ convert lists, to tuples and dicts to frozensets in nested data structures
    array.array is converted to (typecode, itemsize, size, ld2tk(0th element))
    """
    # print(v)
    if issubclass(v.__class__, (list, tuple)):
        y = tuple(ld2tk(x) for x in v)
    # elif :  # issubclass(v.__class__, (list)):
    #     if len(v) > 128 and issubclass(v[0].__class__, (Sequence)):
    #         y = (type(v[0]), len(v), ld2tk(v[0]))
    #     else:
    #         y = tuple(ld2tk(x) for x in v)
    elif issubclass(v.__class__, (array.array)):
        y = (v.typecode, v.itemsize, len(v), len(v[0]) if issubclass(
            v[0].__class__, Sequence) else ld2tk(v[0]))
    elif issubclass(v.__class__, (dict)):
        # print('== ', y)
        y = frozenset((ld2tk(k), ld2tk(v)) for k, v in v.items())
    elif issubclass(v.__class__, (set)):
        # print('== ', y)
        y = frozenset(ld2tk(x) for x in v)
    else:
        y = v
    return y


class UserOrGroupNotFoundError(BaseException):
    pass


def getUidGid(username):
    """ returns the UID and GID  of the named user.

    return: -1 if not available
    """

    try:
        uid = pwd.getpwnam(username).pw_uid
    except KeyError as e:
        msg = 'Cannot get UserID for ' + username + \
            '. check config. ' + str(e) + trbk(e)
        logger.error(msg)
        uid = -1
        # UserOrGroupNotFoundError(msg).with_traceback(sys.exc_info()[2])
        raise
    # do if platform supports.
    try:
        gid = pwd.getpwnam(username).pw_gid
    except KeyError as e:
        msg = 'Cannot get GroupID for ' + username + \
            '. check config. ' + str(e) + trbk(e)
        gid = -1
        logger.error(msg)
        raise

    return uid, gid


def findShape(data, element_seq=(str)):
    """ Shape of list/dict of list/dict.

    :element_seq: treat elements of these sequence types as scalars.
    """
    if data is None:
        return None
    shape = []
    d = data
    while d is not None:
        if issubclass(d.__class__, element_seq):
            d = None
        else:
            try:
                shape.append(len(d))
                d = list(d.values())[0] if issubclass(
                    d.__class__, Mapping) else d[0]
            except (TypeError, IndexError, KeyError) as e:
                d = None
    return tuple(shape)


def guess_value(input_string, parameter=False, last=str):
    """ Returns guessed value from a string.

    | input | output |
    | ```'None'``` | `None` |
    | integer | `int()` |
    | float | `float()` |
    | ```'True'```, ```'False```` | `True`, `False` |
    | string starting with ```'0x'``` | `hex()` |
    | else | run `last`(input_string) |

    """
    from ..dataset.numericparameter import NumericParameter, BooleanParameter
    from ..dataset.dateparameter import DateParameter
    from ..dataset.stringparameter import StringParameter
    from ..dataset.metadata import Parameter
    if input_string == 'None':
        res = None
    elif input_string == '':
        if parameter:
            return StringParameter(value=input_string)
        else:
            return input_string
    else:
        try:
            res = int(input_string)
            return NumericParameter(value=res) if parameter else res
        except ValueError:
            try:
                res = float(input_string)
                return NumericParameter(value=res) if parameter else res
            except ValueError:
                # string, bytes, bool
                if input_string.startswith('0x'):
                    res = bytes.fromhex(input_string[2:])
                    return NumericParameter(value=res) if parameter else res
                elif input_string in ['True', 'False']:
                    res = bool(input_string)
                    return BooleanParameter(value=res) if parameter else res
                else:
                    res = last(input_string)
                    return Parameter(value=res) if parameter else res
    return None
