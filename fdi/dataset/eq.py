# -*- coding: utf-8 -*-

from .serializable import Serializable

import logging
from collections.abc import Mapping, Sequence, Set
from itertools import chain
from collections import OrderedDict
import array
import decimal
import datetime
import fractions
import sys
import hashlib

HASH_WIDTH = sys.hash_info.width // 8

if sys.version_info[0] + 0.1 * sys.version_info[1] >= 3.6:
    PY36 = True
else:
    PY36 = False

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class CircularCallError(RuntimeError):
    pass


DEEPCMP_RESULT = None


def deepcmp(obj1, obj2, seenlist=None, verbose=False, eqcmp=False, brief=True):
    """ Recursively descends into obj1's every component and
    compares with its counterpart in obj2.

    Ways to test includes (in this order):

    * if they are the same object
    * type
    * ```__eq__``` or ```__cmp__``` if requested
    * state from ```__getstate__()```
    * quick length
    * members if is ```Mapping```, ```Sequence``` (
    tuple, set, list, dict, OrderedDict, UserDict ... )
    * properties/attributes in ```__dict__```
    * ```__eq__``` or ```__cmp__``` even if not requested

    Detects cyclic references.

    Returns
    -------
    ``None`` if finds no difference, ```1``` if `brief is ```True``` else a string of explanation.

    :eqcmp: if True, use __eq__ or __cmp__ if the objs have them. If False only use as the last resort. default True.
    """

    global DEEPCMP_RESULT

    # seen and level are to be used as nonlocal variables in run()
    # to overcome python2's lack of nonlocal type this method is usded
    # https://stackoverflow.com/a/28433571
    class _context:
        if seenlist is None:
            seen = []
        else:
            seen = seenlist
        level = 0

    def run(o1, o2, explain=False, v=False, eqcmp=True, brief=True):
        """
        Paremeters
        ----------
        :o1: object to be compared.
        :o2: object to be compared.
        :v: Prints out step-by-step comparison if set `True`.
        :brief: if not equal, return 1 if set `True` else returns an explaination.
        :eqcmp: use ```__eq__``` and ```__cmp__``` for comparison.

        Returns
        -------
        ```None``` if equal. ```1``` if ```brief``` is ```True``` else a string of explanation why not equal.

        """
        #
        # nonlocal seen
        # nonlocal level
        if v or not brief:
            from ..utils.common import lls, bstr
        id1, id2 = id(o1), id(o2)
        if id1 == id2:
            if v:
                print('These are the same object o1=%s ||| o2=%s.' %
                      (bstr(o1, 20), bstr(o2, 20)))
            return None
        pair = (id1, id2) if id1 < id2 else (id2, id1)
        c = o1.__class__
        c2 = o2.__class__
        _context.level += 1
        if v:
            print('deepcmp level %d seenlist length %d' %
                  (_context.level, len(_context.seen)))
            print('1 ' + str(c) + lls(o1, 45))
            print('2 ' + str(c2) + lls(o2, 45))
        if pair in _context.seen:
            msg = 'deja vue %s' % str(pair)
            raise CircularCallError(msg)
        _context.seen.append(pair)
        if c != c2:
            if v:
                print('type diff')
            _context.level -= 1
            del _context.seen[-1]
            return 1 if brief else ' due to diff types: ' + c.__name__ + ' and ' + c2.__name__
        if issubclass(c, (int, float, complex, str, bytes, bool, datetime.datetime)):
            if v:
                print('find simple type')
            _context.level -= 1
            del _context.seen[-1]
            if o1 != o2:
                return 1 if brief else ' due to difference: "%s" ||| "%s"' % (o1, o2)
            else:
                return None

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
                _context.level -= 1
                del _context.seen[-1]
                if t:
                    return None
                else:  # o1 != o2:
                    return 1 if brief else \
                        ' due to "%s" != "%s"' % (lls(o1, 155), lls(o2, 155))

        if hasattr(o1, '__getstate__'):
            if v:
                print('Find __getstate__')
            try:
                o1 = o1.__getstate__()
                o2 = o2.__getstate__()
            except TypeError:
                logger.error('__getstate__ trouble')
                raise
            else:  # no exception for __getstate__
                r = run(o1, o2, v=v, eqcmp=eqcmp, brief=brief)
                del _context.seen[-1]
                _context.level -= 1
                if r:
                    return 1 if brief else ' due to o1.__getstate__ != o2.__getstate__' + r
                else:
                    return None

        try:
            # this is not good if len() is delegated
            # if hasattr(o1, '__len__') and len(o1) != len(o2):
            if hasattr(o1, '__len__') and len(o1) != len(o2):
                del _context.seen[-1]
                _context.level -= 1
                return 1 if brief else \
                    ' due to diff %s lengths: %d and %d (%s, %s)' %\
                    (c.__name__, len(o1), len(o2), lls(
                        list(o1), 115), lls(list(o2), 115))
        except AttributeError:
            pass

        if issubclass(c, Mapping):
            if v:
                print('Find Mapping')
                print('check keys')

            from .odict import ODict
            if issubclass(c, (OrderedDict, ODict)) or PY36:
                #
                r = run(list(o1.keys()), list(o2.keys()),
                        v=v, eqcmp=eqcmp, brief=brief)
            else:
                #  old dict or UserDict
                r = run(tuple(sorted(o1.keys(), key=hash)),
                        tuple(sorted(o1.keys(), key=hash)),
                        v=v, eqcmp=eqcmp, brief=brief)
            if r is not None:
                del _context.seen[-1]
                _context.level -= 1
                return 1 if brief else " due to diff " + c.__name__ + " keys" + r
            if v:
                print('check values')
            for k in o1.keys():
                if k not in o2:
                    del _context.seen[-1]
                    _context.level -= 1
                    return 1 if brief else ' due to o2 has no key=%s' % (lls(k, 155))
                r = run(o1[k], o2[k], v=v, eqcmp=eqcmp, brief=brief)
                if r is not None:
                    del _context.seen[-1]
                    _context.level -= 1
                    return 1 if brief else ' due to diff values for key=%s' % (lls(k, 155)) + r
            del _context.seen[-1]
            _context.level -= 1
            return None
        elif issubclass(c, (Set, Sequence)):
            if v:
                print('Find Set, Sequence.')
            if issubclass(c, Sequence):
                if v:
                    print('Check Sequence.')
                for i in range(len(o1)):
                    r = run(o1[i], o2[i], v=v, eqcmp=eqcmp, brief=brief)
                    if r is not None:
                        del _context.seen[-1]
                        _context.level -= 1
                        return 1 if brief else ' due to diff at index=%d (%s %s)' % \
                            (i,
                             lls(o1[i], 10),
                             lls(o2[i], 10)) + r
                _context.level -= 1
                del _context.seen[-1]
                return None
            else:
                if v:
                    print('Check Set.')
                if 1:
                    del _context.seen[-1]
                    _context.level -= 1
                    if o1.difference(o2):
                        return 1 if brief else ' due to at least one element in o1 not in o2'
                    else:
                        return None
                else:
                    oc = o2.copy()
                    for m in o1:
                        found = False
                        for n in oc:
                            r = run(m, n, v=v, eqcmp=eqcmp, brief=brief)
                            if r is None:
                                found = True
                                break
                        if not found:
                            del _context.seen[-1]
                            _context.level -= 1
                            return 1 if brief else ' due to %s not in the latter' % (lls(m, 155))
                        oc.remove(n)
                    del _context.seen[-1]
                    _context.level -= 1
                    return None
        else:
            if hasattr(o1, '__dict__'):
                if v:
                    print('obj1 has __dict__')
                    o1 = sorted(vars(o1).items())
                    o2 = sorted(vars(o2).items())
                    r = run(o1, o2, v=v, eqcmp=eqcmp, brief=brief)
                    del _context.seen[-1]
                    _context.level -= 1
                if r:
                    return 1 if brief else ' due to o1.__dict__ != o2.__dict__' + r
                else:
                    return None
            # elif hasattr(o1, '__iter__') and hasattr(o1, '__next__') or \
            #         hasattr(o1, '__getitem__'):
            #     # two iterators are equal if all comparable properties are equal.
            #     del _context.seen[-1]
            #     _context.level -= 1
            #     return None
            elif has_eqcmp:
                # last resort
                if o1 == o2:
                    del _context.seen[-1]
                    _context.level -= 1
                    return None
                else:
                    del _context.seen[-1]
                    _context.level -= 1
                    return 1 if brief else ' according to __eq__ or __cmp__'
            else:  # o1 != o2:
                del _context.seen[-1]
                _context.level -= 1
                if v:
                    print('no way')
                return 1 if brief else ' due to no reason found for "%s" == "%s"' % \
                    (lls(o1, 155), lls(o2, 155))
    res = run(obj1, obj2, v=verbose, eqcmp=eqcmp, brief=brief)
    DEEPCMP_RESULT = res
    return res


XHASH_VERBOSE = False


def xhash(hash_list=None, seenlist=None, verbose=None):
    """ get the hash of a tuple of hashes of all members of given sequence.

    :hash_list: use instead of self.getstate__()
    :verbose: set to trace.
    """

    if verbose is None:
        verbose = XHASH_VERBOSE

    # https://stackoverflow.com/a/28433571
    class _context:
        if seenlist is None:
            seen = []
        else:
            seen = seenlist
        level = 0

    def run(hash_list=None):
        _context.level += 1
        ind = ' ' * _context.level
        hashes = []

        if verbose:
            from ..utils.common import lls, bstr

        if 0 and verbose:
            print('entering id%d id%d lv%d len%d' % (id(_context.level), id(_context.seen),
                                                     _context.level, len(_context.seen)))
        hlid = id(hash_list)
        if hlid in _context.seen:
            if verbose:
                print(ind + 'seen it')
            _context.level -= 1
            del _context.seen[-1]
            return 0
        _context.seen.append(hlid)
        if issubclass(hash_list.__class__, int):
            res = hash_list
            if verbose:
                print(ind + 'int "%s" -- %s' % (lls(hash_list, 20), res))
            _context.level -= 1
            del _context.seen[-1]
            return res
        elif issubclass(hash_list.__class__, (float, decimal.Decimal, fractions.Fraction)):
            res = hash(hash_list)
            if verbose:
                print(ind + '%s "%s" -- %s' %
                      (hash_list.__class__.__name__, lls(hash_list, 20), res))
            _context.level -= 1
            del _context.seen[-1]
            return res
        elif issubclass(hash_list.__class__, (str, bytes)):
            # put str first so it is not treated as a sequence
            res = hash(hash_list)
            if verbose:
                print(ind + 'str/bytes "%s" -- %s' %
                      (lls(hash_list, 20), res))
            _context.level -= 1
            del _context.seen[-1]
            return res
        elif issubclass(hash_list.__class__, (array.array)):
            hasher = hashlib.new('sha256', hash_list.typecode.encode('utf-8'))
            hasher.update(hash_list)
            res = int.from_bytes(
                hasher.digest()[:HASH_WIDTH], byteorder=sys.byteorder)
            # source = (hash_list.typecode,
            #           hash_list.itemsize,
            #           len(hash_list),
            #           len(hash_list[0]))
            if verbose:
                print(ind + '%s %s %s' % (hash_list.__class__.__name__,
                                          lls(hash_list, 20), res))
            _context.level -= 1
            del _context.seen[-1]
            return res
        elif hasattr(hash_list, '__getstate__'):
            try:
                o = hash_list.__getstate__()
            except TypeError:
                logger.error('__getstate__ trouble')
                raise
            else:  # no exception for __getstate__
                source = chain.from_iterable(o.items())
            if verbose:
                print(ind + '%s %s %s' % (hash_list.__class__.__name__,
                                          lls(source, 20), 'has __getstate__'))
        elif issubclass(hash_list.__class__, (Set, Sequence)):
            source = hash_list
            if verbose:
                print(ind + '%s %s %s' % (hash_list.__class__.__name__,
                                          lls(source, 20), 'is Sequence'))
        elif issubclass(hash_list.__class__, Mapping):
            source = chain.from_iterable(hash_list.items())
            if verbose:
                print(ind + '%s %s %s' % (hash_list.__class__.__name__,
                                          lls(source, 20), 'is Mapping'))
        else:
            res = hash(hash_list)
            if verbose:
                print(ind + '%s %s -- %s' % (hash_list.__class__.__name__,
                                             lls(hash_list, 20), res))
            _context.level -= 1
            del _context.seen[-1]
            return res

        for t in source:
            if hasattr(t, 'hash'):
                h = t.hash()
            else:
                h = run(t)
            if verbose:
                print(ind + '> %s %s -- %s' % (h.__class__.__name__,
                                               lls(h, 20), h))
            hashes.append(h)
        # if there is only one element only hash the element
        res = hash(hashes[0] if len(hashes) == 1 else tuple(hashes))
        if verbose:
            print(ind + '%s %s -- %s' % ('RET', str(len(hashes)), res))
        _context.level -= 1
        del _context.seen[-1]
        return res
    return run(hash_list=hash_list)


class DeepcmpEqual(object):
    """ mh: Can compare key-val pairs of another object
    with self.

    False if compare with None
    or exceptions raised, e.g. objects that do not have items()
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def equals(self, obj, verbose=False, brief=True):
        """
        Paremeters
        ----------

        :verbose: Prints out step-by-step comparison if set `True`.

        Returns
        -------

        """
        r = self.diff(obj, [], verbose=verbose, brief=brief)
        # logging.debug(r)
        return r is None

    def __eq__(self, obj):
        """
        Paremeters
        ----------

        Returns
        -------

        """
        return self.equals(obj)

    def __ne__(self, obj):
        """
        Paremeters
        ----------

        Returns
        -------

        """

        return not self.__eq__(obj)

    def diff(self, obj, seenlist, verbose=False, brief=True):
        """ recursively compare components of list and dict
        until finding equality or exhausting all ways of testing.

        :seenlist: a list of classes that has been seen. will not descend in to them.
        :verbose: Prints out step-by-step comparison if set `True`.
        :brief: if not equal, return 1 if set `True` else returns an explaination.
        Paremeters
        ----------

        Returns
        -------
        """
        if issubclass(self.__class__, Serializable):
            if issubclass(obj.__class__, Serializable):
                r = deepcmp(self.__getstate__(),
                            obj.__getstate__(),
                            seenlist=seenlist,
                            verbose=verbose,
                            brief=brief)
            else:
                return 1 if brief else('different classes')
        else:
            r = deepcmp(self, obj, seenlist=seenlist,
                        verbose=verbose, brief=brief)
        return r


class EqualDict(object):
    """ mh: Can compare key-val pairs of another object
    with self.

    False if compare with None
    or exceptions raised, e.g. obj  that do not have items().
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def equals(self, obj, verbose=False):
        """
        Paremeters
        ----------

        Returns
        -------

        """

        if obj is None:
            return False
        try:
            if self.__dict__ != obj.__dict__:
                if verbose:
                    print('@@ diff ' + lls(self.__dict__) +
                          '\n>>diff \n' + lls(obj.__dict__))
                return False
        except Exception as err:
            # print('Exception in dict eq comparison ' + lls(err))
            return False
        return True

    def __eq__(self, obj):
        """
        Paremeters
        ----------

        Returns
        -------

        """

        return self.equals(obj)

    def __ne__(self, obj):
        """
        Paremeters
        ----------

        Returns
        -------

        """

        return not self.__eq__(obj)


class EqualODict(object):
    """ mh: Can compare order and key-val pairs of another object
    with self. False if compare with None
    or exceptions raised, e.g. obj that do not have items()
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def equals(self, obj, verbose=False):
        """
        Paremeters
        ----------

        Returns
        -------

        """
        if obj is None:
            return False
        try:
            return list(self.items()) == list(obj.items())
        except Exception:
            return False
        return True

    def __eq__(self, obj):
        """
        Paremeters
        ----------

        Returns
        -------

        """
        return self.equals(obj)

    def __ne__(self, obj):
        """
        Paremeters
        ----------

        Returns
        -------

        """

        return not self.__eq__(obj)


class StateEqual():
    """ Equality tested by hashed state.
    """

    def __init__(self, *args, **kwds):
        """ Must pass *args* so `DataWrapper` in `Composite` can get `data`.
        """

        super().__init__(*args, **kwds)  # StateEqual

    def hash(self, **kwds):
        return xhash(self.__getstate__(), **kwds)

    def __eq__(self, obj, **kwds):
        """ compares hash. """

        if obj is None:
            return False

        if id(self) == id(obj):
            return True

        if type(self) != type(obj):
            return False
        try:
            h1 = self.hash()
            h2 = obj.hash()
        except AttributeError:
            return False
        # print('hashes ', h1, h2)
        return h1 == h2

    equals = __eq__

    def __xne__(self, obj):
        return not self.__eq__(obj)

    def __hash__(self, **kwds):
        return self.hash(**kwds)

    __hash__ = hash


class DeepcmpEqual():
    """ Equality tested by `deepcmp`.
    """

    def __init__(self, *args, **kwds):
        """ Must pass *args* so `DataWrapper` in `Composite` can get `data`.
        """

        super().__init__(*args, **kwds)  # DeepcmpEqual

    def __eq__(self, obj, **kwds):
        """ compares using `deepcmp`. """

        if obj is None:
            return False

        if id(self) == id(obj):
            return True

        if type(self) != type(obj):
            return False
        res = deepcmp(self, obj, **kwds)
        return res is None

    equals = __eq__

    def __xne__(self, obj):
        return not self.__eq__(obj)

    def __hash__(self, **kwds):
        return self.hash(**kwds)

    __hash__ = hash


DeepEqual = DeepcmpEqual
