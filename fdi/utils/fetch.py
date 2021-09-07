# -*- coding: utf-8 -*-

from ..dataset.deserialize import deserialize_args
from collections.abc import Mapping, Sequence
from operator import methodcaller
import inspect
from itertools import chain


def fetch(paths, nested, re='', exe=['is'], not_quoted=True):
    """ use members of paths to go into nested internal recursively to get the end point value.

    :paths: its 0th member matches the first level of nested attribute or keys. if the 0th member is a string and has commas, then it is  tried to be parsed into a tuple of comma-separated numerics. if that fails, it will be taken as a string.
If the above fail and a method whose name starts with 'is', or any string in `exe`, then the method is called and the result returned.
    :nested: a live nested data structure.
    :re: datapath representation. Can be applied to reproduce the result.
    :exe: a list of patterns for names of methods/functions aloowed to run.
    :not_quoted: the method-args string is not encoded with `quote`.
    """

    if len(paths) == 0:
        return nested, re
    if issubclass(paths.__class__, str):
        paths = paths.split('/')

    p0 = paths[0]
    found_method = None

    is_str = issubclass(p0.__class__, str)
    if is_str:
        # get command positional arguments and keyword arguments
        code, m_args, kwds = deserialize_args(
            all_args=p0, not_quoted=not_quoted)
        p0, args = m_args[0], m_args[1:]

    # if is_str and hasattr(nested, p0):
    if is_str and code == 200 and hasattr(nested, p0):
        v = getattr(nested, p0)
        rep = re + '.'+p0
        if '*' in exe:
            can_exec = True
        else:
            can_exec = any(p0.startswith(patt) for patt in exe)  # TODO test
        if inspect.ismethod(v) and can_exec:
            #found_method = v
            kwdsexpr = [str(k)+'='+str(v) for k, v in kwds.items()]
            all_args_expr = ', '.join(chain(map(str, args), kwdsexpr))
            return v(*args, **kwds), f'{rep}({all_args_expr})'
        else:
            if len(paths) == 1:
                return v, rep
            return fetch(paths[1:], v, rep, exe)
    else:
        if is_str and ',' in p0:
            # p0 is a set of arguments of int and float
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
            return fetch(paths[1:], v, rep, exe)
        except TypeError:
            pass
    # not attribute or member
    # if found_method:
        # return methodcaller(p0)(nested), rep + '()'
    #    return found_method(), rep + '()'

    return None, '%s has no attribute or member: %s.' % (re, p0)
