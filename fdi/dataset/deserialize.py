# -*- coding: utf-8 -*-
import logging
import json
import codecs
import builtins
from collections import UserDict

import pdb

from .odict import ODict
from .classes import Classes
from ..utils.common import lls

import sys
if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = (str, bytes)
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

BD = builtins.__dict__


def constructSerializableClassID(obj, lgb=None, debug=False):
    """ mh: reconstruct object from the output of jason.loads().
    Recursively goes into nested class instances that are not
    encoded by default by JSONEncoder, instantiate and fill in
    variables.
    Objects to be deserialized must have their classes loaded.
    ClassID cannot have module names in it (e.g.  dataset.Product)
    or locals()[classname] or globals()[classname] will not work. See alternative in
    https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

    """
    global indent
    indent += 1
    spaces = '  ' * indent

    classname = obj.__class__.__name__
    if debug:
        print(spaces + '===OBJECT %s ===' % (obj))
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
            if issubclass(xc, (list, dict, UserDict)):
                des = constructSerializableClassID(x, lgb=lgb, debug=debug)
            else:
                des = x
            inst.append(des)
        if debug:
            print(spaces + 'Done with list <%s>' % (classname))
        indent -= 1
        return inst

    if not 'classID' in obj:
        """ This object is supported by JSON encoder """
        if debug:
            print(spaces + 'Find non-ClassID. <%s>' % classname)
        inst = obj
    else:
        classname = obj['classID']
        if debug:
            print(spaces + 'Find ClassID <%s>' % classname)
        # process types wrapped in a dict
        if PY3 and classname == 'bytes':
            inst = codecs.decode(obj, 'hex')
            if debug:
                print(spaces + 'Instanciate hex')
            indent -= 1
            return inst
        if classname in lgb:
            inst = lgb[classname]()
            if debug:
                print(spaces + 'Instanciate custom obj <%s>' % classname)
        elif classname == 'ellipsis':
            if debug:
                print(spaces + 'Instanciate Ellipsis')
            indent -= 1
            return Ellipsis
        elif classname in BD and 'obj' in obj:
            o = constructSerializableClassID(obj['obj'], lgb=lgb, debug=debug)
            inst = BD[classname](o)
            if debug:
                print(spaces + 'Instanciate builtin %s' % obj['obj'])
            indent -= 1
            return inst
        else:
            raise ValueError('Class %s is not known.' % classname)
    if debug:
        print(spaces + 'Go through properties of instance')
    for (k, v) in obj.items():
        """ loop through all key-value pairs. """
        if k == 'classID':
            continue
        # deserialize v
        # should be object_pairs_hook in the following if... line
        if issubclass(v.__class__, (dict, UserDict, list)):
            if debug:
                print(spaces + '[%s]value(dict/usrd/list) <%s>: %s' %
                      (k, v.__class__.__qualname__,
                       lls(str(list(iter(v))), 70)))
            desv = constructSerializableClassID(v, lgb=lgb, debug=debug)
        else:
            if debug:
                print(spaces + '[%s]value(simple) <%s>: %s' %
                      (k, v.__class__.__name__, lls(str(v), 70)))
            if 1:
                desv = v
            else:
                if isinstance(v, str) or isinstance(v, bytes):
                    try:
                        desv = int(v)
                    except ValueError:
                        desv = v

        # set k with desv
        if issubclass(inst.__class__, (dict)):    # should be object_pairs_hook
            inst[k] = desv
            if debug:
                print(spaces + 'Set dict/usrd <%s>[%s] = %s <%s>' %
                      ((inst.__class__.__name__), str(k), lls(str(desv), 70), (desv.__class__.__name__)))
        else:
            setattr(inst, k, desv)
            if debug:
                print(spaces + 'set non-dict <%s>.%s = %s <%s>' %
                      ((inst.__class__.__name__), str(k), lls(str(desv), 70), (desv.__class__.__name__)))
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


def deserializeClassID(js, lgb=None, debug=False, usedict=True):
    """ Loads classes with ClassID from the results of serializeClassID.

    if usedict is True dict insted of ODict will be used.
    """

    if lgb is None:
        lgb = Classes.mapping

    if not isinstance(js, strset) or len(js) == 0:
        return None
    # debug = False  # True if issubclass(obj.__class__, list) else False
    try:
        if usedict:
            obj = json.loads(js, cls=IntDecoder)
        else:
            obj = json.loads(js, object_pairs_hook=ODict, cls=IntDecoderOD)
    except json.decoder.JSONDecodeError as e:
        logging.error(' Bad string to decode:\n==============\n' +
                      lls(js, 500) + '\n==============')
        raise e
    if debug:
        # print('load-str ' + str(o) + ' class ' + str(o.__class__))
        print('-------- json loads returns: --------\n' + str(obj))

    global indent
    indent = -1
    return constructSerializableClassID(obj, lgb=lgb, debug=debug)
