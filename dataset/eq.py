from copy import deepcopy
from collections import OrderedDict
import json
import pprint

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Annotatable():
    """ An Annotatable object is an object that can give a
    human readable description of itself.
    """

    def __init__(self, description='UNKNOWN', **kwds):
        self.description = description
        super().__init__(**kwds)

    def getDescription(self):
        """ gets the description of this Annotatable object. """
        return self.description

    def setDescription(self, newDescription):
        """ sets the description of this Annotatable object. """
        self.description = newDescription
        return


class Copyable():
    """ Interface for objects that can make a copy of themselves. """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def copy(self):
        """ Makes a deep copy of itself. """
        return deepcopy(self)


class SerializableEncoder(json.JSONEncoder):
    """ can encode parameter and product etc such that they can be recovered
    with deserializeClassID
    """

    def default(self, obj):
        try:
            #print('%%%' + str(obj.__class__))
            # Let the base class default method raise the TypeError
            d = json.JSONEncoder.default(self, obj)
            #print('d=' + d)
        except TypeError as err:
            try:
                # logger.debug
                #print('&&&& %s %s' % (str(obj.__class__), str(obj)))
                if issubclass(obj.__class__, bytes):
                    return dict(hex=obj.hex(), classID='bytes', version='')
                return obj.serializable()
            except Exception:
                print('exc ' + str(err))
                raise err


#    obj = json.loads(jstring)

def serializeClassID(o):
    """ return JSON using special encoder SerializableEncoder """
    return json.dumps(o, cls=SerializableEncoder)


class Serializable():
    """ mh: Can be serialized.
    Has a ClassID and version instance property to show its class
    and version information.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        sc = self.__class__
        # print('$$ ' + sc.__name__)
        if issubclass(sc, dict):
            self['classID'] = sc.__qualname__
            self['version'] = ''
        else:
            self.classID = sc.__qualname__
            self.version = ''

    def serialized(self):
        return serializeClassID(self)

    def serializable(self):
        """ returns an OrderedDict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(info='serializable function not implemented')


def deepcmp(obj1, obj2, seenlist=None, verbose=False):
    """ recursively descend into set, list, dict, ordereddict,
    (or ods subclasses) and any objects with '__class__', compare
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
                print('deja vue')
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
                r = run(o1[k], o2[k])
                if r is not None:
                    s = ' due to diff values for key=%s' % (str(k))
                    return s + r
            return None
        elif c in (sc, tc, lc):
            if len(o1) != len(o2):
                return ' due to diff lengths ' + c.__name__
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


class EqualOrderedDict():
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
