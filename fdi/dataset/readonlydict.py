# -*- coding: utf-8 -*-

from collections.abc import Mapping
from types import MappingProxyType
import copy


def make_readonly(d, excluded=None):
    """ Recursively make values of Mapping type at all levels read-only.
    """
    if excluded is None:
        excluded = set()
    else:
        i = id(d)
        if i in excluded:
            return d
        else:
            excluded.add(i)
    for k, v in d.items():
        if issubclass(v.__class__, Mapping):
            d[k] = make_readonly(v, excluded=excluded)
        else:
            continue
    return d


class frozendict(dict):
    """
    Extended version of frozent dict.

    This extended version of the code above will also "freeze" dictionaries and lists stored as values of the dictionary. If dictionaries/lists are found among the values, they will be handled recursively.

    Oren Tirosh, Ero Carrera, Søren Løvborg

    https://code.activestate.com/recipes/414283/
    """
    def _blocked_attribute(obj):
        raise AttributeError("A frozendict cannot be modified.")
    _blocked_attribute = property(_blocked_attribute)

    __delitem__ = __setitem__ = clear = _blocked_attribute
    pop = popitem = setdefault = update = _blocked_attribute

    def __new__(cls, *args, **kw):
        new = dict.__new__(cls)

        args_ = []
        for arg in args:
            if isinstance(arg, dict):
                arg = copy.copy(arg)
                for k, v in arg.items():
                    if isinstance(v, dict):
                        arg[k] = frozendict(v)
                    elif isinstance(v, list):
                        v_ = list()
                        for elm in v:
                            if isinstance(elm, dict):
                                v_.append(frozendict(elm))
                            else:
                                v_.append(elm)
                        arg[k] = tuple(v_)
                args_.append(arg)
            else:
                args_.append(arg)

        dict.__init__(new, *args_, **kw)
        return new

    def __init__(self, *args, **kw):
        pass

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(frozenset(self.items()))
            return h

    def __repr__(self):
        return "frozendict(%s)" % dict.__repr__(self)


ReadOnlyDict = frozendict


# from immutabledict import immutabledict
# class aReadOnlyDict(immutabledict):

#     def __getitem_a_(self, key):
#         it = super().__getitem__(key)

#         if issubclass(it.__class__, dict):
#             rodict = ReadOnlyDict(it)
#             return rodict
#         return it


class bReadOnlyDict(dict):
    """
    Dictionary that is read-only and returns all values of dict type to ReadOnlyDict type so they, too, cannot be modified.

    Based on https://stackoverflow.com/a/61700719/13472124


    """

    # def __init__(self, d):

    def __readonly__(self, *args, **kwargs):
        raise RuntimeError("Cannot modify ReadOnlyDict")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    __copy__ = __readonly__  # dict.copy
    __deepcopy__ = __readonly__  # copy._deepcopy_dispatch.get(dict)
    del __readonly__

    def __getitem__(self, key):
        it = super().__getitem__(key)
        # print(key)
        import pdb
        pdb.set_trace()

        if issubclass(it.__class__, dict):
            rodict = ReadOnlyDict(it)
            return rodict
        return it
