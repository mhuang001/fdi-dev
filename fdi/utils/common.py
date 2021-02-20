# -*- coding: utf-8 -*-

from .masked import masked
import hashlib
import traceback
import logging
from itertools import zip_longest
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


def bstr(x, length=0, tostr=True, quote="'", level=0, **kwds):
    """ returns the best string representation.
    if the object is a string, return single-quoted; if has toString(), use it; else returns str(). Length limited by lls(lls)
    """

    s = issubclass(x.__class__, str) if PY3 else issubclass(
        x.__class__, (str, unicode))

    if s:
        r = quote + x + quote
    elif tostr and hasattr(x, 'toString'):
        r = x.toString(level=level, **kwds)
    elif issubclass(x.__class__, (bytes, bytearray, memoryview)):
        r = x.hex()
    else:
        r = str(x)
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


def wls(s, width=15):
    """ widthth-limited string.

    width: if > 0  returns the str with '\n' inserted every width chars. Or else return ``s``. Default is 15.
    """

    if width <= 0:
        return s
    ret = []
    for seg in s.split('\n'):
        ret.append('\n'.join(seg[i:i+width]
                             for i in range(0, len(seg), width)))
    return '\n'.join(ret)


def mstr(obj, level=0, excpt=None, indent=4, depth=0, **kwds):
    """ Makes a presentation string at a detail level.

    'tablefmt' is not in the args as it is needed to be passed by kwds in recursive calls although under some conditions it is used.
    """
    if excpt is None:
        excpt = ['_STID', 'data', '_sets']
    ind = ' '*indent

    if level == 0:
        if not hasattr(obj, 'items'):
            return bstr(obj, level=level, **kwds)
        from fdi.dataset.metadata import MetaData
        if issubclass(obj.__class__, MetaData):
            return obj.toString(level=level, **kwds)
        s = ['%s= {%s}' % (mstr(k, level=level, excpt=excpt,
                                indent=indent, depth=depth+1, quote='', **kwds),
                           mstr(v, level=level, excpt=excpt,
                                indent=indent, depth=depth+1, **kwds))
             for k, v in obj.items() if k not in excpt]
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
        from fdi.dataset.metadata import MetaData
        if issubclass(obj.__class__, MetaData):
            return obj.toString(level=level, **kwds) + '\n'
        else:
            pat = '%s= {%s}' if depth == 0 else '%s= %s'
            data = obj

        s = [pat % (mstr(k, level=level, excpt=excpt,
                         indent=indent, depth=depth+1, quote='', **kwds),
                    mstr(v, level=level, excpt=excpt,
                         indent=indent, depth=depth+1, **kwds))
             for k, v in data.items() if k not in excpt]
        sep = ',\n' if depth == 0 else ', '
        return sep.join(s)
    else:
        if not hasattr(obj, 'items'):
            return mstr(obj, level=1, **kwds)
        s = ['%s' % (mstr(k, level=level, excpt=excpt, quote='', **kwds))
             for k, v in obj.items() if k not in excpt]
        return ', '.join(s)


def binhexstring(val, typ_, width=0, v=None, p=None):
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
        if not issubclass(t.__class__, (tuple, list)):
            # val is a one-dim array or vector
            lst.append(func(t))
            breakline = False
            continue
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
            if len(lst) > 6:
                lst.append('... total %d elements in dim=1' % len(val))
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
            vs = binhexstring(val, ts, width=width)
    elif v == '_valid':
        if ts.startswith('finetime'):
            # print('***', v, ts)
            vs = binhexstring(val, 'string', width=width, v=v)
        else:
            vs = binhexstring(val, ts, width=width, v=v, p=p)
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
            vs = binhexstring(val, ts, width=width, v=v)
        elif hasattr(p, 'validate'):
            # v is _value/data of parameter of non-finetime to be displayed with state
            validity = p.validate(val)
            if issubclass(validity.__class__, tuple):
                # not binary masked
                vv, vdesc = validity
                if vdesc.lower() not in Ommitted_Valid_Rule_Names:
                    vs = '%s (%s)' % (vdesc, binhexstring(val, ts, v=v))
                else:
                    vs = binhexstring(val, ts, v=v)
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
                    s = binhexstring(val, 'string', v=v)
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
                vs = binhexstring(val, ts, width=width, v=v)
            elif hasattr(p, 'validate'):
                # v is _value/data of parameter of non-finetime to be displayed with state
                validity = p.validate(val)
                if issubclass(validity.__class__, tuple):
                    # not binary masked
                    vv, vdesc = validity
                    if vdesc.lower() not in Ommitted_Valid_Rule_Names:
                        vs = '%s (%s)' % (vdesc, binhexstring(val, ts, v=v))
                    else:
                        vs = binhexstring(val, ts, v=v)
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


def exprstrs(param, v='_value', **kwds):
    """ Generates a set of strings for toString().

    """

    ts = attrstr(param, '_type', **kwds)
    vs = attrstr(param, v, ftime=True, **kwds)
    fs = attrstr(param, '_default', ftime=True, **kwds)
    ds = attrstr(param, 'description', **kwds)
    gs = attrstr(param, '_valid', ftime=True, **kwds)
    us = attrstr(param, '_unit', **kwds)
    cs = attrstr(param, '_typecode', **kwds)

    return (vs, us, ts, ds, fs, gs, cs)


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
    """
    # print(v)
    if issubclass(v.__class__, (list, tuple)):
        y = tuple(ld2tk(x) for x in v)
    elif issubclass(v.__class__, (dict)):
        # print('== ', y)
        y = frozenset((ld2tk(k), ld2tk(v)) for k, v in v.items())
    elif issubclass(v.__class__, (set)):
        # print('== ', y)
        y = frozenset(ld2tk(x) for x in v)
    else:
        y = v
    return y
