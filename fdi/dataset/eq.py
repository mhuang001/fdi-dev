# -*- coding: utf-8 -*-


from ..utils.common import lls, ld2tk
from .serializable import Serializable

import pprint
import array
from functools import lru_cache
from collections import OrderedDict
from itertools import chain

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class CircularCallError(RuntimeError):
    pass


def deepcmp(obj1, obj2, seenlist=None, verbose=False, eqcmp=False):
    """ Recursively descends into obj1's every member, which may be
    set, list, dict, ordereddict, (or ordereddict subclasses) and
    any objects with '__class__' attribute,
    compares every member found with its counterpart in obj2.
    Returns None if finds no difference, a string of explanation
    otherwise.
    Detects cyclic references.

    eqcmp: if True, use __eq__ or __cmp__ if the objs have them. If False only use as the last resort. default True.
    """
    # seen and level are to be used as nonlocal variables in run()
    # to overcome python2's lack of nonlocal type this method is usded
    # https://stackoverflow.com/a/28433571
    class _context:
        if seenlist is None:
            seen = []
        else:
            seen = seenlist
        level = 0

    def run(o1, o2, v=False, eqcmp=True, default=None):
        #
        # nonlocal seen
        # nonlocal level
        id1, id2 = id(o1), id(o2)
        if id1 == id2:
            if v:
                print('they are the same object.')
            return None
        pair = (id1, id2) if id1 < id2 else (id2, id1)
        c = o1.__class__
        c2 = o2.__class__
        if v:
            _context.level += 1
            print('deepcmp level %d seenlist length %d' %
                  (_context.level, len(_context.seen)))
            print('1 ' + str(c) + lls(o1, 75))
            print('2 ' + str(c2) + lls(o2, 75))
        if pair in _context.seen:
            msg = 'deja vue %s' % str(pair)
            raise CircularCallError(msg)
        _context.seen.append(pair)
        if c != c2:
            if v:
                print('type diff')
            del _context.seen[-1]
            return ' due to diff types: ' + c.__name__ + ' and ' + c2.__name__
        dc, sc, fc, tc, lc = dict, set, frozenset, tuple, list

        has_eqcmp = (hasattr(o1, '__eq__') or hasattr(
            o1, '__cmp__')) and not issubclass(c, DeepEqual)
        if eqcmp and has_eqcmp:
            if v:
                print('obj1 has __eq__ or __cmp__ and not using deepcmp')
            # checked in-seen to ensure whst follows will not cause RecursionError
            try:
                t = o1 == o2
            except CircularCallError as e:
                if v:
                    print('Get circular call using eq/cmp: '+str(e))
                pass
            else:
                if t:
                    del _context.seen[-1]
                    return None
                else:  # o1 != o2:
                    s = ' due to "%s" != "%s"' % (lls(o1, 155), lls(o2, 155))
                    del _context.seen[-1]
                    return s
        try:
            # this is not good if len() is delegated
            # if hasattr(o1, '__len__') and len(o1) != len(o2):
            if hasattr(o1, '__len__') and len(o1) != len(o2):
                del _context.seen[-1]
                return ' due to diff %s lengths: %d and %d (%s, %s)' %\
                    (c.__name__, len(o1), len(o2), str(list(o1)), str(list(o2)))
        except AttributeError:
            pass
        if issubclass(c, dc):
            if v:
                print('Find dict or subclass')
                print('check keys')
            if issubclass(c, OrderedDict):
                #
                r = run(list(o1.keys()), list(o2.keys()), v=v, eqcmp=eqcmp)
            else:
                #  dict
                r = run(tuple(sorted(o1.keys(), key=hash)),
                        tuple(sorted(o1.keys(), key=hash)),
                        v=v, eqcmp=eqcmp)
            if r is not None:
                del _context.seen[-1]
                return " due to diff " + c.__name__ + " keys" + r
            if v:
                print('check values')
            for k in o1.keys():
                if k not in o2:
                    del _context.seen[-1]
                    return ' due to o2 has no key=%s' % (lls(k, 155))
                r = run(o1[k], o2[k], v=v, eqcmp=eqcmp)
                if r is not None:
                    s = ' due to diff values for key=%s' % (lls(k, 155))
                    del _context.seen[-1]
                    return s + r
            del _context.seen[-1]
            return None
        elif issubclass(c, (sc, fc, tc, lc)):
            if v:
                print('Find set, tuple, or list.')
            if issubclass(c, (tc, lc)):
                if v:
                    print('Check tuple or list.')
                for i in range(len(o1)):
                    r = run(o1[i], o2[i], v=v, eqcmp=eqcmp)
                    if r is not None:
                        del _context.seen[-1]
                        return ' due to diff at index=%d' % (i) + r
                del _context.seen[-1]
                return None
            else:
                if v:
                    print('Check set/frozenset.')
                if 1:
                    if o1.difference(o2):
                        del _context.seen[-1]
                        return ' due to at leasr one in the foremer not in the latter'
                    else:
                        del _context.seen[-1]
                        return None
                else:
                    oc = o2.copy()
                    for m in o1:
                        found = False
                        for n in oc:
                            r = run(m, n, v=v, eqcmp=eqcmp)
                            if r is None:
                                found = True
                                break
                        if not found:
                            del _context.seen[-1]
                            return ' due to %s not in the latter' % (lls(m, 155))
                        oc.remove(n)
                    del _context.seen[-1]
                    return None
        elif hasattr(o1, '__dict__'):
            if v:
                print('obj1 has __dict__')
            r = run(o1.__dict__, o2.__dict__, v=v, eqcmp=eqcmp)
            if r:
                del _context.seen[-1]
                return ' due to o1.__dict__ != o2.__dict__' + r
            else:
                del _context.seen[-1]
                return None
        elif hasattr(o1, '__iter__') and hasattr(o1, '__next__') or \
                hasattr(o1, '__getitem__'):
            # two iterators are equal if all comparable properties are equal.
            del _context.seen[-1]
            return None
        elif has_eqcmp:
            # last resort
            if o1 == o2:
                del _context.seen[-1]
                return None
            else:
                del _context.seen[-1]
                return ' according to __eq__ or __cmp__'
        else:  # o1 != o2:
            if v:
                print('no way')
            s = ' due to no reason found for "%s" == "%s"' % (
                lls(o1, 155), lls(o2, 155))
            del _context.seen[-1]
            return s
    return run(obj1, obj2, v=verbose, eqcmp=eqcmp)


def xhash(hash_list=None):
    """ get the hash of a tuple of hashes of all members of given sequence.

    hash_list: use instead of self.getstate__()
    """

    hashes = []
    if issubclass(hash_list.__class__, (str, bytes)):
        # put str first so it is not treated as a sequence
        return(hash(hash_list))
    elif hasattr(hash_list, 'items'):
        source = chain.from_iterable(hash_list.items())
    elif hasattr(hash_list, '__iter__'):
        source = hash_list
    elif issubclass(hash_list.__class__, (array.array)):
        source = (hash_list.typecode,
                  hash_list.itemsize,
                  len(hash_list),
                  len(hash_list[0]))
    else:
        return(hash(hash_list))

    for t in source:
        h = t.hash() if hasattr(t, 'hash') else xhash(t)
        hashes.append(h)
    # if there is only one element only hash the element
    return hash(hashes[0] if len(hashes) == 1 else tuple(hashes))


class DeepcmpEqual(object):
    """ mh: Can compare key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj does not have items()
    """

    def equals(self, obj, verbose=False):
        r = self.diff(obj, [], verbose=verbose)
        # logging.debug(r)
        return r is None

    def __eq__(self, obj):
        return self.equals(obj)

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def diff(self, obj, seenlist, verbose=False):
        """ recursively compare components of list and dict.
        until meeting equality.
        seenlist: a list of classes that has been seen. will not descend in to them.
        """
        if issubclass(self.__class__, Serializable):
            if issubclass(obj.__class__, Serializable):
                r = deepcmp(self.__getstate__(),
                            obj.__getstate__(), seenlist=seenlist, verbose=verbose)
            else:
                return('different classes')
        else:
            r = deepcmp(self, obj, seenlist=seenlist, verbose=verbose)
        return r


class EqualDict(object):
    """ mh: Can compare key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj does not have items()
    """

    def equals(self, obj, verbose=False):

        if obj is None:
            return False
        try:
            if self.__dict__ != obj.__dict__:
                if verbose:
                    print('@@ diff \n' + lls(self.__dict__) +
                          '\n>>diff \n' + lls(obj.__dict__))
                return False
        except Exception as err:
            # print('Exception in dict eq comparison ' + lls(err))
            return False
        return True

    def __eq__(self, obj):
        return self.equals(obj)

    def __ne__(self, obj):
        return not self.__eq__(obj)


class EqualODict(object):
    """ mh: Can compare order and key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj does not have items()
    """

    def equals(self, obj, verbose=False):
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


class StateEqual(object):
    """ Equality tested by hashed state.
    """

    def hash(self):
        return xhash(self.__getstate__())

    def __eq__(self, obj, verbose=False, **kwds):
        """ compares hash. """

        if obj is None:
            return False

        if id(self) == id(obj):
            return True

        if type(self) != type(obj):
            return False
        try:
            h1, h2 = self.hash(), obj.hash()
        except AttributeError:
            return False
        except TypeError:
            return False
        if verbose:
            print('hashes ', h1, h2)
        return h1 == h2

    equals = __eq__

    def __xne__(self, obj):
        return not self.__eq__(obj)

    def __hash__(self):
        return self.hash()

    __hash__ = hash


DeepEqual = StateEqual
