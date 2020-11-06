# -*- coding: utf-8 -*-

from tabulate import tabulate
import hashlib
import traceback
import logging
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

    width: if > 0   Returns the str with '\n' inserted every width chars.
    else return s.
    """

    if width <= 0:
        return s
    return '\n'.join(s[i:i+width] for i in range(0, len(s), width))


def mstr(obj, level=0, excpt=None, indent=4, depth=0, **kwds):
    """ Makes a presentation string at a detail level.
    """
    if excpt is None:
        excpt = ['classID', 'data', '_sets']
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
            pat = '%s= %s' if depth == 0 else '%s= %s'
            data = obj._sets
        else:
            pat = '%s= {%s}' if depth == 0 else '%s= %s'
            data = obj

        s = [pat % (mstr(k, level=level, excpt=excpt,
                         indent=indent, depth=depth+1, quote='', **kwds),
                    mstr(v, level=level, excpt=excpt,
                         indent=indent, depth=depth+1, **kwds))
             for k, v in data.items() if k not in excpt]
        if issubclass(obj.__class__, MetaData):
            tab = []
            for i in range(int(len(s)/4)):
                row = tuple(wls(s[i*4+j], 20) for j in range(4))
                tab.append(row)
            t = tabulate(tab, headers='', tablefmt='simple', disable_numparse=True,
                         **kwds) if len(tab) else '(empty)'
            return '\n' + t + '\n'
        sep = ',\n' if depth == 0 else ', '
        return sep.join(s)
    else:
        if not hasattr(obj, 'items'):
            return mstr(obj, level=1, **kwds)
        s = ['%s' % (mstr(k, level=level, excpt=excpt, quote='', **kwds))
             for k, v in obj.items() if k not in excpt]
        return ', '.join(s)


def attrstr(p, v, ts, missingval, ftime=False):
    if hasattr(p, v):
        val = getattr(p, v)
        if val is None:
            return 'None'
        vc = val.__class__
        # from ..dataset.finetime import FineTime
        # if issubclass(vc, FineTime):
        if ftime and ts == 'finetime':
            # print('***', v, ts)
            if v == '_valid':
                s = '['+', '.join(str(x) for x in val) + ']'
            else:
                s = val.toString(level=1, width=1)
            val = s
        vs = hex(val) if ts == 'hex' and issubclass(
            vc, int) else str(val)
    else:
        vs = missingval
    return vs


def exprstrs(param, v='_value', missingval='-'):
    """ Generates a set of strings for expr() """

    ts = attrstr(param, '_type', 'string', missingval)
    vs = attrstr(param, v, ts, missingval, ftime=True)
    fs = attrstr(param, '_default', ts, missingval, ftime=True)
    ds = attrstr(param, 'description', ts, missingval)
    gs = attrstr(param, '_valid', ts, missingval, ftime=True)
    us = attrstr(param, '_unit', ts, missingval)
    cs = attrstr(param, '_typecode', ts, missingval)

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
