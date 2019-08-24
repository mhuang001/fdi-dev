# -*- coding: utf-8 -*-
from collections import OrderedDict
import json
import pprint

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def deepcmp(obj1, obj2, seenlist=None, verbose=False):
    """ recursively descend into set, list, dict, ordereddict,
    (or ordereddict subclasses) and any objects with '__class__', compare
    every member with the other objects counterpart.
    Detects cyclic references.
    Returns None if finds no difference, a string of explanation
    otherwise.
    """
    if seenlist is None:
        seen = []
    else:
        seen = seenlist

    def run(o1, o2, v=False):
        nonlocal seen
        pair = (id(o1), id(o2))
        c = o1.__class__
        c2 = o2.__class__
        if v:
            print('1 ' + str(len(seen)) + str(c) + str(o1))
            print('2 ' + str(c2) + str(o2))
        if pair in seen:
            if v:
                logger.debug('deja vue')
            return None
        seen.append(pair)
        if c != c2:
            return ' due to diff types: ' + c.__name__ + ' and ' + c2.__name__
        dc, sc, tc, lc = {1: 2}.__class__, {
            2}.__class__, (2, 9).__class__, [].__class__
        if c == dc or issubclass(c, OrderedDict):
            if c == dc:
                #  dict
                r = run(set(o1.keys()), set(o2.keys()))
            else:
                #  OrderedDict
                r = run(list(o1.keys()), list(o2.keys()))
            if r is not None:
                return " due to diff " + c.__name__ + " keys" + r
            for k in o1.keys():
                if k not in o2:
                    return ' due to o2 has no key=%s' % (str(k))
                r = run(o1[k], o2[k])
                if r is not None:
                    s = ' due to diff values for key=%s' % (str(k))
                    return s + r
            return None
        elif c in (sc, tc, lc):
            if len(o1) != len(o2):
                return ' due to diff %s lengths %d and %d' %\
                    (c.__name__, len(o1), len(o2))
            if c in (tc, lc):
                for i in range(len(o1)):
                    r = run(o1[i], o2[i])
                    if r is not None:
                        return ' due to diff at index=%d' % (i) + r
                return None
            else:
                oc = o2.copy()
                for m in o1:
                    found = False
                    for n in oc:
                        r = run(m, n)
                        if r is None:
                            found = True
                            break
                    if not found:
                        return ' due to %s not in the latter' % (str(m))
                    oc.remove(n)
                return None
        else:
            if hasattr(o1, '__dict__'):
                r = run(o1.__dict__, o2.__dict__)
                return r
            if o1 != o2:
                s = ' due to "%s" != "%s"' % (str(o1), str(o2))
                return s
            return None
    return run(obj1, obj2, verbose)


class DeepEqual():
    """ mh: Can compare key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj does not have items()
    """

    def equals(self, obj):
        r = deepcmp(self, obj)
        # logging.debug(r)
        return r == None

    def __eq__(self, obj):
        return self.equals(obj)

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def diff(self, obj, seenlist):
        r = deepcmp(self, obj, seenlist=seenlist)
        return r


class EqualDict():
    """ mh: Can compare key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj does not have items()
    """

    def equals(self, obj):
        dbg = False
        if obj is None:
            return False
        try:
            if self.__dict__ != obj.__dict__:
                if dbg:
                    print('@@ diff \n' + str(self.__dict__) +
                          '\n>>diff \n' + str(obj.__dict__))
                return False
        except Exception as err:
            # print('Exception in dict eq comparison ' + str(err))
            return False
        return True

    def __eq__(self, obj):
        return self.equals(obj)

    def __ne__(self, obj):
        return not self.__eq__(obj)


class EqualODict():
    """ mh: Can compare order and key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj does not have items()
    """

    def equals(self, obj):
        if obj is None:
            return False
        try:
            return list(self.items()) == list(obj.items())
        except Exception:
            return False
        return True

    def __eq__(self, obj):
        return self.equals(obj)

    def __ne__(self, obj):
        return not self.__eq__(obj)
