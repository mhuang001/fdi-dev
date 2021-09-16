# -*- coding: utf-8 -*-

from ..dataset.deserialize import deserialize_args
from collections.abc import Mapping, Sequence
from operator import methodcaller
import inspect
from itertools import chain


def fetch(paths, nested, re='', exe=['is'], not_quoted=True):
    """ use members of paths to go into nested internal recursively to get the end point value.

    :paths: its 0th member is to match one of the first level of nested attributes, keys, or method names.
    * if the 0th member is a string and can be parsed by `deserialize_args`, the result to used as te named method and its arguments.
    * if that fails, it will be taken as a string and check if there is a match in keys (members);
    * else search in attributes.

    Match: If the name of said attributes, keys, or methds starts with a ppattern'  string in `exe`.

    :nested: a live nested data structure.
    :re: datapath representation for `nested`. Can be applied to reproduce the result.
    :exe: a list of patterns for names of methods/functions aloowed to run.
    :not_quoted: the method-args string is not encoded with `quote`.
    """

    if len(paths) == 0:
        return nested, re
    if issubclass(paths.__class__, str):
        paths = paths.split('/')

    p0 = paths[0]
    found_method = None
    #print('>>>> ', p0)
    try:
        v0 = nested[p0]
        q = '"' if issubclass(p0.__class__, str) else ''
        rep = re + '['+q + str(p0) + q + ']'
        if len(paths) == 1:
            return v0, rep
        return fetch(paths[1:], v0, rep, exe)
    except (TypeError, KeyError):
        pass

    if not issubclass(p0.__class__, str):
        raise TypeError(f'{p0} should be a string, not {p0.__class__}.')

    # get command positional arguments and keyword arguments
    code, m_args, kwds = deserialize_args(
        all_args=p0, not_quoted=not_quoted)
    p0, args = m_args[0], m_args[1:]

    if hasattr(nested, p0):
        v0 = getattr(nested, p0)
        rep = re + '.' + p0
        if '*' in exe:
            can_exec = True
        else:
            can_exec = any(p0.startswith(patt) for patt in exe)  # TODO test
        if inspect.ismethod(v0) and can_exec:
            kwdsexpr = [str(k)+'='+str(v) for k, v in kwds.items()]
            all_args_expr = ', '.join(chain(map(str, args), kwdsexpr))
            # return f'{rep}({all_args_expr})', f'{rep}({all_args_expr})'
            return v0(*args, **kwds), f'{rep}({all_args_expr})'
        else:
            if len(paths) == 1:
                return v0, rep
            return fetch(paths[1:], v0, rep, exe)
    # not methods, attribute or member
    # if found_method:
        # return methodcaller(p0)(nested), rep + '()'
    #    return found_method(), rep + '()'
    return None, '%s has no attribute or member: %s.' % (re, p0)
