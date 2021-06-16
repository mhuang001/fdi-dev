
# -*- coding: utf-8 -*-

from collections.abc import Mapping, Sequence
from operator import methodcaller
import inspect


def fetch(paths, nested, re=''):
    """ use members of paths to go into nested internal recursively to get the end point value.

    paths: its 0th member matches the first level of nested attribute or keys. if the 0th member is a string and has commas, then it is  tried to be parsed into a tuple of comma-separated numerics. if that fails, it will be taken as a string.
If the above fail and a method whose name starts with 'is' then the method is called and the result returned.
    """

    if len(paths) == 0:
        return nested, re
    if issubclass(paths.__class__, str):
        paths = paths.split('/')

    p0 = paths[0]
    found_meth = None

    is_str = issubclass(p0.__class__, str)
    if is_str and hasattr(nested, p0):
        v = getattr(nested, p0)
        rep = re + '.'+p0
        if inspect.ismethod(v) and p0.startswith('is'):
            found_meth = v
        else:
            if len(paths) == 1:
                return v, rep
            return fetch(paths[1:], v, rep)
    else:
        if is_str and ',' in p0:
            num = []
            for seg in p0.split(','):
                try:
                    n = int(seg)
                except ValueError:
                    try:
                        n = float(seg)
                    except ValueError:
                        break
                num.append(n)
            else:
                # can be converted to numerics
                p0 = list(num)
        try:
            v = nested[p0]
            q = '"' if issubclass(p0.__class__, str) else ''
            rep = re + '['+q + str(p0) + q + ']'
            if len(paths) == 1:
                return v, rep
            return fetch(paths[1:], v, rep)
        except TypeError:
            pass
    # not attribute or member
    if found_meth:
        # return methodcaller(p0)(nested), rep + '()'
        return found_meth(), rep + '()'

    return None, '%s has no attribute or member: %s.' % (re, p0)
