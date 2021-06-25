# -*- coding: utf-8 -*-
import logging
import json
import codecs
import binascii
import array
import mmap
from collections import ChainMap
import builtins
from collections import UserDict
from collections.abc import MutableMapping as MM, MutableSequence as MS, MutableSet as MS

from .odict import ODict
from .classes import Classes
from ..utils.common import lls, trbk

import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = (str, bytes, bytearray)
else:
    PY3 = False
    strset = (str, unicode)

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

''' Note: this has to be in a different file where other interface
classes are defined to avoid circular dependency (such as ,
Serializable.
'''


def constructSerializable(obj, lookup=None, debug=False):
    """ mh: reconstruct object from the output of jason.loads().
    Recursively goes into nested class instances that are not
    encoded by default by JSONEncoder, instantiate and fill in
    variables.
    Objects to be deserialized must have their classes loaded.
    _STID cannot have module names in it (e.g.  dataset.Product)
    or locals()[classname] or globals()[classname] will not work. See alternative in
    https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

    """
    global indent
    indent += 1
    spaces = '  ' * indent

    classname = obj.__class__.__name__
    if debug:
        print(spaces + '===OBJECT %s ===' % lls(obj, 150))
    if not hasattr(obj, '__iter__') or issubclass(obj.__class__, strset):
        if debug:
            print(spaces + 'Find non-iter <%s>' % classname)
        indent -= 1
        return obj

    # process list first
    if isinstance(obj, list):
        if debug:
            print(spaces + 'Find list <%s>' % classname)
        inst = []
        # loop i to preserve order
        for i in range(len(obj)):
            x = obj[i]
            xc = x.__class__
            if debug:
                print(spaces + 'looping through list %d <%s>' %
                      (i, xc.__name__))
            if issubclass(xc, (list, dict)):
                des = constructSerializable(x, lookup=lookup, debug=debug)
            else:
                des = x
            inst.append(des)
        if debug:
            print(spaces + 'Done with list <%s>' % (classname))
        indent -= 1
        return inst

    if not '_STID' in obj:
        """ This object is supported by JSON encoder """
        if debug:
            print(spaces + 'Find non-_STID. <%s>' % classname)
        inst = obj
    else:
        classname = obj['_STID']
        if debug:
            print(spaces + 'Find _STID <%s>' % classname)
        # process types wrapped in a dict
        if PY3:
            if classname == 'bytes':
                inst = codecs.decode(obj['code'], 'hex')
                if debug:
                    print(spaces + 'Instanciate hex')
                indent -= 1
                return inst
            elif classname.startswith('array.array'):
                tcode = classname.rsplit('_', 1)[1]
                inst = array.array(tcode, binascii.a2b_hex(obj['code']))
                if debug:
                    print(spaces + 'Instanciate array.array')
                indent -= 1
                return inst
        if classname in lookup:
            # Now we have a blank instance.
            inst = lookup[classname]()
            if debug:
                print(spaces + 'Instanciate custom obj <%s>' % classname)
        elif classname == 'ellipsis':
            if debug:
                print(spaces + 'Instanciate Ellipsis')
            indent -= 1
            return Ellipsis
        elif classname in lookup and 'obj' in obj:
            o = constructSerializable(obj['obj'], lookup=lookup, debug=debug)
            inst = lookup[classname](o)
            if debug:
                print(spaces + 'Instanciate defined %s' % obj['obj'])
            indent -= 1
            return inst
        elif classname == 'dtype':
            if debug:
                print(spaces + 'Instanciate type %s' % obj['obj'])
            inst = lookup[obj['obj']]
            indent -= 1
            return inst
        else:
            raise ValueError('Class %s is not known.' % classname)
    if debug:
        print(spaces + 'Go through properties of instance')
    for (k, v) in obj.items():
        """ loop through all key-value pairs. """
        if k == '_STID':
            continue
        # deserialize v
        # should be object_pairs_hook in the following if... line
        if issubclass(v.__class__, (dict, list)):
            if debug:
                print(spaces + '[%s]value(dict/list) <%s>: %s' %
                      (k, v.__class__.__qualname__,
                       lls(list(iter(v)), 70)))
            desv = constructSerializable(v, lookup=lookup, debug=debug)
        else:
            if debug:
                print(spaces + '[%s]value(simple) <%s>: %s' %
                      (k, v.__class__.__name__, lls(v, 70)))
            if 1:
                desv = v
            else:
                if isinstance(v, str) or isinstance(v, bytes):
                    try:
                        desv = int(v)
                    except ValueError:
                        desv = v

        # set k with desv
        if issubclass(inst.__class__, (MM)):    # should be object_pairs_hook
            inst[k] = desv
            if debug:
                print(spaces + 'Set dict/usrd <%s>[%s] = %s <%s>' %
                      ((inst.__class__.__name__), str(k), lls(desv, 70), (desv.__class__.__name__)))
        else:
            setattr(inst, k, desv)
            if debug:
                print(spaces + 'set non-dict <%s>.%s = %s <%s>' %
                      ((inst.__class__.__name__), str(k), lls(desv, 70), (desv.__class__.__name__)))
    indent -= 1
    return inst


class IntDecoder(json.JSONDecoder):
    """ adapted from https://stackoverflow.com/questions/45068797/how-to-convert-string-int-json-into-real-int-with-json-loads
    modified to also convert keys in dictionaries.
    """

    def decode(self, s):
        # result = super(Decoder, self).decode(s) for Python 2.x
        result = super(IntDecoder, self).decode(s)
        return self._decode(result)

    def _decode(self, o):
        if isinstance(o, str) or isinstance(o, bytes):
            try:
                return int(o)
            except ValueError:
                return o
        elif isinstance(o, dict):
            return dict({self._decode(k): self._decode(v) for k, v in o.items()})
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o


class IntDecoderOD(IntDecoder):
    """ Uses ODict
    """

    def _decode(self, o):
        if isinstance(o, str) or isinstance(o, bytes):
            try:
                return int(o)
            except ValueError:
                return o
        elif isinstance(o, dict):
            return ODict({self._decode(k): self._decode(v) for k, v in o.items()})
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o


def deserialize(js, lookup=None, debug=False, usedict=True):
    """ Loads classes with _STID from the results of serialize.

    if usedict is True dict insted of ODict will be used.
    """

    lookup = Class_Look_Up

    if not isinstance(js, strset) or len(js) == 0:
        return None
    # debug = False  # True if issubclass(obj.__class__, list) else False
    try:
        if usedict:
            obj = json.loads(js)  # , cls=IntDecoder)
        else:
            # , cls=IntDecoderOD)
            obj = json.loads(js, object_pairs_hook=ODict)
    except json.decoder.JSONDecodeError as e:
        msg = '\nBad string to decode as JSON=====>\n%s\n<======\nStack trace: %s' %\
            (lls(js, 500), trbk(e))
        logging.error(msg)
        obj = msg
    if debug:
        # print('load-str ' + str(o) + ' class ' + str(o.__class__))
        print('-------- json loads returns: --------\n' + str(obj))

    global indent
    indent = -1
    return constructSerializable(obj, lookup=lookup, debug=debug)


Class_Look_Up = ChainMap(Classes._classes, globals(), vars(builtins))
