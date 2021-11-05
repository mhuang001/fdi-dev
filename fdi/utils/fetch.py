# -*- coding: utf-8 -*-

from ..dataset.deserialize import deserialize_args
from collections.abc import Mapping, Sequence
from operator import methodcaller
import inspect
import sys
from itertools import chain


def fetch(paths, nested, re='', sep='/', exe=['is'], not_quoted=True):
    """ Use paths to access values of internal elements of a nested python object.

    :paths: 1). If given as a string, the string will be splitted with `sep` into a list of strings, then go on to 2); 2). If given as a list of strings, its 0th member is to match one of the first level of nested attributes, keys, or method names. If the list was made in 1) the 0th member will be converted to an integer if possible.
    * if the 0th member is a string and can be parsed by :meth:`deserialize_args`, the result to used as te named method and its arguments.
    * if that fails, it will be taken as a string and check if there is a match in keys (members);
    * else search in attributes.

    :nested: a live nested data structure.
    :re: datapath representation for `nested`. Can be applied to reproduce the result.
    :exe: 1) A list of patterns which if found in the name of a method/function the matching method/function is allowed to run. 2) If one of the pattern is '*', all methods/functions are allowed to run. 3) If a pattern starts with a '-' then the matching method/function to the pattern ('-' removed) is not allowed to run (overriding previous rules.
    :not_quoted: the method-args string is not encoded with `quote`.
    """

    if issubclass(paths.__class__, str):
        paths = paths.strip(' ').strip(sep).split(sep)
        from_str = True
    else:
        from_str = False

    if len(paths) == 0 or paths[0] == '':
        return nested, re

    p0 = paths[0]
    found_method = None
    # print('>>>> ', p0)

    if from_str:
        try:
            p0 = int(p0)
        except (ValueError, TypeError):
            # nested expects an integer
            pass
        # f'{p0} cannot be converted to an integer.').with_traceback(sys.exc_info()[2])
    try:
        v0 = nested[p0]
        q = '"' if issubclass(p0.__class__, str) else ''
        rep = re + '['+q + str(p0) + q + ']'
        if len(paths) == 1:
            return v0, rep
        return fetch(paths[1:], v0, re=rep, sep=sep, exe=exe)
    except (TypeError, KeyError, ValueError):
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
        if inspect.ismethod(v0) or inspect.isfunction(v0):
            if '*' in exe:
                can_exec = True
            else:   # TODO test
                can_exec = any(patt in p0 for patt in exe if patt[0] != '-')
            can_exec = not any(
                patt[1:] in p0 for patt in exe if patt[0] == '-')
            if can_exec:
                # assemble expression of keywords args from deserialize_args
                kwdsexpr = [str(k)+'='+str(v) for k, v in kwds.items()]
                # assemble positional and keywords args
                all_args_expr = ', '.join(chain(map(str, args), kwdsexpr))
                # return execution results and path-representation
                # return f'{rep}({all_args_expr})', f'{rep}({all_args_expr})'

                # v0(*[], **{}) is not v0() !
                res = v0(*args, **kwds)
                v0 = res
                rep = f'{rep}({all_args_expr})'
        # not executable
        if len(paths) == 1:
            return v0, rep
        return fetch(paths[1:], v0, re=rep, sep=sep, exe=exe)
    # not methods, attribute or member
    # if found_method:
        # return methodcaller(p0)(nested), rep + '()'
    #    return found_method(), rep + '()'
    return None, '%s has no attribute or member: %s.' % (re, p0)
